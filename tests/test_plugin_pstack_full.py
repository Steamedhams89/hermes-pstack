"""Executable parity and native-registration gates for the pstack content plugin.

The immutable upstream mirror is the independent contract.  These tests prove
that the native registrar exposes all source skills explicitly as ``pstack:*``
without contributing anything to Hermes' flat startup skill index.
"""
from __future__ import annotations

import importlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import sys

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
PACKAGES_DIR = REPO_ROOT / "packages"
PACKAGE_ROOT = PACKAGES_DIR / "pstack"
SOURCE_ROOT = REPO_ROOT / "upstream" / "pstack"
SOURCE_SKILLS = SOURCE_ROOT / "skills"
LEDGER_PATH = REPO_ROOT / "provenance" / "parity-ledger.json"

if str(PACKAGES_DIR) not in sys.path:
    sys.path.insert(0, str(PACKAGES_DIR))


def _require_hermes_source() -> Path:
    configured = os.environ.get("HERMES_SOURCE_ROOT")
    candidates = [Path(configured)] if configured else []
    candidates.append(REPO_ROOT / "vendor" / "hermes-agent")
    for candidate in candidates:
        if (candidate / "hermes_cli" / "plugins.py").is_file():
            candidate_text = str(candidate)
            if candidate_text in sys.path:
                sys.path.remove(candidate_text)
            sys.path.insert(0, candidate_text)
            local_tools = REPO_ROOT / "tools"
            cached_tools = sys.modules.get("tools")
            cached_path = getattr(cached_tools, "__file__", None)
            if cached_path and Path(cached_path).resolve().is_relative_to(local_tools):
                for module_name in tuple(sys.modules):
                    if module_name == "tools" or module_name.startswith("tools."):
                        sys.modules.pop(module_name, None)
            return candidate
    pytest.skip("Hermes integration source unavailable; set HERMES_SOURCE_ROOT")


EXPECTED_SKILL_NAMES = tuple(
    sorted(path.name for path in SOURCE_SKILLS.iterdir() if (path / "SKILL.md").is_file())
)
EXPECTED_SUPPORT_COUNTS = {"references": 33, "scripts": 21, "playbooks": 23}


@pytest.fixture
def plugin_module():
    import pstack

    return importlib.reload(pstack)


@pytest.fixture
def plugin_context(monkeypatch):
    _require_hermes_source()
    from hermes_cli import plugins as plugins_mod
    from hermes_cli.plugins import PluginContext, PluginManager, PluginManifest

    manager = PluginManager()
    monkeypatch.setattr(plugins_mod, "_plugin_manager", manager)
    manifest = PluginManifest(
        name="pstack",
        version="0.14.5-hermes.1",
        description="test pstack content plugin",
        source="project",
    )
    return manager, PluginContext(manifest, manager)


def _register_and_isolate_flat_index(plugin_module, plugin_context, monkeypatch, tmp_path):
    manager, context = plugin_context
    plugin_module.register(context)
    flat_skills = tmp_path / "flat-skills"
    flat_skills.mkdir()
    monkeypatch.setattr("tools.skills_tool.SKILLS_DIR", flat_skills)
    return manager, flat_skills


def test_source_inventory_is_the_independent_45_skill_contract():
    assert len(EXPECTED_SKILL_NAMES) == 45
    assert EXPECTED_SKILL_NAMES[0] == "architect"
    assert EXPECTED_SKILL_NAMES[-1] == "why"
    assert sum(name.startswith("principle-") for name in EXPECTED_SKILL_NAMES) == 21


def test_manifest_is_native_mit_and_has_exact_product_identity():
    manifest = (PACKAGE_ROOT / "plugin.yaml").read_text(encoding="utf-8")
    assert "name: pstack" in manifest
    assert "version: 0.14.5-hermes.1" in manifest
    assert "license: MIT" in manifest
    assert "portable: true" not in manifest


def test_preflight_accepts_only_the_complete_source_faithful_tree(plugin_module):
    records = plugin_module.preflight_tree()

    assert tuple(record.name for record in records) == EXPECTED_SKILL_NAMES
    assert len(records) == 45
    assert {record.qualified for record in records} == {
        f"pstack:{name}" for name in EXPECTED_SKILL_NAMES
    }
    assert all(record.path.name == "SKILL.md" and record.path.is_file() for record in records)


