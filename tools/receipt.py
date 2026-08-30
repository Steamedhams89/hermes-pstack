#!/usr/bin/env python3
"""Run documented pstack adaptation gates and write deterministic receipts.

The command is a dry run unless ``--write`` is supplied. It never changes a
live Hermes profile. Frozen Poteto script dependencies are provisioned only
when ``--provision-script-deps`` is explicitly supplied, and only inside an
automatically removed temporary copy of the script tree.
"""

from __future__ import annotations

import argparse
import copy
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import sys
import tempfile
from typing import Any, Callable, Iterable, Sequence

try:
    from . import manifest
except ImportError:  # Direct script execution.
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from tools import manifest


RECEIPT_PATH = Path("provenance/test-receipts.json")
PATCH_PATH = Path("provenance/patches/index.json")
LEDGER_PATH = Path("provenance/parity-ledger.json")
SCRIPT_ROOT = Path("packages/pstack/skills/poteto-mode/scripts")


@dataclass(frozen=True)
class CommandSpec:
    argv: tuple[str, ...]
    cwd: str = "."
    executable: str = "python"


@dataclass(frozen=True)
class TestSpec:
    commands: tuple[CommandSpec, ...]
    inputs: tuple[str, ...]


def _pytest(*nodes: str) -> CommandSpec:
    return CommandSpec(
        (
            "python",
            "-B",
            "-m",
            "pytest",
            "-q",
            "-p",
            "no:cacheprovider",
            *nodes,
        )
    )


