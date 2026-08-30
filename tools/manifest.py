#!/usr/bin/env python3
"""Build deterministic provenance manifests from the immutable pstack mirror.

This module is deliberately standard-library only.  It never downloads source
or infers a completed output: pending rows have no output receipt.
"""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import tempfile
from typing import Any, Iterable


PINNED_COMMIT = "6fecddba65801f9b9c08b8b328d998ee5b09d290"
PINNED_VERSION = "0.14.5"
PINNED_FILE_COUNT = 157
PINNED_TOTAL_BYTES = 3_091_772
PINNED_TREE_SHA256 = "0b261012eb982e45472b5e368592da26a8c15c92bb12dd680d3786b997c57177"
UPSTREAM_REPOSITORY = "https://github.com/cursor/plugins"
UPSTREAM_SUBTREE = "pstack"
UPSTREAM_AUTHOR = "Lauren Tan"
LICENSE_SPDX = "MIT"

DISPOSITIONS = (
    "verbatim_copy_pending",
    "provenance_copy_pending",
    "mechanical_patch_pending",
    "semantic_adapter_pending",
    "verbatim_copy",
    "provenance_copy",
    "mechanical_patch",
    "semantic_adapter",
)
REVIEW_STATES = (
    "mapped_pending_output",
    "materialized_verified",
    "adapted_verified",
)
OUTPUT_STATES = ("pending", "emitted")

POTETO_SHARED_POSTLUDE = "opening-a-pr.md"
PINNED_POTETO_ROUTES = (
    "authoring-a-skill.md",
    "autonomous-run.md",
    "autopilot-full.md",
    "autopilot-stack.md",
    "babysit.md",
    "bug-fix.md",
    "eval.md",
    "feature.md",
    "hillclimb.md",
    "investigation.md",
    "multi-phase-plan.md",
    "orchestrate.md",
    "pause-safely.md",
    "perf-issue.md",
    "prototype.md",
    "refactoring.md",
    "runtime-forensics.md",
    "session-pickup.md",
    "shipping.md",
    "trace-forensics.md",
    "visual-parity.md",
    "worktree-cleanup.md",
)


class ProvenanceError(ValueError):
    """A deterministic provenance invariant was violated."""

    def __init__(self, code: str, message: str, path: str | None = None):
        super().__init__(message)
        self.code = code
        self.path = path


def canonical_json_bytes(value: Any) -> bytes:
    """Return stable, reviewable JSON bytes."""

    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode(
        "utf-8"
    )


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, value: Any) -> None:
    """Atomically write canonical JSON without following a destination symlink."""

    path = Path(path)
    reject_symlink_components(path.parent)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_symlink():
        raise ProvenanceError("symlink", f"refusing to replace symlink: {path}", str(path))
    payload = canonical_json_bytes(value)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, 0o644)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def reject_symlink_components(path: Path) -> None:
    """Reject an existing symlink anywhere in a lexical path."""

    absolute = Path(os.path.abspath(path))
    cursor = Path(absolute.anchor)
    for part in absolute.parts[1:]:
        cursor = cursor / part
        try:
            info = cursor.lstat()
        except FileNotFoundError:
            break
        if stat.S_ISLNK(info.st_mode):
            raise ProvenanceError("symlink", f"symlink path component: {cursor}", str(cursor))