def test_preflight_fails_before_registration_for_an_unexpected_skill_dir(plugin_module, tmp_path):
    copied = tmp_path / "pstack"
    shutil.copytree(PACKAGE_ROOT, copied)
    extra = copied / "skills" / "not-upstream"
    extra.mkdir()
    (extra / "SKILL.md").write_text("---\nname: not-upstream\n---\n", encoding="utf-8")

    with pytest.raises(plugin_module.PstackPreflightError, match="unexpected"):
        plugin_module.preflight_tree(copied)


def test_preflight_rejects_symlinks_and_path_escape_before_registration(plugin_module, tmp_path):
    copied = tmp_path / "pstack"
    shutil.copytree(PACKAGE_ROOT, copied)
    outside = tmp_path / "outside.md"
    outside.write_text("outside", encoding="utf-8")
    link = copied / "skills" / "architect" / "references" / "escaped.md"
    link.symlink_to(outside)

    with pytest.raises(plugin_module.PstackPreflightError, match="symlink"):
        plugin_module.preflight_tree(copied)

    root_link = tmp_path / "pstack-link"
    root_link.symlink_to(PACKAGE_ROOT, target_is_directory=True)
    with pytest.raises(plugin_module.PstackPreflightError, match="symlink"):
        plugin_module.preflight_tree(root_link)


def test_registers_all_45_qualified_skills_after_preflight(plugin_module, plugin_context):
    manager, context = plugin_context
    plugin_module.register(context)

    assert manager.list_plugin_skills("pstack") == list(EXPECTED_SKILL_NAMES)
    assert set(manager._plugin_skills) == {f"pstack:{name}" for name in EXPECTED_SKILL_NAMES}
    assert all(
        entry["path"].is_relative_to(PACKAGE_ROOT)
        for entry in manager._plugin_skills.values()
    )


def test_qualified_skill_view_loads_every_skill_and_never_populates_flat_index(
    plugin_module, plugin_context, monkeypatch, tmp_path
):
    from tools.skills_tool import skill_view

    manager, flat_skills = _register_and_isolate_flat_index(
        plugin_module, plugin_context, monkeypatch, tmp_path
    )
    for name in EXPECTED_SKILL_NAMES:
        result = json.loads(skill_view(f"pstack:{name}"))
        assert result["success"] is True, result
        assert result["name"] == f"pstack:{name}"
        assert result["content"]

    assert list(flat_skills.iterdir()) == []
    assert plugin_module.flat_skill_index_entries(flat_skills) == ()
    assert len(manager.list_plugin_skills("pstack")) == 45


def test_all_77_skill_local_support_files_are_opened_through_their_owner_skill(
    plugin_module, plugin_context, monkeypatch, tmp_path
):
    from tools.skills_tool import skill_view

    _, flat_skills = _register_and_isolate_flat_index(
        plugin_module, plugin_context, monkeypatch, tmp_path
    )
    supports = plugin_module.iter_support_files()
    counts = {
        kind: sum(1 for support in supports if support.kind == kind)
        for kind in EXPECTED_SUPPORT_COUNTS
    }
    assert counts == EXPECTED_SUPPORT_COUNTS
    assert len(supports) == 77

    for support in supports:
        source_relative = support.path.relative_to(PACKAGE_ROOT / "skills")
        owner, *resource_parts = source_relative.parts
        resource = str(Path(*resource_parts))
        assert support.path.is_relative_to(PACKAGE_ROOT)
        assert support.path.is_file()
        assert not support.path.is_symlink()
        result = json.loads(skill_view(f"pstack:{owner}", file_path=resource))
        assert result["success"] is True, (support.path, result)
        assert result["content"] is not None

    assert list(flat_skills.iterdir()) == []


def test_disabled_plugin_refuses_qualified_skill_view(
    plugin_module, plugin_context, monkeypatch, tmp_path
):
    from tools.skills_tool import skill_view

    _register_and_isolate_flat_index(plugin_module, plugin_context, monkeypatch, tmp_path)
    monkeypatch.setattr("hermes_cli.plugins._get_disabled_plugins", lambda: {"pstack"})

    result = json.loads(skill_view("pstack:architect"))
    assert result["success"] is False
    assert "disabled" in result["error"].lower()