TEST_SPECS: dict[str, TestSpec] = {
    "authority-gate": TestSpec(
        commands=(
            _pytest(
                "tests/test_plugin_pstack_full.py::test_exact_negative_fixtures_and_authority_path_behavior",
                "tests/test_guide_port.py::GuidePortTests::test_examples_do_not_execute_external_or_live_profile_actions",
                "tests/test_guide_port.py::GuidePortTests::test_risk_bearing_pages_state_their_authority_boundaries",
            ),
        ),
        inputs=("tests/test_plugin_pstack_full.py", "tests/test_guide_port.py"),
    ),
    "direct-script-contract": TestSpec(
        commands=(
            _pytest(
                "tests/test_plugin_pstack_full.py::test_exact_negative_fixtures_and_authority_path_behavior"
            ),
        ),
        inputs=("tests/test_plugin_pstack_full.py",),
    ),
    "disposable-profile-setup": TestSpec(
        commands=(
            _pytest(
                "tests/test_runtime_pstack_full.py::test_registered_route_tool_get_has_no_registration_or_get_write",
                "tests/test_runtime_pstack_full.py::test_registered_route_tool_set_requires_complete_mapping_and_reads_back",
                "tests/test_runtime_pstack_full.py::test_registered_route_tool_refuses_incomplete_bad_and_symlinked_sets",
                "tests/test_runtime_pstack_full.py::test_setup_skill_uses_registered_tool_and_route_dispatch_contract",
            ),
        ),
        inputs=("tests/test_runtime_pstack_full.py",),
    ),
    "explicit-skill-invocation": TestSpec(
        commands=(
            _pytest(
                "tests/test_plugin_pstack_full.py::test_every_qualified_cross_reference_resolves_and_playbooks_are_linked_resources",
                "tests/test_plugin_pstack_full.py::test_fresh_process_qualified_loading_and_linked_poteto_resource",
            ),
        ),
        inputs=("tests/test_plugin_pstack_full.py",),
    ),
    "guide-link-completeness": TestSpec(
        commands=(
            _pytest(
                "tests/test_guide_port.py::GuidePortTests::test_relative_links_and_fragments_resolve"
            ),
        ),
        inputs=("tests/test_guide_port.py",),
    ),
    "make-bot-ui-authority-gate": TestSpec(
        commands=(
            _pytest(
                "tests/test_plugin_pstack_full.py::test_make_bot_ui_requires_approval_before_recurring_security_or_exposure_changes"
            ),
        ),
        inputs=("tests/test_plugin_pstack_full.py",),
    ),
    "make-bot-ui-runtime-contract": TestSpec(
        commands=(
            _pytest(
                "tests/test_plugin_pstack_full.py::test_make_bot_ui_uses_hermes_webhook_hmac_and_loopback_relay_contract"
            ),
        ),
        inputs=("tests/test_plugin_pstack_full.py",),
    ),
    "no-implicit-install": TestSpec(
        commands=(
            _pytest(
                "tests/test_plugin_pstack_full.py::test_bootstrap_fails_closed_without_implicit_provisioning_and_is_node_parseable"
            ),
        ),
        inputs=("tests/test_plugin_pstack_full.py",),
    ),
    "portable-path-scan": TestSpec(
        commands=(
            _pytest(
                "tests/test_plugin_pstack_full.py::test_workspace_has_no_cache_bytecode_or_machine_absolute_artifacts",
                "tests/test_plugin_pstack_full.py::test_executable_package_code_has_no_dean_path_or_live_cursor_state_path",
                "tests/test_workspace_contract.py::test_materialized_artifact_has_no_machine_specific_home_path",
            ),
        ),
        inputs=("tests/test_plugin_pstack_full.py", "tests/test_workspace_contract.py"),
    ),
    "poteto-route-cardinality": TestSpec(
        commands=(
            _pytest(
                "tests/test_parity_checked_in.py::CheckedInParityTests::test_poteto_contract_is_22_routes_plus_postlude",
                "tests/test_plugin_pstack_full.py::test_every_qualified_cross_reference_resolves_and_playbooks_are_linked_resources",
            ),
        ),
        inputs=("tests/test_parity_checked_in.py", "tests/test_plugin_pstack_full.py"),
    ),
    "representative-delegation": TestSpec(
        commands=(
            _pytest(
                "tests/test_plugin_pstack_full.py::test_role_bearing_workflows_read_named_route_or_fall_back_to_inherited_delegation",
                "tests/test_runtime_pstack_full.py::test_direct_route_describes_native_primitive_without_executing_it",
                "tests/test_runtime_pstack_full.py::test_non_parent_alias_requires_runtime_and_explicit_capability",
                "tests/test_runtime_pstack_full.py::test_fake_safe_adapter_is_injected_and_returns_only_its_local_receipt",
            ),
        ),
        inputs=("tests/test_plugin_pstack_full.py", "tests/test_runtime_pstack_full.py"),
    ),
    "unsupported-primitive-scan": TestSpec(
        commands=(
            _pytest(
                "tests/test_guide_port.py::GuidePortTests::test_adapted_markdown_has_no_live_cursor_mechanics",
                "tests/test_plugin_pstack_full.py::test_operative_markdown_has_no_live_cursor_runtime_primitive",
            ),
        ),
        inputs=("tests/test_guide_port.py", "tests/test_plugin_pstack_full.py"),
    ),
    "upstream-script-suite": TestSpec(
        commands=(
            CommandSpec(("bun", "test", "--parallel=1", "orch/orch.test.ts"), SCRIPT_ROOT.as_posix(), "bun"),
            CommandSpec(
                ("bun", "test", "--parallel=1", "watch-pr/github.test.ts"),
                SCRIPT_ROOT.as_posix(),
                "bun",
            ),
            CommandSpec(
                ("bun", "test", "--parallel=1", "watch-pr/policy.test.ts"),
                SCRIPT_ROOT.as_posix(),
                "bun",
            ),
            CommandSpec(
                ("bun", "test", "--parallel=1", "watch-pr/cli.test.ts"),
                SCRIPT_ROOT.as_posix(),
                "bun",
            ),
            CommandSpec(("bun", "run", "typecheck"), SCRIPT_ROOT.as_posix(), "bun"),
        ),
        inputs=((SCRIPT_ROOT / "package.json").as_posix(), (SCRIPT_ROOT / "bun.lock").as_posix()),
    ),
}


