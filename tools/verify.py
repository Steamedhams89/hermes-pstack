#!/usr/bin/env python3
"""Verify pstack source provenance, parity mapping, and emitted receipts."""

from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass, field
import json
import os
from pathlib import Path
import stat
import sys
from typing import Any

try:
    from . import manifest
except ImportError:  # Direct script execution.
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from tools import manifest


@dataclass(frozen=True)
class Issue:
    code: str
    message: str
    path: str | None = None

    def to_dict(self) -> dict[str, Any]:
        value: dict[str, Any] = {"code": self.code, "message": self.message}
        if self.path is not None:
            value["path"] = self.path
        return value


@dataclass
class VerificationReport:
    issues: list[Issue] = field(default_factory=list)
    source_file_count: int = 0
    ledger_entry_count: int = 0
    pending_output_count: int = 0
    emitted_output_count: int = 0
    unreceipted_existing_output_count: int = 0

    @property
    def ok(self) -> bool:
        return not self.issues

    def add(self, code: str, message: str, path: str | None = None) -> None:
        candidate = Issue(code, message, path)
        if candidate not in self.issues:
            self.issues.append(candidate)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "source_file_count": self.source_file_count,
            "ledger_entry_count": self.ledger_entry_count,
            "pending_output_count": self.pending_output_count,
            "emitted_output_count": self.emitted_output_count,
            "unreceipted_existing_output_count": self.unreceipted_existing_output_count,
            "issues": [issue.to_dict() for issue in self.issues],
        }


def _load_json_or_issue(path: Path, report: VerificationReport, label: str) -> Any | None:
    if path.is_symlink():
        report.add("symlink", f"{label} is a symlink", str(path))
        return None
    try:
        return manifest.load_json(path)
    except FileNotFoundError:
        report.add("missing_manifest", f"missing {label}", str(path))
    except (OSError, json.JSONDecodeError, TypeError) as error:
        report.add("invalid_manifest", f"invalid {label}: {error}", str(path))
    return None


def _patch_metadata(
    registry: Any, report: VerificationReport
) -> dict[str, dict[str, Any]]:
    if not isinstance(registry, dict) or not isinstance(registry.get("patches"), list):
        report.add("invalid_patch_registry", "patch registry must contain a patches list")
        return {}
    patches: dict[str, dict[str, Any]] = {}
    identifiers: list[str] = []
    for patch in registry["patches"]:
        if not isinstance(patch, dict) or not isinstance(patch.get("id"), str):
            report.add("invalid_patch_registry", "every patch requires a string id")
            continue
        identifier = patch["id"]
        identifiers.append(identifier)
        status_value = patch.get("status")
        if status_value not in {"pending", "verified"}:
            report.add(
                "invalid_patch_status",
                f"patch status must be pending or verified: {status_value!r}",
                identifier,
            )
        required = patch.get("required_tests")
        if (
            not isinstance(required, list)
            or not required
            or any(not isinstance(item, str) or not item for item in required)
            or len(required) != len(set(required))
        ):
            report.add(
                "invalid_patch_registry",
                "patch required_tests must be a unique non-empty string list",
                identifier,
            )
        patches.setdefault(identifier, patch)
    for identifier, count in Counter(identifiers).items():
        if count > 1:
            report.add("duplicate_patch", f"duplicate patch id: {identifier}", identifier)
    return patches


