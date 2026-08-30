"""Optional, fake-safe native companion for the pstack content plugin.

The content package works without this plugin. This companion exposes two
qualified role briefs plus one explicit local route-configuration tool. It
registers no hooks, background work, or external integrations, and it never
starts delegation itself.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
import re
from typing import Any, Callable, Mapping

PLUGIN_ROOT = Path(__file__).resolve().parent
AGENT_PROMPTS = {
    "poteto-agent": PLUGIN_ROOT / "resources" / "agents" / "poteto-agent.md",
    "comment-sicko": PLUGIN_ROOT / "resources" / "agents" / "comment-sicko.md",
}
ROLE_SKILLS = {
    "poteto-agent": PLUGIN_ROOT / "skills" / "poteto-agent" / "SKILL.md",
    "comment-sicko": PLUGIN_ROOT / "skills" / "comment-sicko" / "SKILL.md",
}
ROLE_IDS = frozenset(
    {
        "arena-cross-judge-pool",
        "arena-runners",
        "architect-runners",
        "bug-fix",
        "feature",
        "hardest-tasks",
        "hillclimb",
        "how-critics",
        "how-explainer",
        "how-explorer",
        "interrogate-reviewers",
        "judgment-and-prose",
        "perf-issue",
        "refactoring",
        "reflect-divergent",
        "reflect-judgment",
        "reflect-synthesizer",
        "reflect-tooling",
        "swarm-workers",
        "video-review",
        "why-investigators",
        "why-synthesizer",
    }
)
ROUTE_ALIASES = frozenset(
    {"inherit-parent", "bounded", "routine", "hard", "x-research", "video"}
)
ROUTE_TOOL_NAME = "pstack_routes"
ROUTE_TOOLSET = "pstack-runtime"
DEFAULT_ROLE_MAPPING = dict.fromkeys(sorted(ROLE_IDS), "inherit-parent")
ROUTE_TOOL_PARAMETERS = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "action": {"type": "string", "enum": ["get", "set"]},
        "roles": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                role: {"type": "string", "enum": sorted(ROUTE_ALIASES)}
                for role in sorted(ROLE_IDS)
            },
            "required": sorted(ROLE_IDS),
        },
    },
    "required": ["action"],
    "oneOf": [
        {"properties": {"action": {"const": "get"}}, "not": {"required": ["roles"]}},
        {"properties": {"action": {"const": "set"}}, "required": ["roles"]},
    ],
}
ROUTE_TOOL_SCHEMA = {
    "name": ROUTE_TOOL_NAME,
    "description": (
        "Read or replace the complete local pstack role-to-route mapping. "
        "Use get for a non-writing read; set requires every named role."
    ),
    "parameters": ROUTE_TOOL_PARAMETERS,
}
ROUTE_TOOL_SCHEMA_JSON = json.dumps(ROUTE_TOOL_SCHEMA, sort_keys=True, separators=(",", ":"))
ROUTE_TOOL_SCHEMA_CHARACTERS = len(ROUTE_TOOL_SCHEMA_JSON)
EXECUTION_IDS = frozenset({"content-only", "delegate", "review"})
_SKILL_NAME_RE = re.compile(r"^[a-zA-Z0-9_-]+$")


class RouteValidationError(ValueError):
    """Raised when content requests an unsupported local runtime contract."""


@dataclass(frozen=True)
class Route:
    role: str
    execution: str
    route: str = "inherit-parent"
    requires_runtime: bool = False


@dataclass(frozen=True)
class CapabilityResult:
    status: str
    code: str
    message: str
    execution: Mapping[str, Any] | None = None
    receipt: str | None = None


def _contained(path: Path, root: Path) -> Path:
    if path.is_symlink():
        raise RouteValidationError(f"symlinked runtime path is refused: {path}")
    resolved_root = root.resolve()
    resolved = path.resolve()
    try:
        resolved.relative_to(resolved_root)
    except ValueError as exc:
        raise RouteValidationError(f"runtime path escapes package: {path}") from exc
    return resolved


def load_agent_prompt(identity: str) -> str:
    """Read one raw, preserved upstream role prompt without executing it."""
    try:
        path = AGENT_PROMPTS[identity]
    except KeyError as exc:
        raise RouteValidationError(f"unknown preserved agent prompt: {identity}") from exc
    _contained(path, PLUGIN_ROOT)
    if not path.is_file():
        raise RouteValidationError(f"missing preserved agent prompt: {identity}")
    return path.read_text(encoding="utf-8")


def _role_skill_records() -> tuple[tuple[str, Path], ...]:
    records: list[tuple[str, Path]] = []
    seen: set[str] = set()
    for identity, path in ROLE_SKILLS.items():
        if not _SKILL_NAME_RE.fullmatch(identity) or identity in seen:
            raise RouteValidationError(f"invalid or duplicate role identity: {identity!r}")
        _contained(path, PLUGIN_ROOT)
        if not path.is_file():
            raise RouteValidationError(f"missing role skill: {identity}")
        if not load_agent_prompt(identity):
            raise RouteValidationError(f"empty raw role prompt: {identity}")
        seen.add(identity)
        records.append((identity, path))
    if set(seen) != set(AGENT_PROMPTS) or len(records) != 2:
        raise RouteValidationError("runtime role registry must contain exactly two preserved prompts")
    return tuple(records)


def validate_route(raw: Mapping[str, Any]) -> Route:
    """Validate a declarative route without selecting a provider or dispatching."""
    if not isinstance(raw, Mapping):
        raise RouteValidationError("route must be a mapping")
    if "model" in raw:
        raise RouteValidationError("provider model selectors are unsupported; use a route alias")
    role = raw.get("role")
    execution = raw.get("execution")
    route = raw.get("route", "inherit-parent")
    requires_runtime = raw.get("requires_runtime", False)
    if not isinstance(role, str) or role not in ROLE_IDS:
        raise RouteValidationError(f"invalid role: {role!r}")
    if not isinstance(execution, str) or execution not in EXECUTION_IDS:
        raise RouteValidationError(f"invalid execution: {execution!r}")
    if not isinstance(route, str) or route not in ROUTE_ALIASES:
        raise RouteValidationError(f"invalid route alias: {route!r}")
    if not isinstance(requires_runtime, bool):
        raise RouteValidationError("requires_runtime must be a boolean")
    if execution == "content-only" and requires_runtime:
        raise RouteValidationError("content-only routes cannot require runtime")
    return Route(role=role, execution=execution, route=route, requires_runtime=requires_runtime)


def content_only_degradation(capability: str) -> CapabilityResult:
    """Return the truthful outcome for a capability this port cannot prove."""
    if not isinstance(capability, str) or not re.fullmatch(r"[a-z][a-z0-9-]*", capability):
        raise RouteValidationError(f"invalid capability: {capability!r}")
    return CapabilityResult(
        status="degraded",
        code="capability_unavailable",
        message=(
            f"pstack-runtime capability '{capability}' is unavailable; preserve the "
            "boundary and report it without substituting an unproven execution mode."
        ),
    )


def resolve_route(
    route: Route,
    *,
    runtime_enabled: bool,
    capability_granted: bool,
    adapter: Callable[[Route], Mapping[str, Any]] | None = None,
) -> CapabilityResult:
    """Describe a native primitive or use an injected test adapter only."""
    if route.requires_runtime and not runtime_enabled:
        return content_only_degradation("runtime-route-config")
    if route.execution == "content-only":
        return CapabilityResult(
            status="ready",
            code="content_only",
            message="content-only route is ready without a runtime adapter",
            execution={"role": route.role, "execution": route.execution, "route": route.route},
        )
    if route.route == "inherit-parent":
        primitive = "delegate_task"
    else:
        if not runtime_enabled:
            return content_only_degradation("runtime-route-alias")
        if not capability_granted:
            return content_only_degradation("approved-route-alias")
        primitive = "delegate_with_route"
    if adapter is None:
        return CapabilityResult(
            status="ready",
            code="native_primitive",
            message=(
                f"native Hermes primitive '{primitive}' is available for this route; "
                "this package does not execute it"
            ),
            execution={
                "primitive": primitive,
                "role": route.role,
                "execution": route.execution,
                "route": route.route,
            },
        )
    response = adapter(route)
    if not isinstance(response, Mapping):
        raise RouteValidationError("adapter result must be a mapping")
    status = response.get("status")
    if not isinstance(status, str) or not status:
        raise RouteValidationError("adapter result requires a status")
    receipt = response.get("receipt")
    if receipt is not None and not isinstance(receipt, str):
        raise RouteValidationError("adapter receipt must be a string")
    return CapabilityResult(
        status=status,
        code=str(response.get("code", "adapter_result")),
        message=str(response.get("message", "adapter returned a local receipt")),
        execution={"role": route.role, "execution": route.execution, "route": route.route},
        receipt=receipt,
    )


def _storage_dir(*, create: bool) -> Path:
    """Resolve active-profile plugin storage without creating it on read paths."""
    from hermes_constants import get_hermes_home

    root = get_hermes_home() / "plugin-data" / "pstack-runtime"
    if root.is_symlink():
        raise RouteValidationError("symlinked plugin storage directory is refused")
    if root.exists() and not root.is_dir():
        raise RouteValidationError("plugin storage path is not a directory")
    if create:
        root.mkdir(mode=0o700, parents=True, exist_ok=True)
        os.chmod(root, 0o700)
    return root


def role_config_path(*, create_storage: bool = False) -> Path:
    """Return the roles file without mutating storage unless a set operation needs it."""
    root = _storage_dir(create=create_storage)
    path = root / "roles.yaml"
    if path.exists() and path.is_symlink():
        raise RouteValidationError("symlinked roles file is refused")
    _contained(path, root)
    return path


def validate_role_config(raw: Mapping[str, Any], *, require_complete: bool = False) -> dict[str, dict[str, str]]:
    """Validate durable role mappings and normalize their ordering for stable writes."""
    if not isinstance(raw, Mapping):
        raise RouteValidationError("role config must be a mapping")
    if set(raw) - {"roles"}:
        raise RouteValidationError("role config only permits the 'roles' mapping")
    roles = raw.get("roles", {})
    if not isinstance(roles, Mapping):
        raise RouteValidationError("roles must be a mapping")
    normalized: dict[str, str] = {}
    for role, route in roles.items():
        if not isinstance(role, str) or role not in ROLE_IDS:
            raise RouteValidationError(f"invalid role: {role!r}")
        if not isinstance(route, str) or route not in ROUTE_ALIASES:
            raise RouteValidationError(f"invalid route alias for {role!r}: {route!r}")
        normalized[role] = route
    if require_complete and set(normalized) != ROLE_IDS:
        missing = sorted(ROLE_IDS - set(normalized))
        extra = sorted(set(normalized) - ROLE_IDS)
        detail = f"missing roles: {', '.join(missing)}" if missing else "unknown role set"
        if extra:
            detail += f"; unknown roles: {', '.join(extra)}"
        raise RouteValidationError(f"complete role mapping required ({detail})")
    return {"roles": dict(sorted(normalized.items()))}


def load_role_config() -> dict[str, dict[str, str]]:
    """Read an explicit role file without creating storage, or return an empty mapping."""
    path = role_config_path()
    if not path.exists():
        return {"roles": {}}
    if path.is_symlink():
        raise RouteValidationError("symlinked roles file is refused")
    import yaml

    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    return validate_role_config({} if raw is None else raw)


def write_role_config(raw: Mapping[str, Any]) -> Path:
    """Atomically replace an explicitly requested local roles file with mode 0600."""
    normalized = validate_role_config(raw, require_complete=True)
    path = role_config_path(create_storage=True)
    if path.exists() and path.is_symlink():
        raise RouteValidationError("symlinked roles file is refused")
    from utils import atomic_json_write

    atomic_json_write(path, normalized, mode=0o600, sort_keys=True)
    if path.is_symlink():
        raise RouteValidationError("symlinked roles file is refused")
    return path


def _route_tool_result(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def _effective_roles(persisted: Mapping[str, str]) -> dict[str, str]:
    return {role: persisted.get(role, DEFAULT_ROLE_MAPPING[role]) for role in sorted(ROLE_IDS)}


def pstack_routes(arguments: Mapping[str, Any]) -> str:
    """Read or replace the complete, local role mapping through a registered tool."""
    try:
        if not isinstance(arguments, Mapping):
            raise RouteValidationError("tool arguments must be a mapping")
        if set(arguments) - {"action", "roles"}:
            raise RouteValidationError("tool only permits action and roles")
        action = arguments.get("action")
        if action not in {"get", "set"}:
            raise RouteValidationError("action must be one of: get, set")
        if action == "get":
            if "roles" in arguments:
                raise RouteValidationError("get does not accept roles")
            persisted = load_role_config()["roles"]
            return _route_tool_result(
                {
                    "ok": True,
                    "action": "get",
                    "persisted": {"roles": persisted},
                    "defaults": {"roles": DEFAULT_ROLE_MAPPING},
                    "effective": {"roles": _effective_roles(persisted)},
                }
            )
        if "roles" not in arguments:
            raise RouteValidationError("set requires a complete roles mapping")
        requested = validate_role_config({"roles": arguments["roles"]}, require_complete=True)
        write_role_config(requested)
        readback = load_role_config()
        if readback != requested:
            raise RouteValidationError("route write readback did not match requested mapping")
        return _route_tool_result({"ok": True, "action": "set", "persisted": readback})
    except (OSError, RouteValidationError, ValueError) as exc:
        return _route_tool_result({"ok": False, "error": "invalid_route_config", "message": str(exc)})



def register(ctx: Any) -> None:
    """Register two explicit role briefs and the one local route-config tool."""
    records = _role_skill_records()
    manager = getattr(ctx, "_manager", None)
    existing = getattr(manager, "_plugin_skills", {})
    collisions = [f"pstack-runtime:{name}" for name, _ in records if f"pstack-runtime:{name}" in existing]
    if collisions:
        raise RouteValidationError(f"runtime role skill collision: {', '.join(collisions)}")
    for name, path in records:
        ctx.register_skill(name, path)
    ctx.register_tool(
        ROUTE_TOOL_NAME,
        toolset=ROUTE_TOOLSET,
        schema=ROUTE_TOOL_SCHEMA,
        handler=pstack_routes,
        description="Read or replace the complete local pstack role-route mapping.",
    )