def safe_relative_path(value: str) -> PurePosixPath:
    """Validate and normalize a repository-relative POSIX path."""

    if not isinstance(value, str) or not value or "\\" in value:
        raise ProvenanceError("unsafe_path", f"invalid relative path: {value!r}")
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in ("", ".", "..") for part in path.parts):
        raise ProvenanceError("unsafe_path", f"unsafe relative path: {value!r}", value)
    if path.as_posix() != value:
        raise ProvenanceError("unsafe_path", f"non-canonical path: {value!r}", value)
    return path


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _walk_regular_files(root: Path) -> list[tuple[str, Path]]:
    """Walk without following symlinks and reject every non-regular entry."""

    root = Path(root)
    reject_symlink_components(root)
    if root.is_symlink():
        raise ProvenanceError("symlink", f"source root is a symlink: {root}", ".")
    if not root.is_dir():
        raise ProvenanceError("missing_source", f"source root is not a directory: {root}")

    files: list[tuple[str, Path]] = []

    def visit(directory: Path, prefix: PurePosixPath | None = None) -> None:
        with os.scandir(directory) as iterator:
            entries = sorted(iterator, key=lambda item: os.fsencode(item.name))
        for entry in entries:
            relative = PurePosixPath(entry.name) if prefix is None else prefix / entry.name
            relative_text = relative.as_posix()
            if entry.is_symlink():
                raise ProvenanceError("symlink", f"symlink in source: {relative_text}", relative_text)
            info = entry.stat(follow_symlinks=False)
            if stat.S_ISDIR(info.st_mode):
                visit(Path(entry.path), relative)
            elif stat.S_ISREG(info.st_mode):
                safe_relative_path(relative_text)
                files.append((relative_text, Path(entry.path)))
            else:
                raise ProvenanceError(
                    "non_regular", f"non-regular source entry: {relative_text}", relative_text
                )

    visit(root)
    files.sort(key=lambda item: item[0].encode("utf-8"))
    return files