def _verify_test_receipts(
    repo_root: Path,
    patches: dict[str, dict[str, Any]],
    receipts: Any | None,
    report: VerificationReport,
) -> dict[str, str]:
    verified_patches = {
        identifier for identifier, patch in patches.items() if patch.get("status") == "verified"
    }
    if receipts is None:
        if verified_patches:
            report.add(
                "missing_test_receipts",
                "verified patches require provenance/test-receipts.json",
            )
        return {}
    if (
        not isinstance(receipts, dict)
        or receipts.get("schema_version") != 1
        or not isinstance(receipts.get("tests"), dict)
        or not isinstance(receipts.get("patch_verification"), dict)
    ):
        report.add("invalid_test_receipts", "test receipt document has an invalid schema")
        return {}

    known_tests = {
        test_id
        for patch in patches.values()
        for test_id in patch.get("required_tests", [])
        if isinstance(test_id, str)
    }
    tests = receipts["tests"]
    for test_id in sorted(set(tests) - known_tests):
        report.add("stale_test_receipt", "receipt names an unknown test", test_id)
    statuses: dict[str, str] = {}
    for test_id in sorted(known_tests):
        value = tests.get(test_id)
        if not isinstance(value, dict):
            report.add("missing_test_receipt", "required test has no receipt", test_id)
            continue
        status_value = value.get("status")
        if status_value not in {"passed", "failed"}:
            report.add("invalid_test_receipt", "test receipt status must be passed or failed", test_id)
            continue
        statuses[test_id] = status_value
        commands = value.get("commands")
        if not isinstance(commands, list) or not commands:
            report.add("invalid_test_receipt", "test receipt requires command evidence", test_id)
            continue
        exits: list[int] = []
        for command in commands:
            if (
                not isinstance(command, dict)
                or not isinstance(command.get("argv"), list)
                or not command["argv"]
                or any(not isinstance(item, str) or not item for item in command["argv"])
                or not isinstance(command.get("cwd"), str)
                or not isinstance(command.get("exit_code"), int)
                or not isinstance(command.get("output_sha256"), str)
                or len(command["output_sha256"]) != 64
            ):
                report.add("invalid_test_receipt", "invalid command evidence", test_id)
                continue
            exits.append(command["exit_code"])
        if status_value == "passed" and (not exits or any(code != 0 for code in exits)):
            report.add("invalid_test_receipt", "passed test contains a failed command", test_id)
        if status_value == "failed" and exits and all(code == 0 for code in exits):
            report.add("invalid_test_receipt", "failed test contains no failed command", test_id)
        inputs = value.get("inputs")
        if not isinstance(inputs, dict) or not inputs:
            report.add("invalid_test_receipt", "test receipt requires input hashes", test_id)
            continue
        for relative_text, expected_hash in sorted(inputs.items()):
            if not isinstance(relative_text, str) or not isinstance(expected_hash, str) or len(expected_hash) != 64:
                report.add("invalid_test_receipt", "invalid test input receipt", test_id)
                continue
            resolved, target_error = _target_status(repo_root, relative_text)
            if target_error:
                report.add(target_error, "invalid test input path", relative_text)
            elif resolved is None or not resolved.is_file():
                report.add("missing_test_input", "test input no longer exists", relative_text)
            elif manifest.sha256_file(resolved) != expected_hash:
                report.add("stale_test_input", "test input differs from its receipt", relative_text)

    patch_verification = receipts["patch_verification"]
    for identifier in sorted(set(patch_verification) - set(patches)):
        report.add("stale_patch_receipt", "receipt names an unknown patch", identifier)
    for identifier, patch in sorted(patches.items()):
        value = patch_verification.get(identifier)
        if not isinstance(value, dict):
            report.add("missing_patch_receipt", "patch has no verification receipt", identifier)
            continue
        required = patch.get("required_tests", [])
        if value.get("required_tests") != required:
            report.add("patch_receipt_drift", "patch receipt test list differs", identifier)
        expected_status = (
            "verified"
            if required and all(statuses.get(test_id) == "passed" for test_id in required)
            else "pending"
        )
        if value.get("status") != expected_status:
            report.add("patch_receipt_drift", "patch receipt status differs from test evidence", identifier)
        if patch.get("status") != expected_status:
            report.add("patch_status_drift", "patch registry status differs from test evidence", identifier)
    return statuses


def _target_status(repo_root: Path, target: str) -> tuple[Path | None, str | None]:
    """Return a contained target and an optional symlink/unsafe error code."""

    try:
        manifest.reject_symlink_components(repo_root)
        relative = manifest.safe_relative_path(target)
    except manifest.ProvenanceError as error:
        return None, error.code
    cursor = repo_root
    for part in relative.parts:
        cursor = cursor / part
        if cursor.is_symlink():
            return cursor, "symlink"
    return repo_root.joinpath(*relative.parts), None


def _verify_lock(
    repo_root: Path,
    source_root: Path,
    lock: Any,
    report: VerificationReport,
    strict_pin: bool,
) -> None:
    if not isinstance(lock, dict) or not isinstance(lock.get("upstream"), dict):
        report.add("invalid_lock", "lock must contain an upstream object")
        return
    try:
        commit = (
            manifest.PINNED_COMMIT
            if strict_pin
            else lock["upstream"].get("commit", manifest.PINNED_COMMIT)
        )
        expected = manifest.build_upstream_lock(
            source_root, commit=commit, strict_pin=strict_pin
        )
    except manifest.ProvenanceError as error:
        report.add(error.code, str(error), error.path)
        return
    if manifest.canonical_json_bytes(lock) != manifest.canonical_json_bytes(expected):
        report.add("lock_drift", "UPSTREAM.lock.json does not match the immutable source")