class ReceiptError(ValueError):
    def __init__(self, code: str, message: str, path: str | None = None):
        super().__init__(message)
        self.code = code
        self.path = path


@dataclass(frozen=True)
class ReceiptResult:
    write: bool
    ok: bool
    passed_test_count: int
    failed_test_count: int
    verified_patch_count: int
    pending_patch_count: int
    emitted_adapted_count: int
    pending_adapted_count: int
    issues: tuple[dict[str, str], ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "write": self.write,
            "ok": self.ok,
            "passed_test_count": self.passed_test_count,
            "failed_test_count": self.failed_test_count,
            "verified_patch_count": self.verified_patch_count,
            "pending_patch_count": self.pending_patch_count,
            "emitted_adapted_count": self.emitted_adapted_count,
            "pending_adapted_count": self.pending_adapted_count,
            "issues": list(self.issues),
        }


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _safe_target(repo_root: Path, relative_text: str) -> Path:
    manifest.reject_symlink_components(repo_root)
    relative = manifest.safe_relative_path(relative_text)
    cursor = repo_root
    for part in relative.parts:
        cursor = cursor / part
        if cursor.is_symlink():
            raise ReceiptError("symlink", f"target traverses a symlink: {relative_text}", relative_text)
    return repo_root.joinpath(*relative.parts)


def _required_test_ids(registry: dict[str, Any]) -> tuple[str, ...]:
    patches = registry.get("patches")
    if not isinstance(patches, list):
        raise ReceiptError("invalid_patch_registry", "patch registry must contain a patches list")
    required: set[str] = set()
    identifiers: set[str] = set()
    for patch in patches:
        if not isinstance(patch, dict) or not isinstance(patch.get("id"), str):
            raise ReceiptError("invalid_patch_registry", "every patch requires a string id")
        patch_id = patch["id"]
        if patch_id in identifiers:
            raise ReceiptError("duplicate_patch", f"duplicate patch id: {patch_id}", patch_id)
        identifiers.add(patch_id)
        tests = patch.get("required_tests")
        if not isinstance(tests, list) or not tests or any(not isinstance(item, str) or not item for item in tests):
            raise ReceiptError("invalid_patch_registry", f"patch {patch_id} requires a non-empty test list", patch_id)
        if len(tests) != len(set(tests)):
            raise ReceiptError("invalid_patch_registry", f"patch {patch_id} repeats a test id", patch_id)
        for test_id in tests:
            if test_id not in TEST_SPECS:
                raise ReceiptError("unknown_test_id", f"unknown required test id: {test_id}", patch_id)
            required.add(test_id)
    return tuple(sorted(required))


def _expand_inputs(repo_root: Path, test_id: str, spec: TestSpec) -> dict[str, str]:
    paths: set[Path] = {Path("tools/receipt.py")}
    paths.update(Path(value) for value in spec.inputs)
    if test_id == "upstream-script-suite":
        script_root = repo_root / SCRIPT_ROOT
        for path in script_root.rglob("*"):
            if path.is_file() and not path.is_symlink() and "node_modules" not in path.parts:
                paths.add(path.relative_to(repo_root))
    receipts: dict[str, str] = {}
    for relative in sorted(paths, key=lambda item: item.as_posix().encode("utf-8")):
        target = _safe_target(repo_root, relative.as_posix())
        if not target.is_file():
            raise ReceiptError("missing_test_input", f"missing test input: {relative.as_posix()}", relative.as_posix())
        info = target.stat(follow_symlinks=False)
        if not stat.S_ISREG(info.st_mode):
            raise ReceiptError("non_regular_test_input", f"test input is not regular: {relative.as_posix()}", relative.as_posix())
        receipts[relative.as_posix()] = manifest.sha256_file(target)
    return receipts