def scan_source(root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for relative, absolute in _walk_regular_files(root):
        info = absolute.stat(follow_symlinks=False)
        rows.append(
            {
                "source_path": relative,
                "source_sha256": sha256_file(absolute),
                "bytes": info.st_size,
                "mode": f"0o{stat.S_IMODE(info.st_mode):03o}",
            }
        )
    return rows


def canonical_tree_sha256(rows: Iterable[dict[str, Any]]) -> str:
    """Hash sorted path length + path bytes + raw content digest records."""

    digest = hashlib.sha256()
    for row in sorted(rows, key=lambda item: item["source_path"].encode("utf-8")):
        path_bytes = row["source_path"].encode("utf-8")
        digest.update(len(path_bytes).to_bytes(4, "big"))
        digest.update(path_bytes)
        digest.update(bytes.fromhex(row["source_sha256"]))
    return digest.hexdigest()


def classify_path(source_path: str) -> tuple[str, str]:
    """Classify one upstream path without folding first-class components."""

    path = safe_relative_path(source_path)
    parts = path.parts
    if source_path == ".cursor-plugin/plugin.json":
        return "plugin_manifest", "plugin"
    if len(parts) == 1 and source_path in {".gitignore", "LICENSE", "README.md"}:
        return "root_file", source_path
    if len(parts) == 2 and parts[0] == "agents" and path.suffix == ".md":
        return "agent_prompt", path.stem
    if parts[:2] == ("automations", "benny"):
        if len(parts) == 3 and path.suffix == ".md":
            return "automation_document", "benny"
        if len(parts) >= 5 and parts[2] == "skills" and parts[-1] == "SKILL.md":
            return "automation_skill", parts[3]
        if len(parts) >= 6 and parts[2] == "skills" and parts[-2] == "references":
            return "automation_reference", "benny"
        if len(parts) == 4 and parts[2] == "templates":
            return "automation_template", "benny"
        return "unclassified", "benny"
    if parts[:2] == ("docs", "guide"):
        if len(parts) == 3 and path.suffix == ".md":
            return "guide_document", "guide"
        if len(parts) == 4 and parts[2] == "images":
            return "guide_asset", "guide"
        return "unclassified", "guide"
    if parts and parts[0] == "skills" and len(parts) >= 3:
        component = parts[1]
        if len(parts) == 3 and parts[2] == "SKILL.md":
            kind = "principle_skill" if component.startswith("principle-") else "workflow_skill"
            return kind, component
        if len(parts) >= 4 and parts[2] == "references":
            return "skill_reference", component
        if len(parts) == 4 and parts[2] == "playbooks" and path.suffix == ".md":
            return "playbook_resource", component
        if len(parts) >= 4 and parts[2] == "scripts":
            if source_path.endswith(".test.ts"):
                return "script_test", component
            if source_path.endswith("fakes.test-helper.ts"):
                return "script_test_support", component
            if parts[-1] in {"bun.lock", "package.json", "tsconfig.json"}:
                return "script_build_metadata", component
            return "runtime_script", component
    return "unclassified", path.parts[0]


def expected_port_target(source_path: str) -> str:
    path = safe_relative_path(source_path)
    parts = path.parts
    if parts[0] == "skills":
        return (PurePosixPath("packages/pstack/skills") / PurePosixPath(*parts[1:])).as_posix()
    if parts[0] == "agents":
        return (
            PurePosixPath("packages/pstack-runtime/resources/agents")
            / PurePosixPath(*parts[1:])
        ).as_posix()
    if parts[:2] == ("automations", "benny"):
        return (
            PurePosixPath("packages/pstack-benny/resources/benny")
            / PurePosixPath(*parts[2:])
        ).as_posix()
    if parts[:2] == ("docs", "guide"):
        return (PurePosixPath("docs/upstream-guide") / PurePosixPath(*parts[2:])).as_posix()
    return (PurePosixPath("provenance/upstream-root") / path).as_posix()


_HOST_BOUND_PATTERN = re.compile(
    r"(?:\bCursor\b|\.cursor(?:/|\b)|subagent_type|AskQuestion|/loop\b|"
    r"cloud[- ]agent|agent-transcripts|pstack-models\.mdc|cursor-agent|"
    r"control-(?:ui|cli)|(?:^|[`\s])Task\s*\(|CURSOR_AUTOMATION_ID|"
    r"[\"']cursor[\"']|@cursor-skill|claude-fable-5-thinking-max|"
    r"gpt-5\.6-sol-max|grok-4\.6-fast-xhigh|claude-opus-5-thinking-xhigh)",
    re.MULTILINE,
)


def _text_has_host_binding(path: Path, skill_names: Iterable[str] = ()) -> bool:
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return False
    if _HOST_BOUND_PATTERN.search(text):
        return True
    names = tuple(sorted(set(skill_names), key=lambda item: (-len(item), item)))
    if not names:
        return False
    slash_call = re.compile(
        r"(?<![A-Za-z0-9])/(?:" + "|".join(re.escape(name) for name in names) + r")\b"
    )
    return bool(slash_call.search(text))


def disposition_for(
    source_path: str,
    kind: str,
    absolute_path: Path,
    skill_names: Iterable[str] = (),
) -> tuple[str, list[str]]:
    """Select a conservative pending translation class and documented patch IDs."""

    if kind in {"plugin_manifest", "root_file"}:
        return "provenance_copy_pending", []
    if source_path == "skills/make-bot-ui/SKILL.md":
        return "semantic_adapter_pending", ["PATCH-HERMES-MAKE-BOT-UI"]
    if source_path == "skills/poteto-mode/SKILL.md":
        return "semantic_adapter_pending", ["PATCH-POTETO-RUNTIME-ADAPTER"]
    if source_path == "skills/setup-pstack/SKILL.md":
        return "semantic_adapter_pending", ["PATCH-SETUP-RUNTIME-CONFIG"]
    if source_path == "skills/poteto-mode/scripts/bootstrap.ts":
        return "mechanical_patch_pending", ["PATCH-HERMES-NO-IMPLICIT-INSTALL"]
    if kind == "guide_document":
        return "mechanical_patch_pending", ["PATCH-HERMES-GUIDE-COMMANDS"]
    if kind in {
        "runtime_script",
        "script_build_metadata",
        "script_test",
        "script_test_support",
    }:
        if _text_has_host_binding(absolute_path, skill_names):
            return "mechanical_patch_pending", ["PATCH-HERMES-SCRIPT-PATHS"]
        return "verbatim_copy_pending", []
    if kind in {"agent_prompt", "automation_document", "automation_reference", "automation_skill", "automation_template", "guide_asset"}:
        return "verbatim_copy_pending", []
    if _text_has_host_binding(absolute_path, skill_names):
        return "mechanical_patch_pending", ["PATCH-HERMES-SKILL-PRIMITIVES"]
    return "verbatim_copy_pending", []


def parity_tests_for(kind: str, source_path: str, patch_ids: list[str]) -> list[str]:
    tests = ["source-integrity", "target-identity"]
    if kind in {"workflow_skill", "principle_skill", "automation_skill"}:
        tests.append("first-class-component")
    if kind == "playbook_resource":
        tests.append("poteto-route-cardinality")
    if patch_ids:
        tests.extend(("patch-registry", "pending-receipt-discipline"))
    return tests


def default_patch_registry() -> dict[str, Any]:
    patches = [
        {
            "id": "PATCH-HERMES-GUIDE-COMMANDS",
            "status": "pending",
            "class": "mechanical",
            "purpose": "Translate Cursor installation, invocation, and command examples to supported Hermes equivalents without removing guide content.",
            "required_tests": ["guide-link-completeness", "unsupported-primitive-scan"],
        },
        {
            "id": "PATCH-HERMES-SCRIPT-PATHS",
            "status": "pending",
            "class": "mechanical",
            "purpose": "Make script paths and host integrations portable while preserving the complete script and test tree.",
            "required_tests": ["upstream-script-suite", "portable-path-scan"],
        },
        {
            "id": "PATCH-HERMES-NO-IMPLICIT-INSTALL",
            "status": "pending",
            "class": "mechanical",
            "purpose": "Fail closed when Poteto script dependencies are absent instead of downloading or mutating an installed plugin implicitly.",
            "required_tests": ["no-implicit-install", "direct-script-contract"],
        },
        {
            "id": "PATCH-HERMES-SKILL-PRIMITIVES",
            "status": "pending",
            "class": "mechanical",
            "purpose": "Replace Cursor-only skill primitives with behaviorally equivalent supported Hermes operations.",
            "required_tests": ["explicit-skill-invocation", "unsupported-primitive-scan"],
        },
        {
            "id": "PATCH-HERMES-MAKE-BOT-UI",
            "status": "pending",
            "class": "semantic",
            "purpose": "Translate Make Bot UI to Hermes authenticated webhooks, loopback-first serving, explicit approval gates, and verified end-to-end receipts.",
            "required_tests": ["make-bot-ui-runtime-contract", "make-bot-ui-authority-gate"],
        },
        {
            "id": "PATCH-POTETO-RUNTIME-ADAPTER",
            "status": "pending",
            "class": "semantic",
            "purpose": "Preserve Poteto orchestration across 22 routes and the separate opening-a-pr postlude using Hermes-native runtime boundaries.",
            "required_tests": ["poteto-route-cardinality", "representative-delegation"],
        },
        {
            "id": "PATCH-SETUP-RUNTIME-CONFIG",
            "status": "pending",
            "class": "semantic",
            "purpose": "Translate setup-pstack configuration behavior without claiming unsupported Hermes configuration or installation features.",
            "required_tests": ["disposable-profile-setup", "authority-gate"],
        },
    ]
    return {
        "schema_version": 1,
        "description": "Documented translation patches. A ledger patch ID must resolve here before output can be emitted.",
        "patches": patches,
    }


def _declared_test_count(root: Path, rows: list[dict[str, Any]]) -> int:
    pattern = re.compile(r"^\s*(?:test|it)\(", re.MULTILINE)
    total = 0
    for row in rows:
        if row["kind"] != "script_test":
            continue
        text = (root / row["source_path"]).read_text(encoding="utf-8")
        total += len(pattern.findall(text))
    return total


def _expected_counts(root: Path, rows: list[dict[str, Any]]) -> dict[str, int]:
    count = Counter(row["kind"] for row in rows)
    playbooks = sorted(
        PurePosixPath(row["source_path"]).name
        for row in rows
        if row["kind"] == "playbook_resource"
    )
    return {
        "source_paths": len(rows),
        "source_bytes": sum(row["bytes"] for row in rows),
        "registered_skills": count["workflow_skill"] + count["principle_skill"],
        "workflow_skills": count["workflow_skill"],
        "principle_skills": count["principle_skill"],
        "benny_skills": count["automation_skill"],
        "agent_prompts": count["agent_prompt"],
        "playbook_files": count["playbook_resource"],
        "routed_playbooks": len([name for name in playbooks if name != POTETO_SHARED_POSTLUDE]),
        "shared_postludes": int(POTETO_SHARED_POSTLUDE in playbooks),
        "reference_files": count["skill_reference"] + count["automation_reference"],
        "script_tree_files": sum(
            count[kind]
            for kind in (
                "runtime_script",
                "script_build_metadata",
                "script_test",
                "script_test_support",
            )
        ),
        "executable_test_suites": count["script_test"],
        "declared_tests": _declared_test_count(root, rows),
        "guide_documents": count["guide_document"],
        "guide_images": count["guide_asset"],
    }


def build_upstream_lock(source_root: Path, *, commit: str = PINNED_COMMIT, strict_pin: bool = True) -> dict[str, Any]:
    source_root = Path(source_root)
    rows = scan_source(source_root)
    plugin = load_json(source_root / ".cursor-plugin" / "plugin.json")
    author_value = plugin.get("author", {})
    author = author_value.get("name") if isinstance(author_value, dict) else author_value
    license_hash = sha256_file(source_root / "LICENSE")
    tree_hash = canonical_tree_sha256(rows)
    version = plugin.get("version")
    if strict_pin:
        observed = {
            "commit": commit,
            "version": version,
            "file_count": len(rows),
            "total_bytes": sum(row["bytes"] for row in rows),
            "tree_sha256": tree_hash,
            "author": author,
            "license": plugin.get("license"),
        }
        expected = {
            "commit": PINNED_COMMIT,
            "version": PINNED_VERSION,
            "file_count": PINNED_FILE_COUNT,
            "total_bytes": PINNED_TOTAL_BYTES,
            "tree_sha256": PINNED_TREE_SHA256,
            "author": UPSTREAM_AUTHOR,
            "license": LICENSE_SPDX,
        }
        if observed != expected:
            raise ProvenanceError("pin_mismatch", f"pinned source mismatch: {observed!r}")
    return {
        "schema_version": 1,
        "upstream": {
            "name": "pstack",
            "subtree": UPSTREAM_SUBTREE,
            "repository": plugin.get("repository", UPSTREAM_REPOSITORY),
            "homepage": plugin.get("homepage"),
            "version": version,
            "commit": commit,
            "file_count": len(rows),
            "total_bytes": sum(row["bytes"] for row in rows),
            "tree_sha256": tree_hash,
            "tree_hash_algorithm": "sha256(sorted(4-byte-be-path-length || utf8-posix-path || raw-file-sha256))",
            "author": author,
            "license": {
                "spdx": plugin.get("license"),
                "source_path": "LICENSE",
                "source_sha256": license_hash,
                "copyright": "Copyright (c) 2026 Lauren Tan",
            },
        },
    }


def build_parity_ledger(
    source_root: Path,
    *,
    commit: str = PINNED_COMMIT,
    strict_pin: bool = True,
) -> dict[str, Any]:
    source_root = Path(source_root)
    lock = build_upstream_lock(source_root, commit=commit, strict_pin=strict_pin)
    scanned = scan_source(source_root)
    classified = {
        source["source_path"]: classify_path(source["source_path"]) for source in scanned
    }
    skill_names = {
        component
        for kind, component in classified.values()
        if kind in {"workflow_skill", "principle_skill"}
    }
    entries: list[dict[str, Any]] = []
    unclassified: list[str] = []
    for source in scanned:
        source_path = source["source_path"]
        kind, component = classified[source_path]
        if kind == "unclassified":
            unclassified.append(source_path)
        disposition, patch_ids = disposition_for(
            source_path, kind, source_root / source_path, skill_names
        )
        entries.append(
            {
                **source,
                "source_commit": commit,
                "kind": kind,
                "component": component,
                "port_target": expected_port_target(source_path),
                "disposition": disposition,
                "patch_ids": patch_ids,
                "parity_tests": parity_tests_for(kind, source_path, patch_ids),
                "review_state": "mapped_pending_output",
                "output_state": "pending",
                "output_sha256": None,
                "output_mode": None,
            }
        )
    if unclassified:
        raise ProvenanceError(
            "unclassified_source",
            f"unclassified source paths: {', '.join(sorted(unclassified))}",
        )
    entries.sort(key=lambda row: row["source_path"].encode("utf-8"))
    kind_counts = dict(sorted(Counter(row["kind"] for row in entries).items()))
    playbooks = sorted(
        PurePosixPath(row["source_path"]).name
        for row in entries
        if row["kind"] == "playbook_resource"
    )
    poteto_contract = {
        "routed_playbooks": [name for name in playbooks if name != POTETO_SHARED_POSTLUDE],
        "shared_postlude": POTETO_SHARED_POSTLUDE if POTETO_SHARED_POSTLUDE in playbooks else None,
    }
    return {
        "schema_version": 2,
        "schema": {
            "row_identity": "Exactly one row per upstream regular file, keyed by source_path.",
            "disposition_vocabulary": {
                "verbatim_copy_pending": "Exact copy is planned; no output receipt exists.",
                "provenance_copy_pending": "Exact archival copy is planned under provenance; no output receipt exists.",
                "mechanical_patch_pending": "A documented syntax/primitive translation is required; no output receipt exists.",
                "semantic_adapter_pending": "A documented behavior-preserving Hermes adapter is required; no output receipt exists.",
                "verbatim_copy": "Exact copy emitted and receipt verified.",
                "provenance_copy": "Exact provenance copy emitted and receipt verified.",
                "mechanical_patch": "Documented mechanical translation emitted and receipt verified.",
                "semantic_adapter": "Documented semantic adapter emitted and receipt verified.",
            },
            "pending_output_rule": "output_state=pending requires output_sha256 and output_mode to be null.",
            "emitted_output_rule": "output_state=emitted requires a verified output_sha256 and output_mode receipt.",
            "patch_rule": "Every patch_ids value must resolve in provenance/patches/index.json.",
            "target_rule": "Every port_target is unique, repository-relative, path-safe, and preserves its first-class upstream component.",
        },
        "upstream": lock["upstream"],
        "expected_counts": _expected_counts(source_root, entries),
        "kind_counts": kind_counts,
        "entry_count": len(entries),
        "unclassified": unclassified,
        "poteto_contract": poteto_contract,
        "entries": entries,
    }


def _summary(ledger: dict[str, Any]) -> dict[str, Any]:
    return {
        "entry_count": ledger["entry_count"],
        "pending_output_count": sum(
            row["output_state"] == "pending" for row in ledger["entries"]
        ),
        "unclassified": ledger["unclassified"],
        "tree_sha256": ledger["upstream"]["tree_sha256"],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--source-root", type=Path)
    parser.add_argument("--commit", default=PINNED_COMMIT)
    parser.set_defaults(strict_pin=True)
    parser.add_argument(
        "--strict-pin", dest="strict_pin", action="store_true", help="enforce the canonical pin (default)"
    )
    parser.add_argument(
        "--allow-unpinned",
        dest="strict_pin",
        action="store_false",
        help="allow fixture/non-release source; never use for release artifacts",
    )
    parser.add_argument("--write", action="store_true", help="write lock and ledger atomically")
    args = parser.parse_args(argv)
    source_root = args.source_root or args.repo_root / "upstream" / "pstack"
    try:
        ledger = build_parity_ledger(
            source_root, commit=args.commit, strict_pin=args.strict_pin
        )
        if args.write:
            write_json(args.repo_root / "provenance" / "UPSTREAM.lock.json", {
                "schema_version": 1,
                "upstream": ledger["upstream"],
            })
            write_json(args.repo_root / "provenance" / "parity-ledger.json", ledger)
        print(json.dumps(_summary(ledger), sort_keys=True))
        return 0
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(json.dumps({"ok": False, "error": str(error)}, sort_keys=True))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
