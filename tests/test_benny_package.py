from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "packages" / "pstack-benny"
UPSTREAM = ROOT / "upstream" / "pstack" / "automations" / "benny"


def _files(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def test_benny_resources_are_complete_and_byte_identical() -> None:
    packaged = _files(PLUGIN / "resources" / "benny")
    upstream = _files(UPSTREAM)
    assert packaged == upstream
    assert len(packaged) == 12
    assert sum(path.endswith("/SKILL.md") for path in packaged) == 3


def test_benny_package_contains_no_symlinks() -> None:
    assert not [path for path in PLUGIN.rglob("*") if path.is_symlink()]


def test_register_only_preflights_dormant_resources() -> None:
    spec = importlib.util.spec_from_file_location("pstack_benny", PLUGIN / "__init__.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    class RefusingContext:
        def __getattr__(self, name: str):
            raise AssertionError(f"dormant Benny package must not use ctx.{name}")

    module.register(RefusingContext())
