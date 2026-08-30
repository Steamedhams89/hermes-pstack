from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from tools import manifest, receipt, verify


REPO_ROOT = Path(__file__).resolve().parents[1]


def _registry(required_tests: list[str]) -> dict:
    return {
        "schema_version": 1,
        "description": "fixture",
        "patches": [
            {
                "id": "PATCH-FIXTURE",
                "status": "pending",
                "class": "mechanical",
                "purpose": "fixture",
                "required_tests": required_tests,
            }
        ],
    }


def _ledger(target: str) -> dict:
    return {
        "entries": [
            {
                "source_path": "skills/example/SKILL.md",
                "port_target": target,
                "mode": "0o644",
                "patch_ids": ["PATCH-FIXTURE"],
                "disposition": "mechanical_patch_pending",
                "review_state": "mapped_pending_output",
                "output_state": "pending",
                "output_sha256": None,
                "output_mode": None,
            }
        ]
    }


def _test_receipt(status: str) -> dict:
    exit_code = 0 if status == "passed" else 1
    return {
        "status": status,
        "commands": [
            {
                "argv": ["python", "-m", "pytest", "fixture"],
                "cwd": ".",
                "exit_code": exit_code,
                "output_sha256": "0" * 64,
            }
        ],
        "inputs": {"tests/fixture.py": "1" * 64},
    }


def _receipt_document(test_receipt: dict, *, patch_status: str = "verified") -> dict:
    return {
        "schema_version": 1,
        "tests": {"authority-gate": test_receipt},
        "patch_verification": {
            "PATCH-FIXTURE": {
                "required_tests": ["authority-gate"],
                "status": patch_status,
            }
        },
    }


def test_test_spec_registry_covers_every_declared_gate_without_install_commands():
    registry = manifest.default_patch_registry()
    declared = {
        test_id
        for patch in registry["patches"]
        for test_id in patch["required_tests"]
    }
    assert set(receipt.TEST_SPECS) == declared
    for spec in receipt.TEST_SPECS.values():
        for command in spec.commands:
            joined = " ".join(command.argv).lower()
            assert " install" not in joined
            assert "curl " not in joined
            assert "wget " not in joined


def test_script_dependency_provisioning_is_explicit_ephemeral_and_clean(monkeypatch, tmp_path):
    script_root = tmp_path / receipt.SCRIPT_ROOT
    script_root.mkdir(parents=True)
    (script_root / "package.json").write_text("{}\n", encoding="utf-8")
    (script_root / "bun.lock").write_text("lockfileVersion = 1\n", encoding="utf-8")
    (script_root / "source.ts").write_text("export {};\n", encoding="utf-8")
    (tmp_path / "tools").mkdir()
    (tmp_path / "tools" / "receipt.py").write_text("fixture\n", encoding="utf-8")
    calls: list[tuple[tuple[str, ...], Path | None, str | None]] = []

    def fake_execute(repo_root, command, environment, hermes_home, *, cwd_override=None, display_cwd=None):
        calls.append((command.argv, cwd_override, display_cwd))
        return {
            "argv": list(command.argv),
            "cwd": display_cwd or command.cwd,
            "exit_code": 0,
            "output_sha256": "0" * 64,
        }

    monkeypatch.setattr(receipt, "_execute_command", fake_execute)
    spec = receipt.TEST_SPECS["upstream-script-suite"]

    direct = receipt.run_test_spec(tmp_path, "upstream-script-suite", spec)
    assert direct["status"] == "passed"
    assert [argv for argv, _, _ in calls] == [command.argv for command in spec.commands]
    assert all(cwd is None for _, cwd, _ in calls)

    calls.clear()
    provisioned = receipt.run_test_spec(
        tmp_path,
        "upstream-script-suite",
        spec,
        provision_script_deps=True,
    )
    assert provisioned["status"] == "passed"
    assert calls[0][0] == ("bun", "install", "--frozen-lockfile")
    assert [argv for argv, _, _ in calls[1:]] == [command.argv for command in spec.commands]
    assert all(cwd is not None and not cwd.is_relative_to(tmp_path) for _, cwd, _ in calls)
    assert all(display == f"ephemeral:{receipt.SCRIPT_ROOT.as_posix()}" for _, _, display in calls)
    assert not (script_root / "node_modules").exists()


def test_unknown_required_test_id_fails_closed():
    registry = _registry(["not-a-real-gate"])
    with pytest.raises(receipt.ReceiptError, match="unknown required test id") as caught:
        receipt._required_test_ids(registry)
    assert caught.value.code == "unknown_test_id"


def test_partial_or_failed_patch_leaves_adapted_row_pending(tmp_path):
    target = tmp_path / "packages" / "pstack" / "skills" / "example" / "SKILL.md"
    target.parent.mkdir(parents=True)
    target.write_text("adapted\n", encoding="utf-8")
    target.chmod(0o644)
    registry = _registry(["authority-gate", "portable-path-scan"])
    tests = {
        "authority-gate": _test_receipt("passed"),
        "portable-path-scan": _test_receipt("failed"),
    }
    statuses = receipt._patch_statuses(registry, tests)
    updated, issues = receipt.apply_patch_receipts(
        tmp_path, _ledger(target.relative_to(tmp_path).as_posix()), statuses
    )
    row = updated["entries"][0]
    assert statuses == {"PATCH-FIXTURE": "pending"}
    assert issues == ()
    assert row["output_state"] == "pending"
    assert row["output_sha256"] is None
    assert row["disposition"] == "mechanical_patch_pending"


