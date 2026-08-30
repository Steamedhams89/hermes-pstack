# Build the change and clean the diff

The build playbooks share one discipline. State what you observed and let the playbook demand evidence. This page gives prompts for common build work, then keeps the resulting diff small enough to review.

## Prompt each build playbook with what you know

A defect prompt states the symptom and asks for a reproduction:

```text
skill_view("pstack:poteto-mode")
Goal: this command emits two records after a retry.
Evidence: reproduce the duplicate first, then fix it and verify the retry.
```

A feature prompt states new behavior and what must remain unchanged:

```text
skill_view("pstack:poteto-mode")
Goal: add a --json flag.
Constraint: text output stays byte-identical.
Evidence: run both forms.
```

A refactoring prompt pins behavior before moving structure:

```text
skill_view("pstack:poteto-mode")
Goal: move parsing into one module with no behavior change.
Evidence: record the current output and prove that the output is unchanged afterward.
```

A performance prompt states a measurement:

```text
skill_view("pstack:poteto-mode")
Observation: startup takes 1.8 seconds on this fixture.
Goal: trace and fix the measured cause.
Evidence: show the before and after profiles.
```

These prompts route to [bug-fix](../../packages/pstack/skills/poteto-mode/playbooks/bug-fix.md), [feature](../../packages/pstack/skills/poteto-mode/playbooks/feature.md), [refactoring](../../packages/pstack/skills/poteto-mode/playbooks/refactoring.md), or [perf-issue](../../packages/pstack/skills/poteto-mode/playbooks/perf-issue.md). The playbooks provide the steps you did not type: reproduce before fixing, name the data shape before implementing, pin behavior before restructuring, and profile before optimizing.

For sustained improvement of one number, use [hillclimb](../../packages/pstack/skills/poteto-mode/playbooks/hillclimb.md). Give it the metric, target, and minimum attempt count. It keeps the measurement method fixed, tests one hypothesis at a time, keeps measured wins, and reverts attempts that do not help.

## Write the failing test first with `pstack:tdd`

When a defect has a cheap local test seam, a short prompt is enough:

```text
skill_view("pstack:tdd")
Implement the current fix test-first.
```

[`pstack:tdd`](../../packages/pstack/skills/tdd/SKILL.md) writes the smallest test that fails for the intended reason, implements the fix, and reruns the test. If the seam needs a broad harness or brittle mocks, the workflow says so and uses the closest executable check. Do not force a unit test when a real `terminal` command proves more.

## Let the TypeScript rules load themselves

The Hermes content plugin keeps skill bodies lazy, so no skill silently loads from a filename alone. When the task touches TypeScript, Poteto can load [`pstack:typescript-best-practices`](../../packages/pstack/skills/typescript-best-practices/SKILL.md), or you can load it explicitly:

```text
skill_view("pstack:typescript-best-practices")
Apply these rules to the current TypeScript change.
```

The skill turns the type-system principles into concrete checks: discriminated unions, `unknown` at boundaries, exhaustive variants, and schema-derived types.

## Clean before you commit

The [`opening-a-pr` postlude](../../packages/pstack/skills/poteto-mode/playbooks/opening-a-pr.md) includes a cleanup pass before delivery. You can run that local cleanup before asking for authorization to commit. Use [`pstack:unslop`](../../packages/pstack/skills/unslop/SKILL.md) for prose:

```text
skill_view("pstack:unslop")
Tighten the README changes. Use no em dashes.
```

For code, ask for the preserved outcome in plain words: remove narrating comments, unsupported guards, dead compatibility paths, and unrelated edits. Review the result and rerun the evidence. This guide does not authorize a commit, push, or PR. Obtain explicit current authorization before any of those actions.

## Strip the comments with `pstack:no-comments`

Comments need a pass from someone other than the author:

```text
skill_view("pstack:no-comments")
Review the diff's comments, then fix only the findings supported by the code.
```

[`pstack:no-comments`](../../packages/pstack/skills/no-comments/SKILL.md) uses the preserved [comment-sicko agent prompt](../../packages/pstack-runtime/resources/agents/comment-sicko.md). Built-in `delegate_task` can carry the brief. The optional runtime companion can supply role configuration and health checks, but it is not required.

The keep list is short: license headers, public API documentation, links that explain what code cannot, and behavior forced by an external dependency that cannot be reshaped. Other comments become refactor flags. If a comment claims an invariant, encode the claim as a type, test, or lint when the repository supports one.

The division stays clear. `pstack:unslop` cleans prose. `pstack:no-comments` reviews comments through a fresh role. The ordinary code-cleanup pass removes unrelated or defensive code. None of those steps supplies permission to commit.

**Pitfall:** cleanup is part of proving the change, not decorative polish. Narrating comments and unused compatibility paths hide behavior from a reviewer. Remove them before delivery, then rerun the evidence.

Next: [Verify and ship](./06-verify-and-ship.md).
