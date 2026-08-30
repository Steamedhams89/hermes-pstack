from __future__ import annotations

from pathlib import Path

_EXPECTED = {
    "FOR_AGENTS.md",
    "README.md",
    "skills/reproduce-and-fix-issues/SKILL.md",
    "skills/reproduce-and-fix-issues/references/control-adapter.md",
    "skills/reproduce-and-fix-issues/references/feature-map.example.md",
    "skills/reproduce-and-fix-issues/references/verify-existing-fix.md",
    "skills/setup-benny/SKILL.md",
    "skills/triage-issue-reports/SKILL.md",
    "skills/triage-issue-reports/references/routing.example.md",
    "templates/configuration.example.yaml",
    "templates/reproduce-automation-prompt.md",
    "templates/triage-automation-prompt.md",
}


def _preflight() -> None:
    root = Path(__file__).resolve().parent / "resources" / "benny"
    if not root.is_dir():
        raise RuntimeError("pstack-benny resources are missing")
    symlinks = sorted(path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_symlink())
    if symlinks:
        raise RuntimeError(f"pstack-benny refuses symlinks: {symlinks}")
    actual = {path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file()}
    missing = sorted(_EXPECTED - actual)
    extra = sorted(actual - _EXPECTED)
    if missing or extra:
        raise RuntimeError(f"pstack-benny source completeness failure: missing={missing}, extra={extra}")


def register(ctx) -> None:
    _preflight()
    # Procedures remain inert resources until separately approved event adapters exist.
