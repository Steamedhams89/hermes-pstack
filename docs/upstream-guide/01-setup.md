# Set up pstack

This page explains the package boundary, the versioned install path, optional role settings, and the first task.

## Install the plugin

Hermes plugin packs display their contents before installation and pin every plugin to an exact commit. Review first, then install interactively:

```bash
PACK_URL=https://raw.githubusercontent.com/Steamedhams89/hermes-pstack/v0.14.5-hermes.1/hermes-pack.yaml
hermes plugins pack show "$PACK_URL"
hermes plugins pack install "$PACK_URL"
```

The versioned plugin pack includes the complete 45-skill `pstack` content plugin and the optional `pstack-runtime` companion. It deliberately omits `pstack-benny`; those automation resources remain dormant until an operator separately reviews and authorizes their external integrations.

Installation changes a live profile and requires the operator's deliberate confirmation. Use a disposable `HERMES_HOME` when evaluating the package away from an existing profile.

## Pick your models

Load the setup workflow:

```text
skill_view("pstack:setup-pstack")
```

[`pstack:setup-pstack`](../../packages/pstack/skills/setup-pstack/SKILL.md) works only with provider and route values that the current Hermes environment has actually exposed. It must not guess provider-specific names. Use `clarify` when the operator must choose among detected options.

You only override roles you care about. A role without a setting inherits the parent. An approved route alias can map to `delegate_with_route`; otherwise the workflow uses built-in `delegate_task`. A panel setting controls the number and role of delegates, but it does not promise different model families or hard read-only children unless the current runtime proves those capabilities.

`pstack-runtime` can store validated role configuration, Poteto state, and health information. It is optional. Without it, every content skill can still use Hermes built-in tools directly. The content package does not need the companion to call `delegate_task`, `todo`, `clarify`, `session_search`, or `terminal`.

Any role or plugin configuration changes the active profile and needs explicit current authorization.

## Accept the verification offer, or don't

At the end of setup, `pstack:setup-pstack` looks for an existing way to prove application behavior. If no usable harness or project verification skill exists, it can offer to load [`pstack:create-verification-skill`](../../packages/pstack/skills/create-verification-skill/SKILL.md).

Accepting the offer authorizes investigation and a draft inside the already approved repository scope. It does not authorize writing into a live Hermes skill directory. The generator must use `clarify` if the repository does not establish the target location. It then proves one feature end to end before it calls the draft usable. Decline the offer and setup continues. [Verify and ship](./06-verify-and-ship.md#create-a-project-verification-skill) explains when a verification skill earns its place.

Start a fresh disposable test session after role configuration changes. Restart an active gateway only when that profile is in the approved scope.

## Run your first task

Pick something real but small:

```text
skill_view("pstack:poteto-mode")
Goal: add a --json flag to this command.
Constraint: text output stays byte-identical.
Evidence: run and verify both forms with terminal.
```

Watch `todo`. The first item reads the Principles section. The remaining items come from the matched `feature` playbook. If the playbook skips a step, the item remains visible as `skip: <reason>`.

The selected mode can remain active for the conversation. Say `new task` when the goal changes, and say that you are opting out when you want ordinary Hermes behavior again.

Next: [Route work through `pstack:poteto-mode`](./02-poteto-mode.md).
