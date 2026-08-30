from __future__ import annotations

import copy
import json
import os
from pathlib import Path
import shutil
import tempfile
import unittest

from tools import manifest, materialize, verify


REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURES = REPO_ROOT / "tests" / "fixtures" / "parity"


def issue_codes(report: verify.VerificationReport) -> set[str]:
    return {issue.code for issue in report.issues}


class FixtureRepository:
    def __init__(self, root: Path):
        self.root = root
        self.source = root / "upstream" / "pstack"
        self.ledger_path = root / "provenance" / "parity-ledger.json"
        self.patch_index = root / "provenance" / "patches" / "index.json"

        self.source.parent.mkdir(parents=True)
        shutil.copytree(FIXTURES / "mini-source", self.source)
        self.patch_index.parent.mkdir(parents=True)
        manifest.write_json(self.patch_index, manifest.default_patch_registry())
        manifest.write_json(
            root / "provenance" / "UPSTREAM.lock.json",
            manifest.build_upstream_lock(
                self.source,
                commit="fixture-commit",
                strict_pin=False,
            ),
        )
        ledger = manifest.build_parity_ledger(
            self.source,
            commit="fixture-commit",
            strict_pin=False,
        )
        manifest.write_json(self.ledger_path, ledger)

    def load_ledger(self) -> dict:
        return manifest.load_json(self.ledger_path)

    def write_ledger(self, ledger: dict) -> None:
        manifest.write_json(self.ledger_path, ledger)

    def verify(self) -> verify.VerificationReport:
        return verify.verify_repository(self.root, strict_pin=False)


class ParityNegativeFixtureTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.fixture = FixtureRepository(Path(self.temp.name))

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_fixture_catalog_names_every_required_negative(self) -> None:
        catalog = json.loads((FIXTURES / "negative_cases.json").read_text())
        self.assertEqual(
            {case["id"] for case in catalog["cases"]},
            {
                "missing-source-row",
                "null-target",
                "null-disposition",
                "duplicate-target",
                "source-hash-drift",
                "symlink",
                "mode-drift",
                "stale-output-hash",
                "folded-component",
                "mistaken-23rd-poteto-route",
            },
        )

    def test_valid_pending_ledger_is_accepted_and_reported_pending(self) -> None:
        report = self.fixture.verify()
        self.assertTrue(report.ok, report.to_dict())
        self.assertEqual(report.pending_output_count, 6)

    def test_missing_source_row_fails(self) -> None:
        ledger = self.fixture.load_ledger()
        ledger["entries"].pop()
        ledger["entry_count"] -= 1
        self.fixture.write_ledger(ledger)
        self.assertIn("missing_source_row", issue_codes(self.fixture.verify()))

    def test_null_target_and_disposition_fail(self) -> None:
        for field, code in (
            ("port_target", "null_port_target"),
            ("disposition", "null_disposition"),
        ):
            with self.subTest(field=field):
                ledger = self.fixture.load_ledger()
                ledger["entries"][0][field] = None
                self.fixture.write_ledger(ledger)
                self.assertIn(code, issue_codes(self.fixture.verify()))
                self.fixture.write_ledger(
                    manifest.build_parity_ledger(
                        self.fixture.source,
                        commit="fixture-commit",
                        strict_pin=False,
                    )
                )

    def test_duplicate_target_fails(self) -> None:
        ledger = self.fixture.load_ledger()
        ledger["entries"][1]["port_target"] = ledger["entries"][0]["port_target"]
        self.fixture.write_ledger(ledger)
        self.assertIn("duplicate_target", issue_codes(self.fixture.verify()))

    def test_source_hash_drift_fails(self) -> None:
        skill = self.fixture.source / "skills" / "alpha" / "SKILL.md"
        skill.write_text(skill.read_text() + "\ndrift\n", encoding="utf-8")
        self.assertIn("source_hash_drift", issue_codes(self.fixture.verify()))

    def test_source_symlink_fails(self) -> None:
        link = self.fixture.source / "skills" / "rogue-link"
        link.symlink_to(self.fixture.source / "skills" / "alpha", target_is_directory=True)
        self.assertIn("symlink", issue_codes(self.fixture.verify()))

    def test_source_mode_drift_fails(self) -> None:
        skill = self.fixture.source / "skills" / "alpha" / "SKILL.md"
        skill.chmod(0o755)
        self.assertIn("source_mode_drift", issue_codes(self.fixture.verify()))

    def test_stale_output_hash_on_pending_row_fails(self) -> None:
        ledger = self.fixture.load_ledger()
        ledger["entries"][0]["output_sha256"] = "0" * 64
        self.fixture.write_ledger(ledger)
        self.assertIn("stale_output_hash", issue_codes(self.fixture.verify()))

    def test_folded_component_target_fails(self) -> None:
        ledger = self.fixture.load_ledger()
        row = next(e for e in ledger["entries"] if e["component"] == "principle-one")
        row["port_target"] = "packages/pstack/skills/alpha/principle-one.md"
        self.fixture.write_ledger(ledger)
        self.assertIn("folded_component", issue_codes(self.fixture.verify()))

    def test_opening_a_pr_as_route_fails(self) -> None:
        ledger = self.fixture.load_ledger()
        ledger["poteto_contract"]["routed_playbooks"].append("opening-a-pr.md")
        self.fixture.write_ledger(ledger)
        self.assertIn("mistaken_poteto_route", issue_codes(self.fixture.verify()))

    def test_undocumented_patch_fails(self) -> None:
        ledger = self.fixture.load_ledger()
        row = next(e for e in ledger["entries"] if e["kind"] == "workflow_skill")
        row["disposition"] = "mechanical_patch_pending"
        row["patch_ids"] = ["PATCH-NOT-DOCUMENTED"]
        self.fixture.write_ledger(ledger)
        self.assertIn("undocumented_patch", issue_codes(self.fixture.verify()))

    def test_unclassified_extra_source_fails(self) -> None:
        (self.fixture.source / "mystery.bin").write_bytes(b"unknown")
        codes = issue_codes(self.fixture.verify())
        self.assertIn("missing_source_row", codes)
        self.assertIn("unclassified_source", codes)

    def test_manifest_refuses_unclassified_source(self) -> None:
        (self.fixture.source / "mystery.bin").write_bytes(b"unknown")
        with self.assertRaises(manifest.ProvenanceError) as caught:
            manifest.build_parity_ledger(
                self.fixture.source,
                commit="fixture-commit",
                strict_pin=False,
            )
        self.assertEqual(caught.exception.code, "unclassified_source")

    def test_extra_source_row_fails(self) -> None:
        ledger = self.fixture.load_ledger()
        extra = copy.deepcopy(ledger["entries"][0])
        extra["source_path"] = "README-NOT-THERE.md"
        extra["port_target"] = "provenance/upstream-root/README-NOT-THERE.md"
        ledger["entries"].append(extra)
        ledger["entry_count"] += 1
        self.fixture.write_ledger(ledger)
        self.assertIn("extra_source_row", issue_codes(self.fixture.verify()))

    def test_target_path_traversal_fails(self) -> None:
        ledger = self.fixture.load_ledger()
        ledger["entries"][0]["port_target"] = "../escape"
        self.fixture.write_ledger(ledger)
        self.assertIn("unsafe_path", issue_codes(self.fixture.verify()))

    def test_target_parent_symlink_fails(self) -> None:
        target_parent = self.fixture.root / "packages"
        target_parent.symlink_to(self.fixture.root / "elsewhere", target_is_directory=True)
        self.assertIn("symlink", issue_codes(self.fixture.verify()))


