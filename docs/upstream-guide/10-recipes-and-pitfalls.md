# Recipes and pitfalls

These prompts are worth copying. Replace the sample paths and finish conditions with real ones. The wording stays informal because that is how people type, while the skill and playbook hold the procedure.

![She tastes a finished dish while robots work from a recipe box and pinned cards name HOW, TDD, and a bounded run.](./images/recipes.jpg)

## Understand an unfamiliar subsystem

```text
skill_view("pstack:how")
First explain how initialization works.
Then load pstack:why and find why it broke recently.
```

Mechanics come first, then history. Each report lists the files and evidence sources it searched.

## Get a second opinion on a design

```text
skill_view("pstack:arena")
Treat the current design as one candidate. Compare it with independent alternatives and show the synthesis.
```

The current design becomes one candidate. The result says whether the alternatives improved it or confirmed it.

## Check independent slices in parallel

```text
skill_view("pstack:swarm")
Check every package against its check script. Use one delegate per package and return one report.
```

Each `delegate_task` worker owns one package. The parent waits for every slice and returns one `PASS`, `ISSUES`, or `BLOCKED` report rather than raw child output.

## Review a branch skeptically

```text
skill_view("pstack:interrogate")
Review the whole branch skeptically. Do not edit. Ignore style nits unless they expose a defect or behavior regression.
```

The qualifiers keep the pass focused. The lead sorts findings into action and dismissal groups with reasons. It does not edit automatically.

## Fix a bug through a failing test

```text
skill_view("pstack:poteto-mode")
Reproduce the duplicate write first. If the repository has a cheap public test seam, load pstack:tdd. Then fix and rerun the evidence.
```

The condition matters. A brittle mock can prove less than the real command, and the playbook may choose the executable check.

## Keep a run honest while you're away

```text
Keep working in the owning session until every fixture passes.
Keep a local decision log. Stop and report if the session cannot continue or progress stalls.
Do not commit, push, message, merge, deploy, delete, schedule work, or change a live profile.
```

The full contract is on the [overnight page](./07-overnight.md). If the run must become durable, use `cronjob` only after explicit current authorization for the schedule and its effects.

## Redirect a drifting run

Steering prompts stay short:

```text
The goal is reproduction. Do not implement a fix yet.
```

```text
Apply Prove It Works. Show the real output rather than the build log.
```

```text
skill_view("pstack:unslop")
Tighten that prose. Use no em dashes.
```

Use the right principle name rather than a paragraph. The [principles page](./08-principles.md) is the vocabulary.

## Get the reply in plain words

```text
skill_view("pstack:bro")
Restate the last reply in shorter, plain language.
```

[`pstack:bro`](../../packages/pstack/skills/bro/SKILL.md) restates the last message without jargon. Use it when a technically complete reply still does not tell you what happened.

## The pitfalls

- **Enumerating skills in the prompt.** A hand-written sequence can reorder steps that Poteto already preserves. State the goal and constraints. Name a skill only to override a default.
- **A vague finish condition.** "Make it better" gives a run nothing to check. Name a command or artifact that can pass or fail.
- **Parallel delegates in one worktree.** They overwrite one another. Use one worktree per write-capable delegate.
- **Using `pstack:arena` for coverage.** Arena repeats one brief and synthesizes a base. `pstack:swarm` partitions slices or declared race arms.
- **Accepting every review comment.** Reviewers produce real findings and noise. `pstack:interrogate` records both actions and dismissals with reasons.
- **Treating a route alias as a provider name.** Use only aliases that the current environment has validated. Built-in `delegate_task` is the fallback; `delegate_with_route` is an optional approved enhancement. [Setup](./01-setup.md) explains the role boundary.
- **Reporting success from a green build.** A build proves compilation. Ask for the real command, flow, stored value, or profile and require the receipt.
- **Writing a `SKILL.md` freehand.** Use the [authoring-a-skill playbook](../../packages/pstack/skills/poteto-mode/playbooks/authoring-a-skill.md) so validation and blind review remain part of the work.
- **Confusing a workflow with authority.** Loading a shipping, cleanup, automation, or setup skill does not authorize external actions, deletion, credentials, or a live-profile change. Stop at the boundary and use `clarify`.

That is the guide. If you skipped ahead, return to [setup](./01-setup.md) and run one local task. The habits come from use.

Back to the [guide index](./README.md).