def test_unload_then_reload_rebuilds_the_exact_registry(plugin_module, plugin_context):
    manager, context = plugin_context
    plugin_module.register(context)
    assert manager.unload("pstack") is True
    assert manager.list_plugin_skills("pstack") == []

    plugin_module.register(context)
    assert manager.list_plugin_skills("pstack") == list(EXPECTED_SKILL_NAMES)


def test_every_qualified_cross_reference_resolves_and_playbooks_are_linked_resources():
    """No prose may invent pstack:<playbook> as a registered skill identity."""
    actual = {f"pstack:{name}" for name in EXPECTED_SKILL_NAMES}
    pattern = re.compile(
        r"skill_view\(\s*(?:name\s*=\s*)?['\"](pstack:[A-Za-z0-9_-]+)['\"]"
        r"(?:\s*,\s*file_path\s*=\s*['\"]([^'\"]+)['\"])?\s*\)"
    )
    references: list[tuple[Path, str, str | None]] = []
    for path in PACKAGE_ROOT.glob("skills/**/*.md"):
        text = path.read_text(encoding="utf-8")
        references.extend((path, name, resource or None) for name, resource in pattern.findall(text))

    assert references, "expected explicit qualified cross-skill calls"
    for path, name, resource in references:
        assert name in actual, f"invented pstack identity in {path}: {name}"
        if resource is None:
            continue
        assert name == "pstack:poteto-mode", (path, name, resource)
        assert resource.startswith("playbooks/"), (path, resource)
        linked = PACKAGE_ROOT / "skills" / "poteto-mode" / resource
        assert linked.is_file(), f"missing linked Poteto resource: {linked}"

    text = "\n".join(path.read_text(encoding="utf-8") for path in PACKAGE_ROOT.glob("skills/**/*.md"))
    assert "pstack:<" not in text
    assert not re.search(
        r"skill_view\([^\n]*pstack:(?:authoring-a-skill|autonomous-run|autopilot-full|autopilot-stack|"
        r"babysit|bug-fix|eval|feature|hillclimb|investigation|multi-phase-plan|opening-a-pr|"
        r"orchestrate|pause-safely|perf-issue|prototype|refactoring|runtime-forensics|session-pickup|"
        r"shipping|trace-forensics|visual-parity|worktree-cleanup)",
        text,
    )


def test_operative_markdown_has_no_live_cursor_runtime_primitive():
    forbidden = {
        "Cursor proper noun": r"\bCursor\b",
        "Cursor state path": r"(?:^|[^A-Za-z0-9_])\.cursor(?:/|\b)",
        "Cursor Task primitive": r"\bTask\s*\(",
        "Cursor subagent type": r"\bsubagent_type\b",
        "Cursor question primitive": r"\bAskQuestion\b",
        "Cursor background primitive": r"\brun_in_background\b",
        "Cursor readonly primitive": r"\breadonly:\s*(?:true|false)\b",
        "Cursor loop or goal command": r"(?<!\w)/(?:loop|goal)\b",
        "Cursor control surface": r"\bcontrol-(?:ui|cli)\b",
        "Cursor transcript directory": r"\bagent-transcripts\b",
        "Cursor home path": r"~/.cursor",
        "unapproved autonomous merge": r"\b(?:owner|agent|child)\s+(?:squash-)?merges\b",
        "unapproved autonomous push": r"\b(?:owner|agent|child)\s+push(?:es)?\b",
        "unapproved autonomous PR creation": r"\b(?:owner|agent|child)\s+(?:opens|creates)\s+(?:a )?(?:pull request|PR)\b",
        "automatic landing claim": r"\bland(?:s)? automatically\b",
        "autonomy as merge authority": r"\bfull-autonomy grant\b.*\bmerge authorization\b",
        "direct Graphite execution": r"\bgt\s+(?:submit|merge|restack|sync|track)\b",
    }
    failures: list[str] = []
    for path in PACKAGE_ROOT.glob("skills/**/*.md"):
        text = path.read_text(encoding="utf-8")
        for label, pattern in forbidden.items():
            if re.search(pattern, text):
                failures.append(f"{path.relative_to(REPO_ROOT)}: {label}")
    assert not failures, "\n".join(failures)