def _verify_summary_fields(
    source_root: Path,
    ledger: dict[str, Any],
    valid_rows: list[dict[str, Any]],
    report: VerificationReport,
) -> None:
    if ledger.get("entry_count") != len(ledger.get("entries", [])):
        report.add("entry_count_drift", "entry_count does not match entries length")
    observed_kind_counts = dict(sorted(Counter(row.get("kind") for row in valid_rows).items()))
    if ledger.get("kind_counts") != observed_kind_counts:
        report.add("kind_count_drift", "kind_counts does not match ledger rows")
    try:
        expected_counts = manifest._expected_counts(source_root, valid_rows)
    except (OSError, UnicodeDecodeError, KeyError, TypeError) as error:
        report.add("count_failure", f"could not calculate expected counts: {error}")
    else:
        if ledger.get("expected_counts") != expected_counts:
            report.add("expected_count_drift", "expected_counts does not match source rows")


def _verify_poteto_contract(
    ledger: dict[str, Any], source_rows: list[dict[str, Any]], report: VerificationReport
) -> None:
    playbooks = sorted(
        Path(row["source_path"]).name
        for row in source_rows
        if row.get("kind") == "playbook_resource"
    )
    expected_routes = [
        name for name in playbooks if name != manifest.POTETO_SHARED_POSTLUDE
    ]
    expected_postlude = (
        manifest.POTETO_SHARED_POSTLUDE
        if manifest.POTETO_SHARED_POSTLUDE in playbooks
        else None
    )
    contract = ledger.get("poteto_contract")
    if not isinstance(contract, dict):
        report.add("poteto_contract", "poteto_contract must be an object")
        return
    routes = contract.get("routed_playbooks")
    if isinstance(routes, list) and manifest.POTETO_SHARED_POSTLUDE in routes:
        report.add(
            "mistaken_poteto_route",
            "opening-a-pr.md is a shared postlude, not a 23rd routed playbook",
            manifest.POTETO_SHARED_POSTLUDE,
        )
    if routes != expected_routes or contract.get("shared_postlude") != expected_postlude:
        report.add("poteto_contract", "Poteto contract does not match source playbooks")


def _validate_row_shape(row: Any, report: VerificationReport, index: int) -> bool:
    if not isinstance(row, dict):
        report.add("invalid_row", f"ledger entry {index} is not an object")
        return False
    path = row.get("source_path")
    if not isinstance(path, str):
        report.add("invalid_row", f"ledger entry {index} lacks source_path")
        return False
    try:
        manifest.safe_relative_path(path)
    except manifest.ProvenanceError:
        report.add("unsafe_path", "unsafe source_path", str(path))
        return False
    return True


