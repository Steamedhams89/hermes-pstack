---
name: reflect
description: Spawn three parallel review subagents over the active transcript, surface learnings, and route each to a concrete edit on an existing skill. Use when the user says reflect.
disable-model-invocation: true
---

<!-- PATCH-HERMES-SKILL-PRIMITIVES -->

> **Native Hermes mapping.** Read active-session evidence with `session_search`, dispatch bounded no-write reviewers with `delegate_task`, and edit skills only through approved `skill_manage` work. Before each lens, call `pstack_routes` with `{"action":"get"}` and read `effective.roles.reflect-judgment`, `effective.roles.reflect-tooling`, `effective.roles.reflect-divergent`, or `effective.roles.reflect-synthesizer`; unavailable tool/config/route retains inherited `delegate_task`. Route aliases are optional runtime descriptors, not provider model selectors; an unavailable route is `capability_unavailable` rather than a generic serial substitute.

# Reflect

Mine the current conversation for durable learnings, then route them into skill edits.

## When to invoke

- The user said "reflect" or "/reflect".
- A complex task (5+ tool calls) just landed cleanly and the recipe is worth keeping.
- The agent hit dead ends, found the working path, and the path generalizes.
- The user corrected the agent's approach mid-task.
- A non-trivial workflow emerged that isn't captured anywhere.

Skip when the conversation is trivial, off-topic, or already covered by an existing skill the parent followed correctly. One-offs are not learnings.

## Process

### 1. Locate active-session evidence

Use `session_search` for the active Hermes session, then read the opening request, decision points, and relevant tool evidence. If the session evidence is unavailable, prepare a tight parent-authored digest and state that limitation. Do not glob host transcript directories or cross workspace boundaries.

### 2. Dispatch three reviewers in parallel

Dispatch the judgment, tooling, and divergent reviewers together with bounded no-write `delegate_task` briefs. Use the inherited parent route by default; only use a separately approved runtime alias through `delegate_with_route`. Pass each preserved reference template and the scoped session evidence or digest. Reviewers return findings to the parent and do not receive implicit MCP, file-write, sandbox, or provider-model guarantees.

| Lens | Route | Prompt template |
|---|---|---|
| Judgment | `inherit-parent` or approved `hard` alias | `references/judgment-reviewer.md` |
| Tooling | `inherit-parent` or approved `routine` alias | `references/tooling-reviewer.md` |
| Divergent | `inherit-parent` or approved `hard` alias | `references/divergent-reviewer.md` |

### 3. Synthesize

Dispatch one bounded no-write `delegate_task` synthesizer after reviewers return. It receives `references/synthesizer.md`, the reviewer findings, and the evidence references. Use `inherit-parent` or an approved `hard` alias. It returns a structured Accepted / Rejected / Backlog list; it does not modify files or claim an external lookup succeeded without evidence.

### 4. Structural enforcement check

Sanity-check the synthesizer's Accepted list. For any item that would be enforced more reliably by a lint rule, script, metadata flag, or runtime check, move it from Accepted to Backlog. The synthesizer already applies this criterion; this is a final pass before edits land. See the **encode-lessons-in-structure** principle skill.

### 5. Apply

Before applying any Accepted edit, present the synthesizer's full Accepted/Rejected/Backlog output to the user and wait for explicit approval. The user picks which subset to apply and may redirect routings. Skill changes affect every future agent in the org; do not auto-apply.

Report backlog items for the operator's chosen tracker. Do not create tracker submissions from this content-only workflow. Only the Accepted list waits for approval.

For each approved Accepted item, follow the Routing field exactly:

- Trivial existing-skill edit (a one-line bullet, a tightened sentence, a stale fact corrected): parent does directly.
- Substantive existing-skill edit (a new section, a new pattern table, more than ~10 lines): draft the intended change, obtain approval, then use `skill_manage` and run its applicable validation loop.
- `tune description: <skill path>` (the skill exists but did not trigger when it should have): draft and approve the description change through `skill_manage`.
- `new skill: <kebab-name>`: draft the trigger and behavior, obtain approval, then create it through `skill_manage`. Do not invent the shape ad hoc.

If your environment ships a SKILL.md validator, run it on every touched skill before declaring done. Skip this step if it doesn't.

### 6. Summarize for the user

Short list, no preamble:

- Edits applied: `<skill path>`. What changed, one line each.
- New skills created: `<skill path>`. One line each (rare).
- Backlog filed to the devex tracker: `<issue title>` (`<tags>`). One line each.
- Dropped: one line per rejected finding + reason from the synthesizer.