def test_exact_negative_fixtures_and_authority_path_behavior(tmp_path):
    fixtures = json.loads(
        (REPO_ROOT / "tests" / "fixtures" / "plugin" / "operational-negative-fixtures.json").read_text(
            encoding="utf-8"
        )
    )
    for relative, prohibited in fixtures["unsupported_sibling_slashes"].items():
        text = (PACKAGE_ROOT / relative).read_text(encoding="utf-8")
        assert all(marker not in text for marker in prohibited), (relative, prohibited)

    no_comments = (PACKAGE_ROOT / "skills" / "no-comments" / "SKILL.md").read_text(encoding="utf-8")
    assert "skill_view(name='pstack:how')" in no_comments
    assert "skill_view(name='pstack:why')" in no_comments
    assert "skill_view(name='pstack:architect')" in no_comments
    verification = (PACKAGE_ROOT / "skills" / "create-verification-skill" / "SKILL.md").read_text(encoding="utf-8")
    assert "skill_view(name='pstack:maintain-verification-skill')" in verification
    opening = (PACKAGE_ROOT / "skills" / "poteto-mode" / "playbooks" / "opening-a-pr.md").read_text(encoding="utf-8")
    assert "skill_view(name='pstack:unslop')" in opening

    authority_paths = (
        PACKAGE_ROOT / "skills" / "poteto-mode" / "playbooks" / "babysit.md",
        PACKAGE_ROOT / "skills" / "poteto-mode" / "playbooks" / "multi-phase-plan.md",
        PACKAGE_ROOT / "skills" / "poteto-mode" / "playbooks" / "orchestrate.md",
        PACKAGE_ROOT / "skills" / "poteto-mode" / "playbooks" / "worktree-cleanup.md",
    )
    authority_text = "\n".join(path.read_text(encoding="utf-8") for path in authority_paths)
    for marker in fixtures["unsupported_control_claims"]:
        assert marker not in authority_text
    for marker in fixtures["required_degradations"] + fixtures["authority_requirements"]:
        assert marker in authority_text

    repo = tmp_path / "review-only-repo"
    subprocess.run(["git", "init", "-b", "main", str(repo)], check=True, capture_output=True, text=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.email", "pstack@example.invalid"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.name", "Pstack Test"], check=True)
    (repo / "tracked.txt").write_text("tracked\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(repo), "add", "tracked.txt"], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-m", "initial"], check=True, capture_output=True, text=True)
    audit = PACKAGE_ROOT / "skills" / "poteto-mode" / "scripts" / "worktree-audit.sh"
    receipt = subprocess.run([str(audit), str(repo)], check=False, capture_output=True, text=True)
    assert receipt.returncode == 0, receipt.stderr
    assert receipt.stdout.startswith("SIZE\tAGE\tMERGED\tDIRTY\tREMOTE\tPR\tLAST_CHAT\tBUCKET\tWORKTREE")
    assert (repo / "tracked.txt").read_text(encoding="utf-8") == "tracked\n"
    status = subprocess.run(["git", "-C", str(repo), "status", "--porcelain"], check=True, capture_output=True, text=True)
    assert status.stdout == ""


def test_role_bearing_workflows_read_named_route_or_fall_back_to_inherited_delegation():
    named_roles = {
        "arena": ("arena-runners", "arena-cross-judge-pool"),
        "architect": ("architect-runners",),
        "why": ("why-investigators", "why-synthesizer"),
        "swarm": ("swarm-workers",),
        "show-me-your-work": ("judgment-and-prose",),
        "reflect": ("reflect-judgment", "reflect-tooling", "reflect-divergent", "reflect-synthesizer"),
        "interrogate": ("interrogate-reviewers",),
        "how": ("how-explorer", "how-explainer", "how-critics"),
    }
    for skill, roles in named_roles.items():
        text = (PACKAGE_ROOT / "skills" / skill / "SKILL.md").read_text(encoding="utf-8")
        assert "pstack_routes" in text
        assert "delegate_task" in text
        assert "delegate_with_route" in text or "approved route alias" in text
        assert "inherited" in text
        for role in roles:
            assert f"effective.roles.{role}" in text

    poteto = (PACKAGE_ROOT / "skills" / "poteto-mode" / "SKILL.md").read_text(encoding="utf-8")
    assert "pstack_routes" in poteto
    for route in ("feature", "bug-fix", "perf-issue", "refactoring", "hillclimb"):
        assert f"`{route}` → `{route}`" in poteto
    assert "other playbooks inherit the parent route" in poteto


