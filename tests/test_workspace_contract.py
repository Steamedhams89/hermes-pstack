from __future__ import annotations

import hashlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "upstream" / "pstack"


def _manifest(root: Path) -> dict[str, tuple[int, str, int]]:
    return {
        path.relative_to(root).as_posix(): (
            len(path.read_bytes()),
            hashlib.sha256(path.read_bytes()).hexdigest(),
            path.stat().st_mode & 0o777,
        )
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def test_source_lock_shape() -> None:
    manifest = _manifest(SOURCE)
    assert len(manifest) == 157
    assert sum(item[0] for item in manifest.values()) == 3_091_772
    assert manifest["LICENSE"][1] == "bc957ca6bee02792566a1a028d105e02e247c6e77cf057061674273da77b200e"


def test_three_package_boundaries_exist() -> None:
    for name in ("pstack", "pstack-runtime", "pstack-benny"):
        package = ROOT / "packages" / name
        assert (package / "plugin.yaml").is_file()
        assert (package / "__init__.py").is_file()


def test_workspace_contains_no_symlinks() -> None:
    assert not [path for path in ROOT.rglob("*") if path.is_symlink()]


def test_materialized_artifact_has_no_machine_specific_home_path() -> None:
    markers = (
        ("/" + "home" + "/").encode(),
        ("/" + "Users" + "/").encode(),
        ("C:" + "\\" + "Users" + "\\").encode(),
    )
    offenders = []
    for path in ROOT.rglob("*"):
        if not path.is_file() or SOURCE in path.parents or "__pycache__" in path.parts:
            continue
        if path == Path(__file__).resolve():
            continue
        try:
            data = path.read_bytes()
        except OSError:
            continue
        if any(marker in data for marker in markers):
            offenders.append(path.relative_to(ROOT).as_posix())
    assert offenders == []


def test_pack_file_is_an_unusable_template_until_remote_authorization() -> None:
    template = (ROOT / "hermes-pack.yaml.in").read_text(encoding="utf-8")
    assert "REPLACE_OWNER/REPLACE_REPOSITORY" in template
    assert "REPLACE_WITH_EXACT_40_CHARACTER_COMMIT_SHA" in template
    assert not (ROOT / "hermes-pack.yaml").exists()