def verify_repository(
    repo_root: Path, *, strict_pin: bool = True, require_complete: bool = False
) -> VerificationReport:
    repo_root = Path(repo_root)
    source_root = repo_root / "upstream" / "pstack"
    ledger_path = repo_root / "provenance" / "parity-ledger.json"
    lock_path = repo_root / "provenance" / "UPSTREAM.lock.json"
    patch_path = repo_root / "provenance" / "patches" / "index.json"
    receipt_path = repo_root / "provenance" / "test-receipts.json"
    report = VerificationReport()

    ledger = _load_json_or_issue(ledger_path, report, "parity ledger")
    registry = _load_json_or_issue(patch_path, report, "patch registry")
    patches = _patch_metadata(registry, report) if registry is not None else {}
    documented_patches = set(patches)
    receipts: Any | None = None
    if receipt_path.exists() or receipt_path.is_symlink():
        receipts = _load_json_or_issue(receipt_path, report, "test receipts")
    _verify_test_receipts(repo_root, patches, receipts, report)
    lock = _load_json_or_issue(lock_path, report, "upstream lock")

    try:
        scanned = manifest.scan_source(source_root)
    except manifest.ProvenanceError as error:
        report.add(error.code, str(error), error.path)
        return report
    except OSError as error:
        report.add("source_scan", f"source scan failed: {error}")
        return report

    report.source_file_count = len(scanned)
    scanned_by_path = {row["source_path"]: row for row in scanned}
    if lock is not None:
        _verify_lock(repo_root, source_root, lock, report, strict_pin)
    if not isinstance(ledger, dict) or not isinstance(ledger.get("entries"), list):
        report.add("invalid_ledger", "ledger must contain an entries list")
        return report

    raw_rows = ledger["entries"]
    report.ledger_entry_count = len(raw_rows)
    valid_rows = [
        row for index, row in enumerate(raw_rows) if _validate_row_shape(row, report, index)
    ]
    rows_by_path: dict[str, dict[str, Any]] = {}
    for row in valid_rows:
        path = row["source_path"]
        if path in rows_by_path:
            report.add("duplicate_source_row", "duplicate source_path row", path)
        else:
            rows_by_path[path] = row

    source_paths = set(scanned_by_path)
    ledger_paths = set(rows_by_path)
    for path in sorted(source_paths - ledger_paths):
        report.add("missing_source_row", "source path has no ledger row", path)
        try:
            kind, _ = manifest.classify_path(path)
        except manifest.ProvenanceError:
            kind = "unclassified"
        if kind == "unclassified":
            report.add("unclassified_source", "source path is not classified", path)
    for path in sorted(ledger_paths - source_paths):
        report.add("extra_source_row", "ledger row has no source file", path)

    targets: dict[str, str] = {}
    source_rows_for_counts: list[dict[str, Any]] = []
    for path in sorted(source_paths & ledger_paths):
        row = rows_by_path[path]
        observed = scanned_by_path[path]
        try:
            expected_kind, expected_component = manifest.classify_path(path)
        except manifest.ProvenanceError:
            expected_kind, expected_component = "unclassified", "unknown"
        if expected_kind == "unclassified":
            report.add("unclassified_source", "source path is not classified", path)
        if row.get("source_sha256") != observed["source_sha256"]:
            report.add("source_hash_drift", "source hash differs from ledger", path)
        if row.get("bytes") != observed["bytes"]:
            report.add("source_size_drift", "source byte count differs from ledger", path)
        if row.get("mode") != observed["mode"]:
            report.add("source_mode_drift", "source mode differs from ledger", path)
        if row.get("kind") != expected_kind:
            report.add("kind_drift", f"expected kind {expected_kind!r}", path)
        if row.get("component") != expected_component:
            report.add("component_drift", f"expected component {expected_component!r}", path)
        if row.get("source_commit") != ledger.get("upstream", {}).get("commit"):
            report.add("source_commit_drift", "row commit differs from ledger upstream", path)

        target = row.get("port_target")
        if target is None:
            report.add("null_port_target", "port_target must be non-null", path)
        elif not isinstance(target, str):
            report.add("invalid_port_target", "port_target must be a string", path)
        else:
            resolved, target_error = _target_status(repo_root, target)
            if target_error:
                report.add(target_error, f"invalid target path: {target}", target)
            try:
                expected_target = manifest.expected_port_target(path)
            except manifest.ProvenanceError:
                expected_target = None
            if target != expected_target:
                report.add(
                    "folded_component",
                    f"target must preserve exact source identity at {expected_target}",
                    path,
                )
            if target in targets:
                report.add(
                    "duplicate_target",
                    f"target is also used by {targets[target]}",
                    target,
                )
            else:
                targets[target] = path

        disposition = row.get("disposition")
        if disposition is None:
            report.add("null_disposition", "disposition must be non-null", path)
        elif disposition not in manifest.DISPOSITIONS:
            report.add("invalid_disposition", f"unknown disposition: {disposition!r}", path)
        review_state = row.get("review_state")
        if review_state is None:
            report.add("null_review_state", "review_state must be non-null", path)
        elif review_state not in manifest.REVIEW_STATES:
            report.add("invalid_review_state", f"unknown review_state: {review_state!r}", path)

        patch_ids = row.get("patch_ids")
        if not isinstance(patch_ids, list) or any(not isinstance(item, str) for item in patch_ids):
            report.add("invalid_patch_ids", "patch_ids must be an explicit string list", path)
            patch_ids = []
        for patch_id in patch_ids:
            if patch_id not in documented_patches:
                report.add("undocumented_patch", f"patch is not documented: {patch_id}", path)
        if (isinstance(disposition, str) and "patch" in disposition) or disposition in {
            "semantic_adapter_pending",
            "semantic_adapter",
        }:
            if not patch_ids:
                report.add("undocumented_patch", "patched disposition requires patch_ids", path)

        parity_tests = row.get("parity_tests")
        if not isinstance(parity_tests, list) or not parity_tests or any(
            not isinstance(item, str) or not item for item in parity_tests
        ):
            report.add("missing_parity_tests", "parity_tests must be an explicit non-empty list", path)

        output_state = row.get("output_state")
        output_hash = row.get("output_sha256")
        output_mode = row.get("output_mode")
        if output_state == "pending":
            report.pending_output_count += 1
            if patch_ids and all(
                patches.get(patch_id, {}).get("status") == "verified"
                for patch_id in patch_ids
            ):
                report.add(
                    "verified_patch_pending_output",
                    "all row patches are verified but the adapted output lacks a receipt",
                    path,
                )
            if output_hash is not None or output_mode is not None:
                report.add(
                    "stale_output_hash",
                    "pending output must not carry a hash or mode receipt",
                    path,
                )
            if isinstance(disposition, str) and not disposition.endswith("_pending"):
                report.add("output_state_drift", "pending output requires pending disposition", path)
            if isinstance(target, str):
                pending_target, pending_error = _target_status(repo_root, target)
                if pending_error:
                    report.add(pending_error, f"invalid target path: {target}", target)
                elif pending_target is not None and pending_target.is_file():
                    report.unreceipted_existing_output_count += 1
        elif output_state == "emitted":
            report.emitted_output_count += 1
            for patch_id in patch_ids:
                if patches.get(patch_id, {}).get("status") != "verified":
                    report.add(
                        "unverified_patch_output",
                        f"emitted adapted output depends on unverified patch: {patch_id}",
                        path,
                    )
            if not isinstance(output_hash, str) or len(output_hash) != 64:
                report.add("stale_output_hash", "emitted output requires a SHA-256 receipt", path)
            if not isinstance(output_mode, str):
                report.add("output_mode_drift", "emitted output requires a mode receipt", path)
            if isinstance(disposition, str) and disposition.endswith("_pending"):
                report.add("output_state_drift", "emitted output cannot retain pending disposition", path)
            if isinstance(target, str):
                resolved, target_error = _target_status(repo_root, target)
                if target_error:
                    report.add(target_error, f"invalid target path: {target}", target)
                elif resolved is not None and not resolved.exists():
                    report.add("missing_output", "emitted target does not exist", target)
                elif resolved is not None:
                    info = resolved.stat(follow_symlinks=False)
                    if not stat.S_ISREG(info.st_mode):
                        report.add("non_regular_output", "emitted target is not regular", target)
                    else:
                        actual_hash = manifest.sha256_file(resolved)
                        actual_mode = f"0o{stat.S_IMODE(info.st_mode):03o}"
                        if output_hash != actual_hash:
                            report.add("stale_output_hash", "output differs from receipt", target)
                        if output_mode != actual_mode:
                            report.add("output_mode_drift", "output mode differs from receipt", target)
        else:
            report.add("invalid_output_state", f"unknown output_state: {output_state!r}", path)

        source_rows_for_counts.append(row)

    ledger_unclassified = ledger.get("unclassified")
    observed_unclassified = sorted(
        row["source_path"]
        for row in source_rows_for_counts
        if row.get("kind") == "unclassified"
    )
    if ledger_unclassified != observed_unclassified:
        report.add("unclassified_drift", "unclassified inventory does not match ledger rows")
    if observed_unclassified:
        for path in observed_unclassified:
            report.add("unclassified_source", "source path is not classified", path)

    _verify_summary_fields(source_root, ledger, source_rows_for_counts, report)
    _verify_poteto_contract(ledger, source_rows_for_counts, report)

    if strict_pin:
        upstream = ledger.get("upstream")
        if isinstance(lock, dict) and upstream != lock.get("upstream"):
            report.add("ledger_pin_drift", "ledger upstream identity differs from lock")
        if ledger.get("poteto_contract") != {
            "routed_playbooks": list(manifest.PINNED_POTETO_ROUTES),
            "shared_postlude": manifest.POTETO_SHARED_POSTLUDE,
        }:
            report.add("mistaken_poteto_route", "pinned Poteto contract is not 22 routes plus postlude")
    if require_complete and report.pending_output_count:
        report.add(
            "pending_output",
            f"release gate requires receipts for all outputs; {report.pending_output_count} remain pending",
        )

    report.issues.sort(key=lambda issue: (issue.code, issue.path or "", issue.message))
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.set_defaults(strict_pin=True)
    parser.add_argument(
        "--strict-pin", dest="strict_pin", action="store_true", help="enforce the canonical pin (default)"
    )
    parser.add_argument(
        "--require-complete",
        action="store_true",
        help="fail if any mapped output still lacks a verified receipt",
    )
    parser.add_argument(
        "--allow-unpinned",
        dest="strict_pin",
        action="store_false",
        help="allow fixture/non-release source; never use for release artifacts",
    )
    args = parser.parse_args(argv)
    report = verify_repository(
        args.repo_root,
        strict_pin=args.strict_pin,
        require_complete=args.require_complete,
    )
    print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    return 0 if report.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
