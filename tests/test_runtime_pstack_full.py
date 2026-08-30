"""Executable contract tests for the optional, disabled-by-default pstack runtime.

This companion only validates/declaratively describes routes and exposes two
explicit role briefs.  It neither selects providers nor starts child work,
background loops, or external automation.
"""
from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import stat
import sys

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
PACKAGES_DIR = REPO_ROOT / "packages"
RUNTIME_ROOT = PACKAGES_DIR / "pstack-runtime"
SOURCE_ROOT = REPO_ROOT / "upstream" / "pstack"
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


@pytest.fixture
def runtime_module():
    module_path = RUNTIME_ROOT / "__init__.py"
    spec = importlib.util.spec_from_file_location("pstack_runtime", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_runtime_manifest_is_separate_native_package_without_auto_activation_claim():
    manifest = (RUNTIME_ROOT / "plugin.yaml").read_text(encoding="utf-8")
    assert "name: pstack-runtime" in manifest
    assert "version: 0.14.5-hermes.1" in manifest
    assert "license: MIT" in manifest
    assert "provides_hooks:" not in manifest
    assert "requires_plugins:" not in manifest
    assert "provides_tools:" in manifest
    assert "- pstack_routes" in manifest


def test_raw_agent_prompts_are_exact_provenance_copies_and_wrappers_are_operational(
    runtime_module,
):
    assert set(runtime_module.AGENT_PROMPTS) == {"poteto-agent", "comment-sicko"}
    assert set(runtime_module.ROLE_SKILLS) == set(runtime_module.AGENT_PROMPTS)
    for identity, prompt_path in runtime_module.AGENT_PROMPTS.items():
        upstream = SOURCE_ROOT / "agents" / f"{identity}.md"
        assert prompt_path.read_bytes() == upstream.read_bytes()
        assert runtime_module.load_agent_prompt(identity) == upstream.read_text(encoding="utf-8")
        wrapper = runtime_module.ROLE_SKILLS[identity].read_text(encoding="utf-8")
        assert "disable-model-invocation: true" in wrapper
        assert "provenance only" in wrapper.lower()
        assert "delegate_task" in wrapper
        assert "executable hermes mapping" in wrapper.lower()


def test_route_schema_accepts_exact_aliases_and_rejects_provider_model_selectors(runtime_module):
    assert runtime_module.ROUTE_ALIASES == {
        "inherit-parent", "bounded", "routine", "hard", "x-research", "video"
    }
    for alias in runtime_module.ROUTE_ALIASES:
        route = runtime_module.validate_route(
            {"role": "feature", "execution": "delegate", "route": alias}
        )
        assert route.route == alias

    with pytest.raises(runtime_module.RouteValidationError, match="model"):
        runtime_module.validate_route(
            {
                "role": "feature",
                "execution": "delegate",
                "route": "inherit-parent",
                "model": "arbitrary-unverified-slug",
            }
        )
    with pytest.raises(runtime_module.RouteValidationError, match="role"):
        runtime_module.validate_route(
            {"role": "not-a-role", "execution": "delegate", "route": "inherit-parent"}
        )
    with pytest.raises(runtime_module.RouteValidationError, match="route alias"):
        runtime_module.validate_route(
            {"role": "feature", "execution": "delegate", "route": "auto"}
        )


def test_direct_route_describes_native_primitive_without_executing_it(runtime_module):
    route = runtime_module.validate_route(
        {"role": "feature", "execution": "delegate", "route": "inherit-parent"}
    )
    result = runtime_module.resolve_route(route, runtime_enabled=False, capability_granted=False)

    assert result.status == "ready"
    assert result.code == "native_primitive"
    assert result.execution == {
        "primitive": "delegate_task",
        "role": "feature",
        "execution": "delegate",
        "route": "inherit-parent",
    }
    assert "does not execute" in result.message


def test_non_parent_alias_requires_runtime_and_explicit_capability(runtime_module):
    route = runtime_module.validate_route(
        {"role": "feature", "execution": "delegate", "route": "hard"}
    )
    unavailable = runtime_module.resolve_route(
        route, runtime_enabled=False, capability_granted=False
    )
    assert unavailable.status == "degraded"
    assert unavailable.code == "capability_unavailable"

    not_granted = runtime_module.resolve_route(
        route, runtime_enabled=True, capability_granted=False
    )
    assert not_granted.status == "degraded"

    ready = runtime_module.resolve_route(route, runtime_enabled=True, capability_granted=True)
    assert ready.status == "ready"
    assert ready.execution["primitive"] == "delegate_with_route"


def test_fake_safe_adapter_is_injected_and_returns_only_its_local_receipt(runtime_module):
    route = runtime_module.validate_route(
        {"role": "feature", "execution": "delegate", "route": "inherit-parent"}
    )
    seen = []

    def fake_adapter(request):
        seen.append(request)
        return {"status": "accepted", "receipt": "fake-1", "code": "test-only"}

    result = runtime_module.resolve_route(
        route, runtime_enabled=True, capability_granted=True, adapter=fake_adapter
    )
    assert result.status == "accepted"
    assert result.code == "test-only"
    assert result.receipt == "fake-1"
    assert seen == [route]


def test_content_only_degradation_is_truthful_for_unproven_capabilities(runtime_module):
    result = runtime_module.content_only_degradation("sticky-continuation")
    assert result.status == "degraded"
    assert result.code == "capability_unavailable"
    assert "unavailable" in result.message
    assert "sandbox" not in result.message.lower()


def _runtime_tool(runtime_module, monkeypatch):
    _require_hermes_source()
    from hermes_cli import plugins as plugins_mod
    from hermes_cli.plugins import PluginContext, PluginManager, PluginManifest
    from tools.registry import registry

    manager = PluginManager()
    monkeypatch.setattr(plugins_mod, "_plugin_manager", manager)
    context = PluginContext(
        PluginManifest(name="pstack-runtime", version="0.14.5-hermes.1", description="runtime", source="project"),
        manager,
    )
    runtime_module.register(context)
    entry = registry.get_entry(runtime_module.ROUTE_TOOL_NAME, scope=manager.scope_key)
    assert entry is not None
    assert entry.toolset == runtime_module.ROUTE_TOOLSET
    return manager, entry


def _dispatch_route_tool(manager, runtime_module, arguments):
    from tools.registry import registry

    raw = registry.dispatch(
        runtime_module.ROUTE_TOOL_NAME,
        arguments,
        scope=manager.scope_key,
    )
    assert isinstance(raw, str)
    return json.loads(raw)


def test_registered_route_tool_get_has_no_registration_or_get_write(runtime_module, monkeypatch, tmp_path):
    hermes_home = tmp_path / "isolated-hermes"
    monkeypatch.setenv("HERMES_HOME", str(hermes_home))

    manager, entry = _runtime_tool(runtime_module, monkeypatch)
    assert not hermes_home.exists()
    from tools.registry import registry

    definitions = registry.get_definitions({runtime_module.ROUTE_TOOL_NAME})
    assert definitions == [{"type": "function", "function": runtime_module.ROUTE_TOOL_SCHEMA}]
    response = _dispatch_route_tool(manager, runtime_module, {"action": "get"})
    assert response["ok"] is True
    assert response["action"] == "get"
    assert response["persisted"] == {"roles": {}}
    assert response["defaults"]["roles"] == runtime_module.DEFAULT_ROLE_MAPPING
    assert response["effective"]["roles"] == runtime_module.DEFAULT_ROLE_MAPPING
    assert not hermes_home.exists()


def test_registered_route_tool_set_requires_complete_mapping_and_reads_back(runtime_module, monkeypatch, tmp_path):
    hermes_home = tmp_path / "isolated-hermes"
    monkeypatch.setenv("HERMES_HOME", str(hermes_home))
    manager, entry = _runtime_tool(runtime_module, monkeypatch)
    mapping = dict(runtime_module.DEFAULT_ROLE_MAPPING)
    mapping["feature"] = "bounded"
    mapping["why-synthesizer"] = "hard"

    response = _dispatch_route_tool(
        manager,
        runtime_module,
        {"action": "set", "roles": mapping},
    )
    assert response == {"ok": True, "action": "set", "persisted": {"roles": mapping}}
    path = runtime_module.role_config_path()
    assert path.exists()
    assert stat.S_IMODE(path.stat().st_mode) == 0o600
    assert stat.S_IMODE(path.parent.stat().st_mode) == 0o700
    assert _dispatch_route_tool(manager, runtime_module, {"action": "get"})["effective"] == {"roles": mapping}


def test_registered_route_tool_refuses_incomplete_bad_and_symlinked_sets(runtime_module, monkeypatch, tmp_path):
    hermes_home = tmp_path / "isolated-hermes"
    monkeypatch.setenv("HERMES_HOME", str(hermes_home))
    manager, entry = _runtime_tool(runtime_module, monkeypatch)
    partial = {"feature": "bounded"}
    incomplete = _dispatch_route_tool(
        manager,
        runtime_module,
        {"action": "set", "roles": partial},
    )
    assert incomplete["ok"] is False
    assert "complete role mapping" in incomplete["message"]
    assert not hermes_home.exists()

    bad_role = dict(runtime_module.DEFAULT_ROLE_MAPPING)
    bad_role["not-a-role"] = "bounded"
    assert _dispatch_route_tool(
        manager,
        runtime_module,
        {"action": "set", "roles": bad_role},
    )["ok"] is False
    bad_alias = dict(runtime_module.DEFAULT_ROLE_MAPPING)
    bad_alias["feature"] = "unverified"
    assert _dispatch_route_tool(
        manager,
        runtime_module,
        {"action": "set", "roles": bad_alias},
    )["ok"] is False

    path = runtime_module.role_config_path()
    path.parent.mkdir(parents=True)
    outside = tmp_path / "outside.yaml"
    outside.write_text("roles: {}\n", encoding="utf-8")
    path.symlink_to(outside)
    refused = _dispatch_route_tool(manager, runtime_module, {"action": "get"})
    assert refused["ok"] is False
    assert "symlinked roles file" in refused["message"]


def test_setup_skill_uses_registered_tool_and_route_dispatch_contract(runtime_module, monkeypatch, tmp_path):
    monkeypatch.setenv("HERMES_HOME", str(tmp_path / "isolated-hermes"))
    manager, entry = _runtime_tool(runtime_module, monkeypatch)
    setup = (PACKAGES_DIR / "pstack" / "skills" / "setup-pstack" / "SKILL.md").read_text(encoding="utf-8")
    assert "`pstack_routes`" in setup
    assert "pstack-runtime.write_role_config" not in setup
    mapping = dict(runtime_module.DEFAULT_ROLE_MAPPING)
    mapping["architect-runners"] = "routine"
    set_result = _dispatch_route_tool(
        manager,
        runtime_module,
        {"action": "set", "roles": mapping},
    )
    assert set_result["persisted"]["roles"]["architect-runners"] == "routine"
    assert _dispatch_route_tool(manager, runtime_module, {"action": "get"})["effective"]["roles"] == mapping


def test_route_tool_schema_has_stable_measured_character_cost(runtime_module):
    serialized = json.dumps(runtime_module.ROUTE_TOOL_SCHEMA, sort_keys=True, separators=(",", ":"))
    assert runtime_module.ROUTE_TOOL_SCHEMA_JSON == serialized
    assert runtime_module.ROUTE_TOOL_SCHEMA_CHARACTERS == len(serialized)
    assert runtime_module.ROUTE_TOOL_SCHEMA["name"] == "pstack_routes"
    assert runtime_module.ROUTE_TOOL_SCHEMA["description"]
    assert runtime_module.ROUTE_TOOL_SCHEMA["parameters"] == runtime_module.ROUTE_TOOL_PARAMETERS
    assert runtime_module.ROUTE_TOOL_SCHEMA_CHARACTERS == 3312


def test_runtime_wrappers_register_as_explicit_qualified_skills_without_flat_index(
    runtime_module, monkeypatch, tmp_path
):
    _require_hermes_source()
    from hermes_cli import plugins as plugins_mod
    from hermes_cli.plugins import PluginContext, PluginManager, PluginManifest
    from tools.skills_tool import skill_view

    manager = PluginManager()
    monkeypatch.setattr(plugins_mod, "_plugin_manager", manager)
    flat_skills = tmp_path / "flat-skills"
    flat_skills.mkdir()
    monkeypatch.setattr("tools.skills_tool.SKILLS_DIR", flat_skills)
    context = PluginContext(
        PluginManifest(
            name="pstack-runtime",
            version="0.14.5-hermes.1",
            description="runtime test",
            source="project",
        ),
        manager,
    )
    runtime_module.register(context)

    assert manager.list_plugin_skills("pstack-runtime") == ["comment-sicko", "poteto-agent"]
    for name in ("poteto-agent", "comment-sicko"):
        result = json.loads(skill_view(f"pstack-runtime:{name}"))
        assert result["success"] is True, result
    assert list(flat_skills.iterdir()) == []

    monkeypatch.setattr("hermes_cli.plugins._get_disabled_plugins", lambda: {"pstack-runtime"})
    disabled = json.loads(skill_view("pstack-runtime:poteto-agent"))
    assert disabled["success"] is False
    assert "disabled" in disabled["error"].lower()


def test_runtime_unload_then_reload_rebuilds_two_wrappers_and_route_tool(runtime_module, monkeypatch, tmp_path):
    _require_hermes_source()
    monkeypatch.setenv("HERMES_HOME", str(tmp_path / "isolated-hermes"))
    from hermes_cli import plugins as plugins_mod
    from hermes_cli.plugins import PluginContext, PluginManager, PluginManifest
    from tools.registry import registry

    manager = PluginManager()
    monkeypatch.setattr(plugins_mod, "_plugin_manager", manager)
    context = PluginContext(
        PluginManifest(name="pstack-runtime", version="0.14.5-hermes.1", description="runtime", source="project"),
        manager,
    )
    runtime_module.register(context)
    assert registry.get_entry(runtime_module.ROUTE_TOOL_NAME, scope=manager.scope_key) is not None
    assert manager.unload("pstack-runtime") is True
    assert manager.list_plugin_skills("pstack-runtime") == []
    assert registry.get_entry(runtime_module.ROUTE_TOOL_NAME, scope=manager.scope_key) is None
    runtime_module.register(context)
    assert manager.list_plugin_skills("pstack-runtime") == ["comment-sicko", "poteto-agent"]
    assert registry.get_entry(runtime_module.ROUTE_TOOL_NAME, scope=manager.scope_key) is not None


def test_runtime_package_has_one_local_tool_and_no_hook_background_or_external_side_effect_surface():
    package_python = (RUNTIME_ROOT / "__init__.py").read_text(encoding="utf-8")
    forbidden = (
        "subprocess",
        "os.system",
        "delegate_task(",
        "delegate_with_route(",
        "cronjob(",
        "register_hook",
        "git commit",
        "git push",
        "requests.",
    )
    assert package_python.count("ctx.register_tool(") == 1
    assert not any(token in package_python for token in forbidden)
