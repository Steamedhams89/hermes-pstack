from __future__ import annotations

import hashlib
import os
from pathlib import Path
import re
import stat
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCE = REPO_ROOT / "upstream" / "pstack" / "docs" / "guide"
GUIDE = REPO_ROOT / "docs" / "upstream-guide"

MARKDOWN_FILES = {
    "README.md",
    "01-setup.md",
    "02-poteto-mode.md",
    "03-understand.md",
    "04-design.md",
    "05-build-and-clean.md",
    "06-verify-and-ship.md",
    "07-overnight.md",
    "08-principles.md",
    "09-make-it-yours.md",
    "10-recipes-and-pitfalls.md",
}

IMAGE_RECEIPTS = {
    "images/design.jpg": "b8ed07427f6a0c37dd8ba97961fc0eb5071efeee6c4a230648bdb7547f6f2a8f",
    "images/overnight.jpg": "4b4405e4df8925c5b3abbe702f681af0f3b1f5f32271b599f95717f578f1a0c8",
    "images/recipes.jpg": "9fa2d51b476635712737795ddef81806efaa0086bb3bfa9f9f45695d9ab0f8e8",
    "images/router.jpg": "525843055a4efd2b10acc50a8652fd02b0834ea733a8a2f895c1eb89036017da",
    "images/understanding.jpg": "b60587e9a9bbe2550e93be9819cf0cd4acf77d90fac769a0c43d82bd8e34e279",
    "images/verification.jpg": "2a76b52007a1cd2866ba67fd47d7d9ef3e1118bb5a09c4665eee8c3f161bd09a",
}

WORKFLOW_SKILLS = {
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
}

PRINCIPLE_SKILLS = {
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
}

ROUTED_PLAYBOOKS = {
    "authoring-a-skill",
    "autonomous-run",
    "autopilot-full",
    "autopilot-stack",
    "babysit",
    "bug-fix",
    "eval",
    "feature",
    "hillclimb",
    "investigation",
    "multi-phase-plan",
    "orchestrate",
    "pause-safely",
    "perf-issue",
    "prototype",
    "refactoring",
    "runtime-forensics",
    "session-pickup",
    "shipping",
    "trace-forensics",
    "visual-parity",
    "worktree-cleanup",
}

PROVENANCE_CURSOR_LINE = (
    "Upstream context: pstack 0.14.5 was originally authored for Cursor. "
    "This guide describes the complete Hermes-native port."
)

FORBIDDEN_HOST_MECHANICS = {
    "cursor-path": re.compile(r"\.cursor(?:/|\\|\b)", re.IGNORECASE),
    "cursor-command": re.compile(r"/(?:add-plugin|deslop|loop)\b", re.IGNORECASE),
    "cursor-task": re.compile(r"\bTask\b"),
    "ask-question": re.compile(r"\bAskQuestion\b"),
    "subagent-type": re.compile(r"\bsubagent_type\b"),
    "cloud-agent": re.compile(r"\bCursor cloud agents?\b", re.IGNORECASE),
    "control-team-kit": re.compile(r"\b(?:control|cursor)-team-kit\b", re.IGNORECASE),
    "create-skill": re.compile(r"\bcreate-skill\b", re.IGNORECASE),
    "graphite": re.compile(r"\bGraphite\b"),
    "model-slug": re.compile(
        r"\b(?:claude|gpt|grok|gemini)-[a-z0-9][a-z0-9.-]*(?:-[a-z0-9]+)+\b",
        re.IGNORECASE,
    ),
}

PSTACK_SLASH_COMMAND = re.compile(
    r"(?<![A-Za-z0-9])/(?:"
    + "|".join(
        re.escape(name)
        for name in sorted(WORKFLOW_SKILLS | PRINCIPLE_SKILLS, key=lambda value: (-len(value), value))
    )
    + r")\b"
)