_ANSI = re.compile(r"\x1b\[[0-9;]*m")
_DURATION = re.compile(r"\bin\s+\d+(?:\.\d+)?s\b")
_BRACKETED_DURATION = re.compile(r"\[\d+(?:\.\d+)?(?:ns|us|µs|ms|s)\]")
_BUN_PARALLEL_LABEL = re.compile(r"(?m)^(bun test v[^\n]+?) \d+x PARALLEL$")
_GITHUB_GROUP_PREFIX = re.compile(r"(?m)^::group::")
_GITHUB_END_GROUP = re.compile(r"(?m)^::endgroup::(?:\n\n|\n|$)")
_TEMP_PATH = re.compile(r"/tmp/(?:pytest-of-[^/\s]+/pytest-\d+|pstack-receipt-[^/\s]+)")


def _normalize_output(text: str, repo_root: Path, hermes_home: Path) -> str:
    value = _ANSI.sub("", text.replace("\r\n", "\n"))
    value = _BUN_PARALLEL_LABEL.sub(r"\1", value)
    value = _GITHUB_GROUP_PREFIX.sub("", value)
    value = _GITHUB_END_GROUP.sub("", value)
    replacements = {
        str(repo_root): "<repo>",
        str(hermes_home): "<hermes-home>",
    }
    hermes_source = os.environ.get("HERMES_SOURCE_ROOT")
    if hermes_source:
        replacements[hermes_source] = "<hermes-source>"
    for raw, replacement in sorted(replacements.items(), key=lambda item: -len(item[0])):
        value = value.replace(raw, replacement)
    value = _TEMP_PATH.sub("<tmp>", value)
    value = _DURATION.sub("in <duration>s", value)
    value = _BRACKETED_DURATION.sub("[<duration>]", value)
    return value.strip() + ("\n" if value.strip() else "")


def _display_command(command: CommandSpec) -> dict[str, Any]:
    return {"argv": list(command.argv), "cwd": command.cwd}


def _execute_command(
    repo_root: Path,
    command: CommandSpec,
    environment: dict[str, str],
    hermes_home: Path,
    *,
    cwd_override: Path | None = None,
    display_cwd: str | None = None,
) -> dict[str, Any]:
    if command.executable == "python":
        executable_argv = (sys.executable, *command.argv[1:])
    else:
        executable_argv = command.argv
    cwd = (
        cwd_override
        if cwd_override is not None
        else _safe_target(repo_root, command.cwd) if command.cwd != "." else repo_root
    )
    display = _display_command(command)
    if display_cwd is not None:
        display["cwd"] = display_cwd
    try:
        result = subprocess.run(
            executable_argv,
            cwd=cwd,
            env=environment,
            capture_output=True,
            text=True,
            check=False,
            timeout=180,
        )
    except FileNotFoundError:
        return {
            **display,
            "exit_code": 127,
            "output_sha256": _sha256_bytes(f"executable not found: {command.executable}\n".encode()),
            "error": f"executable not found: {command.executable}",
        }
    except subprocess.TimeoutExpired as error:
        combined = (error.stdout or "") + (error.stderr or "")
        normalized = _normalize_output(combined, repo_root, hermes_home)
        return {
            **display,
            "exit_code": 124,
            "output_sha256": _sha256_bytes(normalized.encode()),
            "error": "command timed out after 180 seconds",
        }
    combined = result.stdout + result.stderr
    normalized = _normalize_output(combined, repo_root, hermes_home)
    return {
        **display,
        "exit_code": result.returncode,
        "output_sha256": _sha256_bytes(normalized.encode()),
    }