class ParityMaterializationTests(unittest.TestCase):
    def make_fixture(self, root: Path) -> FixtureRepository:
        return FixtureRepository(root)

    def test_materializes_copies_and_updates_receipts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fixture = self.make_fixture(Path(tmp))
            result = materialize.materialize_repository(
                fixture.root, write=True, strict_pin=False
            )
            self.assertEqual(result.materialized_count, 6)
            self.assertEqual(result.pending_output_count, 0)
            report = fixture.verify()
            self.assertTrue(report.ok, report.to_dict())

            ledger = fixture.load_ledger()
            self.assertTrue(all(row["output_sha256"] for row in ledger["entries"]))
            self.assertTrue(all(row["output_state"] == "emitted" for row in ledger["entries"]))

    def test_materialization_is_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as left_tmp, tempfile.TemporaryDirectory() as right_tmp:
            left = self.make_fixture(Path(left_tmp))
            right = self.make_fixture(Path(right_tmp))
            materialize.materialize_repository(left.root, write=True, strict_pin=False)
            materialize.materialize_repository(right.root, write=True, strict_pin=False)
            self.assertEqual(left.ledger_path.read_bytes(), right.ledger_path.read_bytes())
            left_receipts = [e["output_sha256"] for e in left.load_ledger()["entries"]]
            right_receipts = [e["output_sha256"] for e in right.load_ledger()["entries"]]
            self.assertEqual(left_receipts, right_receipts)

    def test_output_hash_and_mode_drift_fail_after_materialization(self) -> None:
        for mutation, code in (("hash", "stale_output_hash"), ("mode", "output_mode_drift")):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as tmp:
                fixture = self.make_fixture(Path(tmp))
                materialize.materialize_repository(
                    fixture.root, write=True, strict_pin=False
                )
                row = next(e for e in fixture.load_ledger()["entries"] if e["kind"] == "workflow_skill")
                target = fixture.root / row["port_target"]
                if mutation == "hash":
                    target.write_text(target.read_text() + "\nstale\n", encoding="utf-8")
                else:
                    target.chmod(0o755 if row["mode"] != "0o755" else 0o644)
                self.assertIn(code, issue_codes(fixture.verify()))

    def test_missing_emitted_output_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fixture = self.make_fixture(Path(tmp))
            materialize.materialize_repository(fixture.root, write=True, strict_pin=False)
            row = fixture.load_ledger()["entries"][0]
            (fixture.root / row["port_target"]).unlink()
            self.assertIn("missing_output", issue_codes(fixture.verify()))

    def test_emitted_adapted_output_with_pending_patch_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fixture = self.make_fixture(Path(tmp))
            materialize.materialize_repository(fixture.root, write=True, strict_pin=False)
            ledger = fixture.load_ledger()
            row = next(
                entry for entry in ledger["entries"] if entry["kind"] == "workflow_skill"
            )
            row["disposition"] = "mechanical_patch"
            row["patch_ids"] = ["PATCH-HERMES-SKILL-PRIMITIVES"]
            fixture.write_ledger(ledger)
            self.assertIn("unverified_patch_output", issue_codes(fixture.verify()))


if __name__ == "__main__":
    unittest.main()
