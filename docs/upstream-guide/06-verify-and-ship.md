# Verify the result and open a PR

"It compiles" is not evidence. [`pstack:principle-prove-it-works`](../../packages/pstack/skills/principle-prove-it-works/SKILL.md) requires a check against the real artifact. This page covers finish conditions, project verification skills, and the point where local preparation meets an external approval boundary.

![A prototype plane flies a real test course while a stopwatch, camera, and checklist capture the result; the terminal reads verify: pass, evidence: captured.](./images/verification.jpg)

## State the finish condition up front

Put done in the first prompt:

```text
skill_view("pstack:poteto-mode")
Goal: add JSON output to this command.
Constraints: text output stays byte-identical and the JSON parses.
Evidence: run both forms against the sample project with terminal and show the output.
```

That prompt gives the workflow three checks. The final reply must include the exact commands and results. If a check cannot run, the result is `inconclusive`, not success.

Match the check to the change:

- A CLI change runs the real command through `terminal`.
- A UI change walks the changed flow in the running local app.
- A parser or migration replays a saved input.
- A performance change compares before and after profiles.
- A storage change reads back the written value.

For a small diff you do not fully trust, [`pstack:blast-radius`](../../packages/pstack/skills/blast-radius/SKILL.md) identifies what else the change could break. It names the fact that would make the change safe and runs the narrowest executable proof.

## Create a project verification skill

A UI check needs a repeatable way to drive the app. If the repository does not have one, load the generator:

```text
skill_view("pstack:create-verification-skill")
Draft a project-local verification skill for this app. Ask before choosing a target path that the repository does not define.
```

[`pstack:create-verification-skill`](../../packages/pstack/skills/create-verification-skill/SKILL.md) reads the repository to find user-visible features, the local launch path, available drivers, useful evidence, and whether isolated instances can run together. It prefers an existing harness. Other possible local drivers include a verified browser connection, a PTY, or HTTP. It uses `clarify` only for facts the repository cannot answer.

The output has Launch, Doctor, Drive, Evidence, and Cleanup sections plus a feature map. The bundled [feature-map example](../../packages/pstack/skills/create-verification-skill/references/feature-map-example/) has an index and one file per feature. The generator must launch the app, pass the doctor check, drive one feature, capture evidence, and clean up before it calls the draft usable. A failed proof leaves the result blocked.

The generator may write only to a repository-local target already within the task's authority. It must not install the skill into a live profile. Once the draft works, [`pstack:swarm`](../../packages/pstack/skills/swarm/SKILL.md) can use `delegate_task` to split verification by feature-map entry.

## Keep the verification skill honest

When the feature map drifts, load the maintainer:

```text
skill_view("pstack:maintain-verification-skill")
Audit the project verification skill. Do not edit product code or perform external actions.
```

[`pstack:maintain-verification-skill`](../../packages/pstack/skills/maintain-verification-skill/SKILL.md) assigns one bounded source review per feature, then runs one live local pass across the map. It returns exactly one outcome. `clean` means that coverage is current. `changed` means that proven corrections are ready inside the verification skill's own directory. `blocked` names the blocker. A product regression is reported as a regression rather than hidden by a documentation change.

## Open the PR

The [`opening-a-pr` postlude](../../packages/pstack/skills/poteto-mode/playbooks/opening-a-pr.md) can prepare a clean diff, an ordered commit plan, and a draft PR description with evidence:

```text
skill_view("pstack:poteto-mode")
Prepare the opening-a-pr postlude for review. Do not commit, push, or create the PR.
```

Without explicit current authorization, the postlude stops with local drafts. After the operator authorizes specific commit, push, and PR actions, the workflow may perform only those approved actions and return their receipts. Reaching this heading or loading the playbook grants no authority by itself.

Narrow, ordered changes remain easier to review than one growing branch. That design preference survives even when delivery is deferred.

## Drive the PR to merge-ready with Babysit

The [`babysit` playbook](../../packages/pstack/skills/poteto-mode/playbooks/babysit.md) can inspect an authorized PR and classify blockers in order: conflicts, review threads, and CI. A status-only request remains read-only:

```text
skill_view("pstack:poteto-mode")
Use babysit to report the outstanding blockers on the authorized PR. Take no external action.
```

Fixing conflicts changes local code. Pushing a fix, replying to a review thread, dismissing a finding, or restarting an external check changes another system. Each class of external action needs explicit current authorization. If authorized, batch known fixes before one approved push so checks restart once.

When you need only status, ask for only status:

```text
Use babysit to report whether the authorized PR has unresolved reviews or failing checks. Do not modify local or external state.
```

Babysit stops at merge-ready. It never treats green checks as merge approval.

## Land the stack with Shipping

The [`shipping` playbook](../../packages/pstack/skills/poteto-mode/playbooks/shipping.md) verifies each change independently with fresh delegates. The reviewer for a change must not be its author. The workflow then reports the contiguous verified run from the bottom and the first gap.

```text
skill_view("pstack:poteto-mode")
Use shipping to verify this stack and prepare a landing order. Do not merge or deploy.
```

The versioned plugin pack proves source installation, not merge or deployment integration. Shipping therefore stops with evidence and a proposed order. A merge or deployment requires explicit current authorization and a separately verified external adapter. A verified change above an unverified dependency waits.

Next: [Run work while you sleep](./07-overnight.md).