def run_test_spec(
    repo_root: Path,
    test_id: str,
    spec: TestSpec,
    *,
    provision_script_deps: bool = False,
) -> dict[str, Any]:
    environment = os.environ.copy()
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    environment["PYTEST_ADDOPTS"] = "-p no:cacheprovider"
    python_paths = [str(repo_root), str(repo_root / "packages")]
    hermes_source = environment.get("HERMES_SOURCE_ROOT")
    if hermes_source:
        python_paths.append(hermes_source)
    existing = environment.get("PYTHONPATH")
    if existing:
        python_paths.append(existing)
    environment["PYTHONPATH"] = os.pathsep.join(python_paths)
    with tempfile.TemporaryDirectory(prefix="pstack-receipt-") as temporary:
        hermes_home = Path(temporary) / "hermes-home"
        environment["HERMES_HOME"] = str(hermes_home)
        if test_id == "upstream-script-suite" and provision_script_deps:
            script_copy = Path(temporary) / "poteto-scripts"
            shutil.copytree(
                repo_root / SCRIPT_ROOT,
                script_copy,
                ignore=shutil.ignore_patterns("node_modules"),
            )
            ephemeral_cwd = f"ephemeral:{SCRIPT_ROOT.as_posix()}"
            install = CommandSpec(
                ("bun", "install", "--frozen-lockfile"),
                SCRIPT_ROOT.as_posix(),
                "bun",
            )
            commands = [
                _execute_command(
                    repo_root,
                    install,
                    environment,
                    hermes_home,
                    cwd_override=script_copy,
                    display_cwd=ephemeral_cwd,
                )
            ]
            commands.extend(
                _execute_command(
                    repo_root,
                    command,
                    environment,
                    hermes_home,
                    cwd_override=script_copy,
                    display_cwd=ephemeral_cwd,
                )
                for command in spec.commands
            )
        else:
            commands = [
                _execute_command(repo_root, command, environment, hermes_home)
                for command in spec.commands
            ]
    passed = all(command["exit_code"] == 0 for command in commands)
    return {
        "status": "passed" if passed else "failed",
        "commands": commands,
        "inputs": _expand_inputs(repo_root, test_id, spec),
    }


def _patch_statuses(
    registry: dict[str, Any], test_receipts: dict[str, dict[str, Any]]
) -> dict[str, str]:
    statuses: dict[str, str] = {}
    for patch in registry["patches"]:
        required = patch["required_tests"]
        statuses[patch["id"]] = (
            "verified"
            if all(test_receipts.get(test_id, {}).get("status") == "passed" for test_id in required)
            else "pending"
        )
    return statuses


def _set_pending(row: dict[str, Any]) -> None:
    disposition = row.get("disposition")
    if isinstance(disposition, str) and not disposition.endswith("_pending"):
        row["disposition"] = f"{disposition}_pending"
    row["review_state"] = "mapped_pending_output"
    row["output_state"] = "pending"
    row["output_sha256"] = None
    row["output_mode"] = None


def apply_patch_receipts(
    repo_root: Path,
    ledger: dict[str, Any],
    statuses: dict[str, str],
) -> tuple[dict[str, Any], tuple[dict[str, str], ...]]:
    updated = copy.deepcopy(ledger)
    issues: list[dict[str, str]] = []
    for row in updated.get("entries", []):
        patch_ids = row.get("patch_ids")
        if not patch_ids:
            continue
        if any(statuses.get(patch_id) != "verified" for patch_id in patch_ids):
            _set_pending(row)
            continue
        target_text = row.get("port_target")
        try:
            if not isinstance(target_text, str):
                raise ReceiptError("invalid_port_target", "adapted row has no target", str(row.get("source_path")))
            target = _safe_target(repo_root, target_text)
            if not target.exists():
                raise ReceiptError("missing_output", f"adapted output does not exist: {target_text}", target_text)
            info = target.stat(follow_symlinks=False)
            if not stat.S_ISREG(info.st_mode):
                raise ReceiptError("non_regular_output", f"adapted output is not regular: {target_text}", target_text)
            actual_mode = f"0o{stat.S_IMODE(info.st_mode):03o}"
            if actual_mode != row.get("mode"):
                raise ReceiptError("output_mode_drift", f"adapted output mode differs: {target_text}", target_text)
            actual_hash = manifest.sha256_file(target)
        except (OSError, manifest.ProvenanceError, ReceiptError) as error:
            _set_pending(row)
            issues.append(
                {
                    "code": getattr(error, "code", "output_receipt_failure"),
                    "message": str(error),
                    "path": getattr(error, "path", None) or str(target_text),
                }
            )
            continue
        disposition = row.get("disposition")
        if isinstance(disposition, str):
            row["disposition"] = disposition.removesuffix("_pending")
        row["review_state"] = "adapted_verified"
        row["output_state"] = "emitted"
        row["output_sha256"] = actual_hash
        row["output_mode"] = actual_mode
    issues.sort(key=lambda issue: (issue["code"], issue["path"], issue["message"]))
    return updated, tuple(issues)


