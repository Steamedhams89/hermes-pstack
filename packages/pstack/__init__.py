"""Native, fail-closed registrar for the full pstack content package.

This module deliberately owns registration only.  It has no tools, hooks,
networking, task runner, or external-action surface.  Native Hermes resolves
every registered item as ``pstack:<upstream-name>``.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Any, Iterable, Mapping, Sequence

PLUGIN_NAME = "pstack"
PLUGIN_ROOT = Path(__file__).resolve().parent
SKILLS_ROOT = PLUGIN_ROOT / "skills"
EXPECTED_SKILL_NAMES: tuple[str, ...] = (
    "architect",
    "arena",
    "automate-me",
    "blast-radius",
    "bro",
    "create-verification-skill",
    "figure-it-out",
    "how",
    "interrogate",
    "maintain-verification-skill",
    "make-bot-ui",
    "no-comments",
    "poteto-mode",
    "principle-boundary-discipline",
    "principle-build-the-lever",
    "principle-encode-lessons-in-structure",
    "principle-exhaust-the-design-space",
    "principle-experience-first",
    "principle-fix-root-causes",
    "principle-foundational-thinking",
    "principle-guard-the-context-window",
    "principle-laziness-protocol",
    "principle-make-operations-idempotent",
    "principle-migrate-callers-then-delete-legacy-apis",
    "principle-minimize-reader-load",
    "principle-model-the-domain",
    "principle-never-block-on-the-human",
    "principle-outcome-oriented-execution",
    "principle-prove-it-works",
    "principle-redesign-from-first-principles",
    "principle-separate-before-serializing-shared-state",
    "principle-sequence-verifiable-units",
    "principle-subtract-before-you-add",
    "principle-type-system-discipline",
    "recall",
    "reflect",
    "setup-pstack",
    "show-me-your-work",
    "swarm",
    "tdd",
    "teach",
    "technical-writing",
    "typescript-best-practices",
    "unslop",
    "why",
)
EXPECTED_SUPPORT_COUNTS = {"references": 33, "scripts": 21, "playbooks": 23}
ADAPTER_MARKER = "<!-- pstack-hermes-adapter:v1 -->"
_NAME_RE = re.compile(r"^[A-Za-z0-9_-]+$")
_FRONTMATTER_NAME_RE = re.compile(r"(?m)^name:\s*[\"']?([^\"'\s#]+)")


class PstackPreflightError(RuntimeError):
    """Raised before registration when the complete content tree is invalid."""


@dataclass(frozen=True)
class SkillRecord:
    name: str
    qualified: str
    path: Path
    description: str
    frontmatter: Mapping[str, str]


@dataclass(frozen=True)
class SupportFile:
    kind: str
    path: Path


def _resolved_contained(root: Path, candidate: Path) -> bool:
    try:
        candidate.resolve(strict=True).relative_to(root.resolve(strict=True))
    except (FileNotFoundError, ValueError):
        return False
    return True


def _reject_symlinks_and_escapes(root: Path) -> None:
    if root.is_symlink():
        raise PstackPreflightError(f"symlinked plugin root is not permitted: {root}")
    for candidate in root.rglob("*"):
        if candidate.is_symlink():
            raise PstackPreflightError(f"symlink is not permitted: {candidate}")
        if not _resolved_contained(root, candidate):
            raise PstackPreflightError(f"path escapes plugin root: {candidate}")


def _frontmatter_for(skill_md: Path, expected_name: str) -> Mapping[str, str]:
    text = skill_md.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise PstackPreflightError(f"missing frontmatter: {skill_md}")
    end = text.find("\n---", 4)
    if end < 0:
        raise PstackPreflightError(f"unterminated frontmatter: {skill_md}")
    frontmatter = text[4:end]
    match = _FRONTMATTER_NAME_RE.search(frontmatter)
    if match is None:
        raise PstackPreflightError(f"frontmatter name missing: {skill_md}")
    declared_name = match.group(1)
    # Upstream keeps one human-facing display name ("Poteto Mode") rather
    # than the filesystem identity. The native qualified identity is always
    # the validated directory name; source display text is preserved as data.
    description_match = re.search(r"(?m)^description:\s*[\"']?(.+?)[\"']?\s*$", frontmatter)
    description = description_match.group(1).strip() if description_match else ""
    return {
        "name": expected_name,
        "description": description,
        "source_display_name": declared_name,
    }


def _skill_directories(skills_root: Path) -> Sequence[Path]:
    if not skills_root.is_dir():
        raise PstackPreflightError(f"skills directory missing: {skills_root}")
    children = sorted(skills_root.iterdir(), key=lambda path: path.name)
    if any(not child.is_dir() for child in children):
        unexpected = [child.name for child in children if not child.is_dir()]
        raise PstackPreflightError(f"unexpected non-directory skill entries: {unexpected}")
    names = tuple(child.name for child in children)
    expected = tuple(sorted(EXPECTED_SKILL_NAMES))
    if names != expected:
        missing = sorted(set(expected) - set(names))
        unexpected = sorted(set(names) - set(expected))
        raise PstackPreflightError(
            f"skill tree mismatch; missing={missing or 'none'} unexpected={unexpected or 'none'}"
        )
    return children


def preflight_tree(plugin_root: Path | None = None) -> tuple[SkillRecord, ...]:
    """Validate the complete tree before making a single Hermes registration.

    This guarantees registrar all-or-nothing behavior only: it is not an
    installer transaction claim.
    """
    requested_root = plugin_root or PLUGIN_ROOT
    if requested_root.is_symlink():
        raise PstackPreflightError(f"symlinked plugin root is not permitted: {requested_root}")
    root = requested_root.resolve()
    if not root.is_dir():
        raise PstackPreflightError(f"plugin root missing: {root}")
    _reject_symlinks_and_escapes(root)
    records: list[SkillRecord] = []
    qualified_names: set[str] = set()
    for skill_dir in _skill_directories(root / "skills"):
        name = skill_dir.name
        if not _NAME_RE.fullmatch(name):
            raise PstackPreflightError(f"invalid skill name: {name!r}")
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.is_file() or skill_md.is_symlink():
            raise PstackPreflightError(f"SKILL.md missing or invalid: {skill_md}")
        if not _resolved_contained(root, skill_md):
            raise PstackPreflightError(f"SKILL.md escapes plugin root: {skill_md}")
        metadata = _frontmatter_for(skill_md, name)
        qualified = f"{PLUGIN_NAME}:{name}"
        if qualified in qualified_names:
            raise PstackPreflightError(f"duplicate qualified identity: {qualified}")
        qualified_names.add(qualified)
        records.append(
            SkillRecord(
                name=name,
                qualified=qualified,
                path=skill_md,
                description=str(metadata["description"]),
                frontmatter=metadata,
            )
        )
    if len(records) != 45 or {record.name for record in records} != set(EXPECTED_SKILL_NAMES):
        raise PstackPreflightError("expected skill set is incomplete")
    supports = iter_support_files(root)
    actual_counts = {
        kind: sum(1 for support in supports if support.kind == kind)
        for kind in EXPECTED_SUPPORT_COUNTS
    }
    if actual_counts != EXPECTED_SUPPORT_COUNTS:
        raise PstackPreflightError(
            f"support tree mismatch; expected={EXPECTED_SUPPORT_COUNTS} actual={actual_counts}"
        )
    return tuple(records)


def iter_support_files(plugin_root: Path | None = None) -> tuple[SupportFile, ...]:
    """Return all declared skill-local references, scripts, and playbooks."""
    requested_root = plugin_root or PLUGIN_ROOT
    if requested_root.is_symlink():
        raise PstackPreflightError(f"symlinked plugin root is not permitted: {requested_root}")
    root = requested_root.resolve()
    supports: list[SupportFile] = []
    for file_path in sorted((root / "skills").rglob("*")):
        if not file_path.is_file() or file_path.name == "SKILL.md":
            continue
        relative = file_path.relative_to(root / "skills")
        parts = relative.parts
        kind = ""
        if "references" in parts:
            kind = "references"
        elif "scripts" in parts:
            kind = "scripts"
        elif "playbooks" in parts:
            kind = "playbooks"
        if kind:
            if file_path.is_symlink() or not _resolved_contained(root, file_path):
                raise PstackPreflightError(f"invalid support path: {file_path}")
            supports.append(SupportFile(kind=kind, path=file_path))
    return tuple(supports)


def flat_skill_index_entries(flat_skills_root: Path) -> tuple[str, ...]:
    """Expose the flat-index delta for tests: plugin registrations add none."""
    if not flat_skills_root.exists():
        return ()
    return tuple(
        sorted(path.name for path in flat_skills_root.iterdir() if path.is_dir())
    )


def register(ctx: Any) -> None:
    """Register all verified skills only after the full-tree preflight passes."""
    namespace = getattr(ctx.manifest, "skill_namespace", "") or ctx.manifest.name
    if namespace != PLUGIN_NAME:
        raise PstackPreflightError(
            f"pstack registrar requires namespace {PLUGIN_NAME!r}, got {namespace!r}"
        )
    records = preflight_tree()
    existing = [
        record.qualified
        for record in records
        if ctx._manager.find_plugin_skill(record.qualified) is not None
    ]
    if existing:
        raise PstackPreflightError(f"qualified identities already registered: {existing}")
    for record in records:
        ctx.register_skill(
            record.name,
            record.path,
            record.description,
            frontmatter=record.frontmatter,
        )
