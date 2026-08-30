---
name: setup-pstack
description: "Configure optional pstack route aliases in a reversible local roles file. Use for pstack setup or changing pstack route choices."
---

<!-- PATCH-SETUP-RUNTIME-CONFIG -->

# Setup pstack

Configure an optional, reversible local route policy through the registered
`pstack_routes` tool. The tool stores only its explicit mapping under the active
profile's `plugin-data/pstack-runtime/` root, outside the plugin install tree.
An explicit setup invocation authorizes only that tool's `set` operation. This
port never writes an always-applied host rule and never enumerates provider
model identifiers.

## Route schema

```yaml
roles:
  feature: inherit-parent
  judgment-and-prose: hard
  how-explorer: routine
  why-investigators: x-research
  video-review: video
```

The only valid values are `inherit-parent`, `bounded`, `routine`, `hard`,
`x-research`, and `video`. A `set` request must contain every named role; use
`inherit-parent` explicitly for the defaults. Reject any other value as
`capability_unavailable`; never silently replace it with an unverified provider
route.

## Flow

1. Call `pstack_routes` with `{"action":"get"}`. Read `persisted.roles`,
   `defaults.roles`, and `effective.roles`; this read does not create or update
   a local file. If the tool is absent or returns an error, report
   `capability_unavailable` and retain inherited delegation.
2. Build a complete role map from `effective.roles`. Validate every role and
   alias against the schema above.
3. Use `clarify` only if a selected alias materially changes cost, capability,
   or authority.
4. On this explicit setup invocation only, call `pstack_routes` with
   `{"action":"set","roles":<complete mapping>}`. Require its exact
   `persisted.roles` readback before claiming the mapping changed; the tool
   refuses symlinked storage and uses a mode-safe atomic file replacement.
5. On invocation, workflow skills first call `pstack_routes` for their named
   role. They use `delegate_with_route` only when the selected alias and active
   runtime are both available; otherwise they use `delegate_task` with the
   inherited parent route.

## Verification

Before claiming a route policy applies, validate the file, state the effective
role-to-route mapping, and demonstrate the intended native primitive:
`delegate_task` for inherited work or `delegate_with_route` for an approved
alias. No route policy authorizes a commit, push, pull request, merge,
deployment, external message, credential change, or recurring automation.

## Optional verification skill

If the project needs a real-app proof harness, offer
`skill_view('pstack:create-verification-skill')`. Do not create or modify a
project skill without the operator's approval.
