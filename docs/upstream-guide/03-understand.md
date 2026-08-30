# Understand the code before changing it

Editing code before tracing it is how subtle regressions ship. pstack gives you four ways in. `pstack:how` explains current behavior. `pstack:why` reconstructs the reason behind it. `pstack:teach` combines both into one explanation. `pstack:recall` rebuilds your recent working context.

![A detective studies a machine blueprint while robots fetch case files; the evidence board links clues under HOW and WHY.](./images/understanding.jpg)

## Trace behavior with `pstack:how`

```text
skill_view("pstack:how")
How do we deduplicate notifications? Is there an N+1 query when we load subscribers?
```

[`pstack:how`](../../packages/pstack/skills/how/SKILL.md) reads the code and explains the runtime flow, key types, and non-obvious behavior. For a large subsystem it can fan out two to four bounded explorers with `delegate_task`. Their briefs prohibit edits, but this guide does not claim a hard read-only sandbox. The parent checks the worktree before it accepts that no files changed. A narrow question usually needs no fan-out.

Ask for Critique mode when you suspect the structure:

```text
skill_view("pstack:how")
Explain the sync service, then critique its ownership boundaries.
```

The explanation comes first, so the critique stays grounded in observed behavior.

## Dig up history with `pstack:why`

```text
skill_view("pstack:why")
Why was the retry limit set to five? Does the reason still hold?
```

[`pstack:why`](../../packages/pstack/skills/why/SKILL.md) begins with source history. It then searches only evidence systems available to the current session, such as an authorized issue tracker, long-form documents, team discussion, observability, error tracking, or analytics. Independent searches can use `delegate_task`. The report cites evidence, separates fact from inference, and records a null result instead of inventing a reason.

The two skills compose. Ask for `pstack:why` first and `pstack:how` second when the history may explain the current structure.

## Actually understand it with `pstack:teach`

```text
skill_view("pstack:teach")
Teach me how this change affects retries. Convince me that it fixes the cause rather than the symptom.
```

[`pstack:teach`](../../packages/pstack/skills/teach/SKILL.md) loads `pstack:how` and `pstack:why`, or only the one a small change needs. It builds a plain explanation from the evidence, one diagram at a time. The "convince me" framing turns the result into an argument you can test rather than a tour.

## Rebuild your own context with `pstack:recall`

```text
skill_view("pstack:recall")
Catch me up on the export work from last week.
```

[`pstack:recall`](../../packages/pstack/skills/recall/SKILL.md) uses `session_search` to find recent conversations in the active workspace. It can combine those results with shared records that the current session is already authorized to read. The output is a brief on the present state and the next likely step. Use the `session-pickup` playbook instead when you need to resume one specific run.

## Take over prior work with Session pickup

When you inherit a branch or working directory, state the takeover contract:

```text
skill_view("pstack:poteto-mode")
Use session-pickup. Read the decision log, find what is complete, and continue from the verified resume point. Do not redo finished work.
```

The [`session-pickup` playbook](../../packages/pstack/skills/poteto-mode/playbooks/session-pickup.md) treats the prior trail as evidence. It uses `session_search` where needed, reconstructs repository state, names the resume point, and checks inherited claims against the original goal.

**Pitfall:** do not skip this page because an agent can read source files. An edit made before a traced model often changes the first plausible symptom. Loading `pstack:how` first is cheaper than repairing the second defect.

Next: [Design the change](./04-design.md).
