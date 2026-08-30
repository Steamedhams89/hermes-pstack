#!/usr/bin/env python3
"""Materialize receipt-safe copy rows from the pstack parity ledger.

Patch and adapter rows remain pending until their documented translators exist.
The command is a dry run unless --write is supplied.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
import os
from pathlib import Path
import shutil
import stat
import sys
import tempfile

try:
    from . import manifest, verify
except ImportError:  # Direct script execution.
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from tools import manifest, verify


@dataclass(frozen=True)
class MaterializationResult:
    write: bool
    eligible_count: int
    materialized_count: int
    pending_output_count: int
    skipped_patch_count: int

    def to_dict(self) -> dict[str, int | bool]:
        return {
            "write": self.write,
            "eligible_count": self.eligible_count,
            "materialized_count": self.materialized_count,
            "pending_output_count": self.pending_output_count,
            "skipped_patch_count": self.skipped_patch_count,
        }


def _safe_destination(repo_root: Path, target: str) -> Path:
    manifest.reject_symlink_components(repo_root)
    relative = manifest.safe_relative_path(target)
    cursor = repo_root
    for part in relative.parts:
        cursor = cursor / part
        if cursor.is_symlink():
            raise manifest.ProvenanceError(
                "symlink", f"refusing target beneath symlink: {cursor}", target
            )
    return repo_root.joinpath(*relative.parts)


def _atomic_copy(source: Path, destination: Path, mode_text: str) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.is_symlink():
        raise manifest.ProvenanceError(
            "symlink", f"refusing to replace output symlink: {destination}"
        )
    if destination.exists() and not destination.is_file():
        raise manifest.ProvenanceError(
            "non_regular_output", f"output is not a regular file: {destination}"
        )
    if destination.exists():
        expected_hash = manifest.sha256_file(source)
        expected_mode = mode_text
        destination_info = destination.stat(follow_symlinks=False)
        destination_hash = manifest.sha256_file(destination)
        destination_mode = f"0o{stat.S_IMODE(destination_info.st_mode):03o}"
        if destination_hash != expected_hash or destination_mode != expected_mode:
            raise manifest.ProvenanceError(
                "stale_output_hash",
                f"refusing to overwrite unreceipted output: {destination}",
            )
    descriptor, temporary = tempfile.mkstemp(
        prefix=f".{destination.name}.", dir=destination.parent
    )
    try:
        with source.open("rb") as input_handle, os.fdopen(descriptor, "wb") as output_handle:
            shutil.copyfileobj(input_handle, output_handle, length=1024 * 1024)
            output_handle.flush()
            os.fsync(output_handle.fileno())
        os.chmod(temporary, int(mode_text, 8))
        os.replace(temporary, destination)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def materialize_repository(
    repo_root: Path, *, write: bool = False, strict_pin: bool = True
) -> MaterializationResult:
    repo_root = Path(repo_root)
    preflight = verify.verify_repository(repo_root, strict_pin=strict_pin)
    if not preflight.ok:
        raise manifest.ProvenanceError(
            "preflight_failed", json.dumps(preflight.to_dict(), sort_keys=True)
        )

    ledger_path = repo_root / "provenance" / "parity-ledger.json"
    source_root = repo_root / "upstream" / "pstack"
    ledger = manifest.load_json(ledger_path)
    eligible = [
        row
        for row in ledger["entries"]
        if row["output_state"] == "pending"
        and row["disposition"] in {"verbatim_copy_pending", "provenance_copy_pending"}
    ]
    skipped = [
        row
        for row in ledger["entries"]
        if row["output_state"] == "pending" and row not in eligible
    ]
    if not write:
        return MaterializationResult(
            write=False,
            eligible_count=len(eligible),
            materialized_count=0,
            pending_output_count=preflight.pending_output_count,
            skipped_patch_count=len(skipped),
        )

    materialized_count = 0
    for row in eligible:
        source = source_root / manifest.safe_relative_path(row["source_path"])
        destination = _safe_destination(repo_root, row["port_target"])
        _atomic_copy(source, destination, row["mode"])
        info = destination.stat(follow_symlinks=False)
        actual_hash = manifest.sha256_file(destination)
        actual_mode = f"0o{stat.S_IMODE(info.st_mode):03o}"
        if actual_hash != row["source_sha256"] or actual_mode != row["mode"]:
            raise manifest.ProvenanceError(
                "copy_receipt_mismatch", f"copy receipt mismatch: {row['port_target']}"
            )
        row["disposition"] = row["disposition"].removesuffix("_pending")
        row["review_state"] = "materialized_verified"
        row["output_state"] = "emitted"
        row["output_sha256"] = actual_hash
        row["output_mode"] = actual_mode
        materialized_count += 1

    manifest.write_json(ledger_path, ledger)
    postflight = verify.verify_repository(repo_root, strict_pin=strict_pin)
    if not postflight.ok:
        raise manifest.ProvenanceError(
            "postflight_failed", json.dumps(postflight.to_dict(), sort_keys=True)
        )
    return MaterializationResult(
        write=True,
        eligible_count=len(eligible),
        materialized_count=materialized_count,
        pending_output_count=postflight.pending_output_count,
        skipped_patch_count=len(skipped),
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)
    try:
        result = materialize_repository(args.repo_root, write=args.write, strict_pin=True)
        print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
        return 0
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(json.dumps({"ok": False, "error": str(error)}, sort_keys=True))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
