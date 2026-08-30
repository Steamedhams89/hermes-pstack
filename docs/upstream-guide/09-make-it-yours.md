# Make it yours

Poteto captures one working style. The playbooks, routing, and role briefs can support yours too. This page covers drafting a personal mode, capturing lessons from a session, authoring a focused skill, and testing a skill change before you trust it.

## Generate your own mode with `pstack:automate-me`

```text
skill_view("pstack:automate-me")
Draft a mode from repeated preferences in my recent work. Ask me to confirm each proposed rule.
```

[`pstack:automate-me`](../../packages/pstack/skills/automate-me/SKILL.md) uses `session_search` over the active workspace to find repeated preferences in replies, delegation, verification, code, prose, and process. It presents candidate patterns through `clarify` so the operator can separate a durable preference from one unusual session.

The workflow drafts a repository-local `SKILL.md` at a target that the current task has authorized, then loads [`pstack:unslop`](../../packages/pstack/skills/unslop/SKILL.md) and validates the links and frontmatter. It does not write to a live profile, commit, push, or open a PR without explicit current authorization.

Run it again when your habits change:

```text
skill_view("pstack:automate-me")
Update the draft mode with evidence since its last edit. Keep rules that the newer sessions do not contradict.
```

Update mode uses only the later history, revises rules with new evidence, and adds a section only for a genuinely new pattern.

## Capture a session's lessons with `pstack:reflect`

After a task teaches you something, load the reviewer:

```text
skill_view("pstack:reflect")
That took too long. Extract lessons that would change a future decision.
```

[`pstack:reflect`](../../packages/pstack/skills/reflect/SKILL.md) can send the transcript to three bounded reviewers with `delegate_task`. A synthesizer sorts proposals into `Accepted`, `Rejected`, and `Backlog`, then uses `clarify` before any local skill edit. Approve a proposal only if it changes a future decision. One strange session is evidence to inspect, not a rule.

## Author a focused skill

When you already know the workflow, route the authoring task:

```text
skill_view("pstack:poteto-mode")
Use authoring-a-skill to draft a skill for verifying database migrations in this repository.
```

The [authoring-a-skill playbook](../../packages/pstack/skills/poteto-mode/playbooks/authoring-a-skill.md) drafts the skill, validates frontmatter and links, and prepares local delivery material. Agent-facing prose needs a high bar because a vague sentence becomes a future instruction. The playbook does not invent a target or change installed skills. Use `clarify` when the repository has no approved skill location.

A skill that drives an app and proves behavior has a narrower generator. Use [`pstack:create-verification-skill`](../../packages/pstack/skills/create-verification-skill/SKILL.md) and [`pstack:maintain-verification-skill`](../../packages/pstack/skills/maintain-verification-skill/SKILL.md). [Verify and ship](./06-verify-and-ship.md#create-a-project-verification-skill) covers both.

## Write docs to a standard with `pstack:technical-writing`

Use the writing standard for docs, RFCs, READMEs, draft PR descriptions, and draft commit messages:

```text
skill_view("pstack:technical-writing")
Review the README changes as a how-to. Preserve the commands and warnings.
```

[`pstack:technical-writing`](../../packages/pstack/skills/technical-writing/SKILL.md) chooses the document mode first, then checks each sentence for a named actor, one thought, plain words, and one reading. The skill also loads `pstack:unslop` for its final pass. A polished PR description or commit message remains a draft until its external action receives authorization.

## Test a skill change blind

A skill edit affects future sessions, so test it as an experiment:

```text
skill_view("pstack:poteto-mode")
Use eval on this skill change. Give both variants the same organic task in separate sanitized directories, and keep each candidate blind to the comparison.
```

The [`eval` playbook](../../packages/pstack/skills/poteto-mode/playbooks/eval.md) controls the observer effect. Candidate delegates receive the same ordinary-looking task through `delegate_task`. They do not see evaluation labels or each other's output. One judge scores neutral labels, and chain-following is measured from files read rather than from self-report.

Read every output before accepting the verdict. If your judgment and the score disagree, inspect the rubric first.

`pstack-benny` is not a shortcut for this evaluation. Its three procedures remain dormant resources for a separately authorized event plane. No test here enables recurring automation, credentials, issue updates, or external delivery.

**Pitfall:** do not edit a skill in the middle of unrelated feature work. Keep the draft and its evaluation in a separate reviewable change. Any commit, push, PR, live-profile edit, or scheduled evaluation still needs explicit current authorization.

Next: [Recipes and pitfalls](./10-recipes-and-pitfalls.md).