def _receipt_document(
    registry: dict[str, Any], test_receipts: dict[str, dict[str, Any]], statuses: dict[str, str]
) -> dict[str, Any]:
    patch_verification = {
        patch["id"]: {
            "status": statuses[patch["id"]],
            "required_tests": list(patch["required_tests"]),
        }
        for patch in sorted(registry["patches"], key=lambda value: value["id"])
    }
    return {
        "schema_version": 1,
        "description": "Deterministic local evidence for documented Hermes adaptation gates; frozen script dependencies are installed only in an explicitly provisioned, automatically removed temporary copy.",
        "tests": {test_id: test_receipts[test_id] for test_id in sorted(test_receipts)},
        "patch_verification": patch_verification,
    }


def receipt_repository(
    repo_root: Path,
    *,
    write: bool = False,
    runner: Callable[[Path, str, TestSpec], dict[str, Any]] | None = None,
    provision_script_deps: bool = False,
) -> ReceiptResult:
    repo_root = Path(repo_root)
    manifest.reject_symlink_components(repo_root)
    registry = manifest.load_json(repo_root / PATCH_PATH)
    ledger = manifest.load_json(repo_root / LEDGER_PATH)
    required_ids = _required_test_ids(registry)
    selected_runner = runner or (
        lambda root, test_id, spec: run_test_spec(
            root,
            test_id,
            spec,
            provision_script_deps=provision_script_deps,
        )
    )
    test_receipts = {
        test_id: selected_runner(repo_root, test_id, TEST_SPECS[test_id])
        for test_id in required_ids
    }
    statuses = _patch_statuses(registry, test_receipts)
    updated_registry = copy.deepcopy(registry)
    for patch in updated_registry["patches"]:
        patch["status"] = statuses[patch["id"]]
    updated_ledger, issues = apply_patch_receipts(repo_root, ledger, statuses)
    receipt_document = _receipt_document(updated_registry, test_receipts, statuses)

    if write:
        manifest.write_json(repo_root / RECEIPT_PATH, receipt_document)
        manifest.write_json(repo_root / PATCH_PATH, updated_registry)
        manifest.write_json(repo_root / LEDGER_PATH, updated_ledger)

    passed = sum(receipt["status"] == "passed" for receipt in test_receipts.values())
    failed = len(test_receipts) - passed
    verified_patches = sum(status == "verified" for status in statuses.values())
    adapted = [row for row in updated_ledger["entries"] if row.get("patch_ids")]
    emitted = sum(row.get("output_state") == "emitted" for row in adapted)
    result_ok = failed == 0 and not issues and emitted == len(adapted)
    return ReceiptResult(
        write=write,
        ok=result_ok,
        passed_test_count=passed,
        failed_test_count=failed,
        verified_patch_count=verified_patches,
        pending_patch_count=len(statuses) - verified_patches,
        emitted_adapted_count=emitted,
        pending_adapted_count=len(adapted) - emitted,
        issues=issues,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--write", action="store_true")
    parser.add_argument(
        "--provision-script-deps",
        action="store_true",
        help="install frozen Poteto dependencies only in an automatically removed temporary copy",
    )
    args = parser.parse_args(argv)
    try:
        result = receipt_repository(
            args.repo_root,
            write=args.write,
            provision_script_deps=args.provision_script_deps,
        )
        print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
        return 0 if result.ok else 1
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(
            json.dumps(
                {
                    "ok": False,
                    "error": str(error),
                    "code": getattr(error, "code", "receipt_failure"),
                    "path": getattr(error, "path", None),
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