MARKDOWN_LINK = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
HEADING = re.compile(r"^(#{1,6})\s+(.+?)\s*$", re.MULTILINE)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def heading_levels(text: str) -> list[int]:
    return [len(match.group(1)) for match in HEADING.finditer(text)]


def heading_anchors(text: str) -> set[str]:
    anchors: set[str] = set()
    for match in HEADING.finditer(text):
        value = match.group(2).strip().lower()
        value = re.sub(r"[`*_]", "", value)
        value = re.sub(r"[^a-z0-9 -]", "", value)
        value = re.sub(r"\s+", "-", value).strip("-")
        anchors.add(value)
    return anchors


class GuidePortTests(unittest.TestCase):
    def test_inventory_is_exactly_eleven_guides_and_six_images(self) -> None:
        actual = {
            path.relative_to(GUIDE).as_posix()
            for path in GUIDE.rglob("*")
            if path.is_file()
        }
        self.assertEqual(actual, MARKDOWN_FILES | set(IMAGE_RECEIPTS))
        self.assertFalse(any(path.is_symlink() for path in GUIDE.rglob("*")))

    def test_images_match_pinned_hashes_bytes_and_modes(self) -> None:
        for relative, expected_hash in IMAGE_RECEIPTS.items():
            with self.subTest(image=relative):
                source = SOURCE / relative
                port = GUIDE / relative
                self.assertEqual(sha256(source), expected_hash)
                self.assertEqual(sha256(port), expected_hash)
                self.assertEqual(port.read_bytes(), source.read_bytes())
                self.assertEqual(
                    stat.S_IMODE(port.stat(follow_symlinks=False).st_mode),
                    stat.S_IMODE(source.stat(follow_symlinks=False).st_mode),
                )
                self.assertFalse(port.is_symlink())

    def test_markdown_preserves_information_architecture_and_examples(self) -> None:
        for name in MARKDOWN_FILES:
            with self.subTest(guide=name):
                source = (SOURCE / name).read_text(encoding="utf-8")
                port = (GUIDE / name).read_text(encoding="utf-8")
                self.assertEqual(heading_levels(port), heading_levels(source))
                self.assertGreaterEqual(port.count("```"), source.count("```"))
                self.assertGreaterEqual(port.count("**Pitfall:**"), source.count("**Pitfall:**"))
                self.assertGreaterEqual(
                    len(MARKDOWN_LINK.findall(port)),
                    len(MARKDOWN_LINK.findall(source)),
                )
                self.assertGreaterEqual(len(port), int(len(source) * 0.70))

    def test_relative_links_and_fragments_resolve(self) -> None:
        for guide_path in sorted(GUIDE.glob("*.md")):
            text = guide_path.read_text(encoding="utf-8")
            for raw_target in MARKDOWN_LINK.findall(text):
                target = raw_target.strip().split(maxsplit=1)[0].strip("<>")
                if target.startswith(("http://", "https://", "mailto:")):
                    continue
                path_text, separator, fragment = target.partition("#")
                resolved = guide_path if not path_text else guide_path.parent / path_text
                with self.subTest(guide=guide_path.name, target=target):
                    self.assertTrue(resolved.exists(), f"broken link: {guide_path} -> {target}")
                    if separator and resolved.suffix.lower() == ".md":
                        anchors = heading_anchors(resolved.read_text(encoding="utf-8"))
                        self.assertIn(fragment, anchors, f"broken anchor: {guide_path} -> {target}")

    def test_adapted_markdown_has_no_live_cursor_mechanics(self) -> None:
        cursor_lines: list[tuple[str, str]] = []
        for path in sorted(GUIDE.glob("*.md")):
            text = path.read_text(encoding="utf-8")
            instruction_text = re.sub(r"(!?\[[^\]]*\])\([^)]+\)", r"\1", text)
            for line in text.splitlines():
                if re.search(r"\bCursor\b", line, re.IGNORECASE):
                    cursor_lines.append((path.name, line))
            for label, pattern in FORBIDDEN_HOST_MECHANICS.items():
                with self.subTest(guide=path.name, mechanic=label):
                    self.assertIsNone(pattern.search(instruction_text))
            with self.subTest(guide=path.name, mechanic="pstack-slash-command"):
                self.assertIsNone(PSTACK_SLASH_COMMAND.search(instruction_text))
        self.assertEqual(cursor_lines, [("README.md", PROVENANCE_CURSOR_LINE)])

    def test_all_first_class_skills_and_poteto_routes_remain_documented(self) -> None:
        combined = "\n".join(
            (GUIDE / name).read_text(encoding="utf-8") for name in sorted(MARKDOWN_FILES)
        )
        for skill in sorted(WORKFLOW_SKILLS | PRINCIPLE_SKILLS):
            with self.subTest(skill=skill):
                self.assertIn(f'pstack:{skill}', combined)
        route_page = (GUIDE / "02-poteto-mode.md").read_text(encoding="utf-8")
        for route in sorted(ROUTED_PLAYBOOKS):
            with self.subTest(route=route):
                self.assertIn(f'`{route}`', route_page)
        self.assertIn("22 routed playbooks", route_page)
        self.assertIn("`opening-a-pr` is the shared postlude, not a route", route_page)

    def test_native_runtime_terms_and_complete_product_boundaries_are_explicit(self) -> None:
        combined = "\n".join(
            (GUIDE / name).read_text(encoding="utf-8") for name in sorted(MARKDOWN_FILES)
        )
        for term in (
            'skill_view("pstack:',
            "delegate_task",
            "delegate_with_route",
            "todo",
            "clarify",
            "session_search",
            "terminal",
            "cronjob",
            "pstack-runtime",
            "pstack-benny",
            "poteto-agent",
            "comment-sicko",
            "setup-benny",
            "triage-issue-reports",
            "reproduce-and-fix-issues",
        ):
            with self.subTest(term=term):
                self.assertIn(term, combined)
        self.assertIn("`pstack-runtime` is optional", combined)
        self.assertIn("does not gate Hermes built-in tools", combined)
        self.assertIn("versioned plugin pack proves source installation", combined)
        self.assertIn("explicit current authorization", combined)

    def test_examples_do_not_execute_external_or_live_profile_actions(self) -> None:
        forbidden_instruction = re.compile(
            r"^(?:git\s+(?:commit|push)|gh\s+pr|commit\b|push\b|merge\b|deploy\b|"
            r"delete\b|send\b|message\b|install\b|publish\b|schedule\b|expose\b)",
            re.IGNORECASE | re.MULTILINE,
        )
        for path in sorted(GUIDE.glob("*.md")):
            text = path.read_text(encoding="utf-8")
            blocks = re.findall(r"```(?:text|bash|shell)?\n(.*?)```", text, re.DOTALL)
            for index, block in enumerate(blocks):
                with self.subTest(guide=path.name, block=index):
                    self.assertIsNone(forbidden_instruction.search(block))

    def test_risk_bearing_pages_state_their_authority_boundaries(self) -> None:
        required = {
            "README.md": ("explicit current authorization", "non-loopback exposure"),
            "01-setup.md": ("versioned plugin pack", "live profile"),
            "02-poteto-mode.md": ("explicit current authorization", "before any deletion"),
            "05-build-and-clean.md": ("does not authorize a commit, push, or PR",),
            "06-verify-and-ship.md": ("explicit current authorization", "Take no external action"),
            "07-overnight.md": ("explicit current authorization", "does not inherit permission"),
            "09-make-it-yours.md": ("explicit current authorization", "dormant resources"),
            "10-recipes-and-pitfalls.md": ("does not authorize external actions",),
        }
        for guide, phrases in required.items():
            text = (GUIDE / guide).read_text(encoding="utf-8")
            for phrase in phrases:
                with self.subTest(guide=guide, phrase=phrase):
                    self.assertIn(phrase, text)


if __name__ == "__main__":
    unittest.main()