def test_bootstrap_fails_closed_without_implicit_provisioning_and_is_node_parseable():
    bootstrap = PACKAGE_ROOT / "skills" / "poteto-mode" / "scripts" / "bootstrap.ts"
    text = bootstrap.read_text(encoding="utf-8")
    assert "PATCH-HERMES-NO-IMPLICIT-INSTALL" in text
    assert "Bun.spawnSync" not in text
    assert "writeFileSync" not in text
    assert "Do not install automatically" in text
    assert "authorize `bun install --frozen-lockfile`" in text
    node = shutil.which("node")
    assert node is not None
    result = subprocess.run(
        [node, "--experimental-strip-types", "--check", str(bootstrap)],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr


def test_make_bot_ui_uses_hermes_webhook_hmac_and_loopback_relay_contract():
    text = (PACKAGE_ROOT / "skills" / "make-bot-ui" / "SKILL.md").read_text(encoding="utf-8")
    for marker in (
        "PATCH-HERMES-MAKE-BOT-UI",
        "skill_view(name='webhook-subscriptions')",
        "hermes webhook subscribe",
        "hermes webhook list",
        "X-Webhook-Signature-V2",
        "X-Webhook-Timestamp",
        "<timestamp>.<body>",
        "HMAC",
        "127.0.0.1",
        "tailscale serve",
        "mode `0600`",
        "untrusted data",
        "harmless test button",
    ):
        assert marker in text
    for forbidden in (
        "update_state",
        "SendToUser",
        "api2.cursor.sh",
        "X-Automation-Key",
        "Authorization: Bearer",
        "curl -fsSL",
        "0.0.0.0",
    ):
        assert forbidden not in text


def test_make_bot_ui_requires_approval_before_recurring_security_or_exposure_changes():
    text = (PACKAGE_ROOT / "skills" / "make-bot-ui" / "SKILL.md").read_text(encoding="utf-8")
    for marker in (
        "explicit approval",
        "recurring webhook subscription",
        "gateway or security configuration",
        "installing software",
        "non-loopback exposure",
        "externally visible action",
        "does not authorize those changes",
        "Do not install dependencies implicitly",
        "without approval",
    ):
        assert marker in text


def test_workspace_has_no_cache_bytecode_or_machine_absolute_artifacts():
    forbidden_names = {".pytest_cache", "__pycache__"}
    forbidden_suffixes = {".pyc", ".pyo", ".pyd"}
    forbidden_bytes = (
        b"/" + b"home/",
        b"/" + b"Users/",
        b"C:" + b"\\" + b"Users\\",
    )
    failures: list[str] = []
    for path in REPO_ROOT.rglob("*"):
        relative = path.relative_to(REPO_ROOT)
        if "upstream" in relative.parts:
            continue
        if path.name in forbidden_names or path.suffix in forbidden_suffixes:
            failures.append(str(relative))
            continue
        if not path.is_file():
            continue
        try:
            data = path.read_bytes()
        except OSError as exc:
            failures.append(f"{relative}: unreadable ({exc})")
            continue
        if any(marker in data for marker in forbidden_bytes):
            failures.append(f"{relative}: machine-specific absolute path")
    assert not failures, "\n".join(failures)


def test_parity_ledger_enforces_exact_verbatim_modes_and_exactly_50_adapted_rows():
    ledger = json.loads(LEDGER_PATH.read_text(encoding="utf-8"))
    entries = [
        entry
        for entry in ledger["entries"]
        if str(entry.get("port_target", "")).startswith("packages/pstack/")
    ]
    verbatim = [entry for entry in entries if not entry["patch_ids"]]
    adapted = [entry for entry in entries if entry["patch_ids"]]
    assert len(entries) == 122
    assert len(verbatim) == 72
    assert len(adapted) == 50

    changed: set[str] = set()
    for entry in entries:
        source = SOURCE_ROOT / entry["source_path"]
        target = REPO_ROOT / entry["port_target"]
        assert source.is_file(), source
        assert target.is_file(), target
        assert stat.S_IMODE(source.stat().st_mode) == int(entry["mode"], 8)
        assert stat.S_IMODE(target.stat().st_mode) == int(entry["mode"], 8)
        if not entry["patch_ids"]:
            assert entry["disposition"] in {"verbatim_copy", "verbatim_copy_pending"}
            assert target.read_bytes() == source.read_bytes(), target
            continue
        assert entry["disposition"] in {
            "mechanical_patch",
            "mechanical_patch_pending",
            "semantic_adapter",
            "semantic_adapter_pending",
        }
        assert target.read_bytes() != source.read_bytes(), target
        changed.add(str(target.relative_to(REPO_ROOT)))
        text = target.read_text(encoding="utf-8", errors="replace")
        for patch_id in entry["patch_ids"]:
            assert patch_id in text, (target, patch_id)

    assert len(changed) == 50


def test_content_package_has_no_process_or_external_side_effect_surface(plugin_module):
    package_python = (PACKAGE_ROOT / "__init__.py").read_text(encoding="utf-8")
    forbidden = ("subprocess", "os.system", "git commit", "git push", "deploy", "requests.")
    assert not any(token in package_python for token in forbidden)
    assert plugin_module.EXPECTED_SKILL_NAMES == EXPECTED_SKILL_NAMES


def test_executable_package_code_has_no_dean_path_or_live_cursor_state_path():
    forbidden = (
        "/" + "home/" + "dean",
        "~/" + ".cursor",
        ".cursor" + "/projects",
        "/" + "Users/",
    )
    candidates = [PACKAGE_ROOT / "__init__.py"]
    candidates.extend((PACKAGE_ROOT / "skills").glob("**/scripts/*"))
    violations: list[str] = []
    for path in candidates:
        if not path.is_file() or path.suffix not in {".py", ".sh", ".ts", ".mjs", ".json"}:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        if any(token in text for token in forbidden):
            violations.append(str(path.relative_to(REPO_ROOT)))
    assert not violations, violations


def test_no_generator_or_marker_only_policy_artifact_is_shipped():
    prohibited = {
        "_adapt_once.py",
        "_apply_patch_ids.py",
        "_apply_exact_core.py",
        "_apply_exact_playbooks.py",
        "_apply_remaining_core.py",
        "resources/HERMES_ADAPTER_POLICY.md",
    }
    present = {
        str(path.relative_to(PACKAGE_ROOT))
        for path in PACKAGE_ROOT.rglob("*")
        if path.is_file() and str(path.relative_to(PACKAGE_ROOT)) in prohibited
    }
    assert not present, present


def test_fresh_process_qualified_loading_and_linked_poteto_resource(tmp_path):
    hermes_source = _require_hermes_source()
    script = """
import json
import sys
from pathlib import Path
repo = Path(sys.argv[1])
source = Path(sys.argv[2])
sys.path.insert(0, str(repo / 'packages'))
sys.path.insert(0, str(source))
from hermes_cli import plugins as plugins_mod
from hermes_cli.plugins import PluginContext, PluginManager, PluginManifest
import pstack
manager = PluginManager()
plugins_mod._plugin_manager = manager
context = PluginContext(PluginManifest(name='pstack', version='0.14.5-hermes.1', description='fresh', source='project'), manager)
pstack.register(context)
from tools.skills_tool import skill_view
main = json.loads(skill_view('pstack:architect'))
playbook = json.loads(skill_view(name='pstack:poteto-mode', file_path='playbooks/bug-fix.md'))
print(json.dumps({'skills': manager.list_plugin_skills('pstack'), 'main': main['success'], 'playbook': playbook['success']}))
"""
    environment = os.environ.copy()
    environment["HERMES_HOME"] = str(tmp_path / "isolated-hermes")
    existing = environment.get("PYTHONPATH", "")
    environment["PYTHONPATH"] = os.pathsep.join(
        part for part in (str(PACKAGES_DIR), str(hermes_source), existing) if part
    )
    result = subprocess.run(
        [sys.executable, "-c", script, str(REPO_ROOT), str(hermes_source)],
        cwd=REPO_ROOT,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    receipt = json.loads(result.stdout.strip().splitlines()[-1])
    assert receipt["skills"] == list(EXPECTED_SKILL_NAMES)
    assert receipt["main"] is True
    assert receipt["playbook"] is True
