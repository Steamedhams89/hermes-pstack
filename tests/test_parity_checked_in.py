from __future__ import annotations

import ast
import json
from pathlib import Path
import re
import subprocess
import sys
import unittest

from tools import manifest, verify


REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = REPO_ROOT / "upstream" / "pstack"
LEDGER_PATH = REPO_ROOT / "provenance" / "parity-ledger.json"
LOCK_PATH = REPO_ROOT / "provenance" / "UPSTREAM.lock.json"


class CheckedInParityTests(unittest.TestCase):
    def test_checked_in_ledger_matches_pinned_source(self) -> None:
        report = verify.verify_repository(REPO_ROOT, strict_pin=True)
        self.assertTrue(report.ok, report.to_dict())
        self.assertEqual(report.source_file_count, 157)
        self.assertEqual(report.pending_output_count + report.emitted_output_count, 157)
        ledger = manifest.load_json(LEDGER_PATH)
        pending_patch_ids = {
            patch_id
            for row in ledger["entries"]
            if row["output_state"] == "pending"
            for patch_id in row["patch_ids"]
        }
        self.assertTrue(pending_patch_ids <= {"PATCH-HERMES-SCRIPT-PATHS"})

    def test_manifest_rebuild_matches_source_identity_and_pending_shape(self) -> None:
        rebuilt = manifest.build_parity_ledger(SOURCE_ROOT, strict_pin=True)
        checked = manifest.load_json(LEDGER_PATH)
        self.assertEqual(
            {key: value for key, value in checked.items() if key != "entries"},
            {key: value for key, value in rebuilt.items() if key != "entries"},
        )
        rebuilt_by_path = {row["source_path"]: row for row in rebuilt["entries"]}
        self.assertEqual(set(rebuilt_by_path), {row["source_path"] for row in checked["entries"]})
        for row in checked["entries"]:
            expected = rebuilt_by_path[row["source_path"]]
            normalized = dict(row)
            disposition = normalized["disposition"]
            if not disposition.endswith("_pending"):
                normalized["disposition"] = f"{disposition}_pending"
            normalized["review_state"] = "mapped_pending_output"
            normalized["output_state"] = "pending"
            normalized["output_sha256"] = None
            normalized["output_mode"] = None
            self.assertEqual(normalized, expected)

    def test_lock_contains_exact_pin_and_mit_identity(self) -> None:
        lock = manifest.load_json(LOCK_PATH)
        upstream = lock["upstream"]
        self.assertEqual(upstream["commit"], manifest.PINNED_COMMIT)
        self.assertEqual(upstream["version"], "0.14.5")
        self.assertEqual(upstream["file_count"], 157)
        self.assertEqual(upstream["total_bytes"], 3_091_772)
        self.assertEqual(upstream["tree_sha256"], manifest.PINNED_TREE_SHA256)
        self.assertEqual(upstream["license"]["spdx"], "MIT")
        self.assertEqual(upstream["author"], "Lauren Tan")

    def test_exact_component_counts_and_test_declarations(self) -> None:
        ledger = manifest.load_json(LEDGER_PATH)
        counts = ledger["expected_counts"]
        self.assertEqual(counts["registered_skills"], 45)
        self.assertEqual(counts["workflow_skills"], 24)
        self.assertEqual(counts["principle_skills"], 21)
        self.assertEqual(counts["benny_skills"], 3)
        self.assertEqual(counts["agent_prompts"], 2)
        self.assertEqual(counts["playbook_files"], 23)
        self.assertEqual(counts["routed_playbooks"], 22)
        self.assertEqual(counts["shared_postludes"], 1)
        self.assertEqual(counts["reference_files"], 37)
        self.assertEqual(counts["script_tree_files"], 21)
        self.assertEqual(counts["executable_test_suites"], 4)
        self.assertEqual(counts["declared_tests"], 52)
        self.assertEqual(counts["guide_documents"], 11)
        self.assertEqual(counts["guide_images"], 6)

    def test_poteto_contract_is_22_routes_plus_postlude(self) -> None:
        ledger = manifest.load_json(LEDGER_PATH)
        fixture = json.loads(
            (REPO_ROOT / "tests" / "fixtures" / "parity" / "poteto_contract.json").read_text()
        )
        self.assertEqual(ledger["poteto_contract"], fixture)
        self.assertNotIn("opening-a-pr.md", ledger["poteto_contract"]["routed_playbooks"])

    def test_all_77_skill_support_files_are_individually_mapped(self) -> None:
        ledger = manifest.load_json(LEDGER_PATH)
        support_kinds = {
            "skill_reference",
            "playbook_resource",
            "runtime_script",
            "script_build_metadata",
            "script_test",
            "script_test_support",
        }
        support = [row for row in ledger["entries"] if row["kind"] in support_kinds]
        self.assertEqual(len(support), 77)
        self.assertEqual(len({row["port_target"] for row in support}), 77)

    def test_notice_is_unofficial_and_source_pinned(self) -> None:
        notice = (REPO_ROOT / "provenance" / "NOTICE.md").read_text(encoding="utf-8")
        self.assertIn("Lauren Tan", notice)
        self.assertIn("MIT", notice)
        self.assertIn(manifest.PINNED_COMMIT, notice)
        self.assertIn("unofficial", notice.lower())
        self.assertIn("not endorsed", notice.lower())

    def test_patch_registry_matches_canonical_structure_and_receipt_statuses(self) -> None:
        patch_path = REPO_ROOT / "provenance" / "patches" / "index.json"
        actual = manifest.load_json(patch_path)
        expected = manifest.default_patch_registry()
        actual_without_status = {
            **actual,
            "patches": [
                {key: value for key, value in patch.items() if key != "status"}
                for patch in actual["patches"]
            ],
        }
        expected_without_status = {
            **expected,
            "patches": [
                {key: value for key, value in patch.items() if key != "status"}
                for patch in expected["patches"]
            ],
        }
        self.assertEqual(actual_without_status, expected_without_status)
        for patch in actual["patches"]:
            self.assertIn(patch["status"], {"pending", "verified"})
            if patch["status"] == "pending":
                self.assertEqual(patch["id"], "PATCH-HERMES-SCRIPT-PATHS")

    def test_tools_are_stdlib_only_and_have_no_network_imports(self) -> None:
        network_forbidden = {"http", "requests", "socket", "urllib"}
        for tool_name in ("manifest.py", "materialize.py", "receipt.py", "verify.py"):
            with self.subTest(tool=tool_name):
                tree = ast.parse((REPO_ROOT / "tools" / tool_name).read_text())
                imports = {
                    alias.name.split(".")[0]
                    for node in ast.walk(tree)
                    if isinstance(node, ast.Import)
                    for alias in node.names
                }
                imports.update(
                    node.module.split(".")[0]
                    for node in ast.walk(tree)
                    if isinstance(node, ast.ImportFrom)
                    and node.level == 0
                    and node.module
                )
                allowed = set(sys.stdlib_module_names) | {"__future__", "tools"}
                self.assertTrue(imports <= allowed, imports)
                self.assertFalse(imports & network_forbidden, imports & network_forbidden)
                if tool_name != "receipt.py":
                    self.assertNotIn("subprocess", imports)

    def test_verify_cli_passes_without_writing(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                str(REPO_ROOT / "tools" / "verify.py"),
                "--repo-root",
                str(REPO_ROOT),
                "--strict-pin",
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_release_gate_matches_current_receipt_completeness(self) -> None:
        ordinary = verify.verify_repository(REPO_ROOT, strict_pin=True)
        gate = verify.verify_repository(
            REPO_ROOT, strict_pin=True, require_complete=True
        )
        self.assertEqual(gate.ok, ordinary.pending_output_count == 0)
        if ordinary.pending_output_count:
            self.assertIn("pending_output", {issue.code for issue in gate.issues})
        else:
            self.assertTrue(gate.ok, gate.to_dict())


if __name__ == "__main__":
    unittest.main()