def test_verified_patch_emits_hash_mode_and_review_receipt(tmp_path):
    target = tmp_path / "packages" / "pstack" / "skills" / "example" / "SKILL.md"
    target.parent.mkdir(parents=True)
    target.write_text("adapted\n", encoding="utf-8")
    target.chmod(0o644)
    registry = _registry(["authority-gate"])
    statuses = receipt._patch_statuses(
        registry, {"authority-gate": _test_receipt("passed")}
    )
    updated, issues = receipt.apply_patch_receipts(
        tmp_path, _ledger(target.relative_to(tmp_path).as_posix()), statuses
    )
    row = updated["entries"][0]
    assert issues == ()
    assert row["output_state"] == "emitted"
    assert row["review_state"] == "adapted_verified"
    assert row["disposition"] == "mechanical_patch"
    assert row["output_mode"] == "0o644"
    assert row["output_sha256"] == hashlib.sha256(target.read_bytes()).hexdigest()

    target.write_text("drifted\n", encoding="utf-8")
    assert manifest.sha256_file(target) != row["output_sha256"]


def test_symlinked_target_is_refused_and_left_pending(tmp_path):
    outside = tmp_path / "outside.md"
    outside.write_text("outside\n", encoding="utf-8")
    link = tmp_path / "packages" / "pstack" / "skills" / "example" / "SKILL.md"
    link.parent.mkdir(parents=True)
    link.symlink_to(outside)
    updated, issues = receipt.apply_patch_receipts(
        tmp_path,
        _ledger(link.relative_to(tmp_path).as_posix()),
        {"PATCH-FIXTURE": "verified"},
    )
    assert updated["entries"][0]["output_state"] == "pending"
    assert {issue["code"] for issue in issues} == {"symlink"}


def test_wrong_target_mode_is_not_receipted(tmp_path):
    target = tmp_path / "output.md"
    target.write_text("adapted\n", encoding="utf-8")
    target.chmod(0o755)
    updated, issues = receipt.apply_patch_receipts(
        tmp_path,
        _ledger("output.md"),
        {"PATCH-FIXTURE": "verified"},
    )
    assert updated["entries"][0]["output_state"] == "pending"
    assert {issue["code"] for issue in issues} == {"output_mode_drift"}


def test_real_repository_receipt_dry_run_does_not_mutate_provenance():
    paths = [
        REPO_ROOT / receipt.LEDGER_PATH,
        REPO_ROOT / receipt.PATCH_PATH,
        REPO_ROOT / receipt.RECEIPT_PATH,
    ]
    before = {path: path.read_bytes() if path.exists() else None for path in paths}

    def passing_runner(repo_root: Path, test_id: str, spec: receipt.TestSpec) -> dict:
        return _test_receipt("passed")

    result = receipt.receipt_repository(REPO_ROOT, write=False, runner=passing_runner)
    after = {path: path.read_bytes() if path.exists() else None for path in paths}
    assert result.write is False
    assert result.failed_test_count == 0
    assert result.pending_adapted_count == 0
    assert before == after


def test_verifier_requires_receipts_for_verified_patches(tmp_path):
    report = verify.VerificationReport()
    patches = {
        "PATCH-FIXTURE": {
            "status": "verified",
            "required_tests": ["authority-gate"],
        }
    }
    verify._verify_test_receipts(tmp_path, patches, None, report)
    assert {issue.code for issue in report.issues} == {"missing_test_receipts"}


def test_verifier_rejects_stale_receipt_inputs(tmp_path):
    test_input = tmp_path / "tests" / "fixture.py"
    test_input.parent.mkdir(parents=True)
    test_input.write_text("before\n", encoding="utf-8")
    test_receipt = _test_receipt("passed")
    test_receipt["inputs"] = {
        "tests/fixture.py": manifest.sha256_file(test_input),
    }
    receipts = _receipt_document(test_receipt)
    test_input.write_text("after\n", encoding="utf-8")

    report = verify.VerificationReport()
    patches = {
        "PATCH-FIXTURE": {
            "status": "verified",
            "required_tests": ["authority-gate"],
        }
    }
    verify._verify_test_receipts(tmp_path, patches, receipts, report)
    assert "stale_test_input" in {issue.code for issue in report.issues}


def test_verifier_rejects_patch_registry_receipt_drift(tmp_path):
    test_input = tmp_path / "tests" / "fixture.py"
    test_input.parent.mkdir(parents=True)
    test_input.write_text("fixture\n", encoding="utf-8")
    test_receipt = _test_receipt("passed")
    test_receipt["inputs"] = {
        "tests/fixture.py": manifest.sha256_file(test_input),
    }
    receipts = _receipt_document(test_receipt)

    report = verify.VerificationReport()
    patches = {
        "PATCH-FIXTURE": {
            "status": "pending",
            "required_tests": ["authority-gate"],
        }
    }
    verify._verify_test_receipts(tmp_path, patches, receipts, report)
    assert "patch_status_drift" in {issue.code for issue in report.issues}
