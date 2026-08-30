# Steer with principle names

pstack ships 21 principles as first-class qualified skills. `pstack:poteto-mode` reads the relevant principle content at the start of a multi-step task, applies triggered rules, and names each rule with the decision it changed.

You usually steer by principle name rather than loading each skill yourself. When you need the full rule, load its exact qualified identity with `skill_view`.

## Steering in practice

If an agent is about to add another adapter beside obsolete ones, say:

```text
Apply Subtract Before You Add. Remove obsolete adapters first, then design what remains.
```

If it claims success from a build, say:

```text
Apply Prove It Works. Run the real import flow and show the written records.
```

If parallel attempts would write to one branch, say:

```text
Apply Separate Before Serializing Shared State. Give every attempt its own worktree.
```

The agent must name the decision the principle changed. A citation without a changed decision is name-dropping, not application.

## The 21, briefly

The core principles decide how much to build and when to rethink the design:

- [Laziness Protocol](../../packages/pstack/skills/principle-laziness-protocol/SKILL.md), `pstack:principle-laziness-protocol`, prefers deletion and the smallest change that solves the problem.
- [Foundational Thinking](../../packages/pstack/skills/principle-foundational-thinking/SKILL.md), `pstack:principle-foundational-thinking`, chooses the core data structures before logic.
- [Redesign from First Principles](../../packages/pstack/skills/principle-redesign-from-first-principles/SKILL.md), `pstack:principle-redesign-from-first-principles`, integrates a new requirement as if it had existed from the start.
- [Subtract Before You Add](../../packages/pstack/skills/principle-subtract-before-you-add/SKILL.md), `pstack:principle-subtract-before-you-add`, removes dead weight before adding code.
- [Minimize Reader Load](../../packages/pstack/skills/principle-minimize-reader-load/SKILL.md), `pstack:principle-minimize-reader-load`, reduces layers and hidden state.
- [Outcome-Oriented Execution](../../packages/pstack/skills/principle-outcome-oriented-execution/SKILL.md), `pstack:principle-outcome-oriented-execution`, moves a rewrite toward the target design without preserving temporary compatibility states.
- [Experience First](../../packages/pstack/skills/principle-experience-first/SKILL.md), `pstack:principle-experience-first`, chooses the user's result over implementation convenience.
- [Exhaust the Design Space](../../packages/pstack/skills/principle-exhaust-the-design-space/SKILL.md), `pstack:principle-exhaust-the-design-space`, builds competing prototypes when precedent does not answer the design question.
- [Build the Lever](../../packages/pstack/skills/principle-build-the-lever/SKILL.md), `pstack:principle-build-the-lever`, creates a script that does or proves repeatable work.

The architecture principles decide where state, validation, and compatibility live:

- [Model the Domain](../../packages/pstack/skills/principle-model-the-domain/SKILL.md), `pstack:principle-model-the-domain`, encodes repeated rules in one structure.
- [Boundary Discipline](../../packages/pstack/skills/principle-boundary-discipline/SKILL.md), `pstack:principle-boundary-discipline`, validates at the boundary and trusts internal types.
- [Type System Discipline](../../packages/pstack/skills/principle-type-system-discipline/SKILL.md), `pstack:principle-type-system-discipline`, makes illegal states unrepresentable.
- [Make Operations Idempotent](../../packages/pstack/skills/principle-make-operations-idempotent/SKILL.md), `pstack:principle-make-operations-idempotent`, makes retries converge on one end state.
- [Migrate Callers Then Delete Legacy APIs](../../packages/pstack/skills/principle-migrate-callers-then-delete-legacy-apis/SKILL.md), `pstack:principle-migrate-callers-then-delete-legacy-apis`, migrates callers and removes the old API in one wave.
- [Separate Before Serializing Shared State](../../packages/pstack/skills/principle-separate-before-serializing-shared-state/SKILL.md), `pstack:principle-separate-before-serializing-shared-state`, removes sharing before it adds coordination.

The verification principles define proof:

- [Prove It Works](../../packages/pstack/skills/principle-prove-it-works/SKILL.md), `pstack:principle-prove-it-works`, verifies the real artifact rather than a proxy.
- [Fix Root Causes](../../packages/pstack/skills/principle-fix-root-causes/SKILL.md), `pstack:principle-fix-root-causes`, reproduces and traces the cause before changing code.
- [Sequence Work into Verifiable Units](../../packages/pstack/skills/principle-sequence-verifiable-units/SKILL.md), `pstack:principle-sequence-verifiable-units`, ends each small unit with a check.

The delegation principles keep parallel work reviewable:

- [Guard the Context Window](../../packages/pstack/skills/principle-guard-the-context-window/SKILL.md), `pstack:principle-guard-the-context-window`, routes bulk reading through `delegate_task` and keeps compact findings in the parent.
- [Never Block on the Human](../../packages/pstack/skills/principle-never-block-on-the-human/SKILL.md), `pstack:principle-never-block-on-the-human`, proceeds on safe reversible work and uses `clarify` only when a decision or authority boundary needs the operator.

One meta principle completes the set:

- [Encode Lessons in Structure](../../packages/pstack/skills/principle-encode-lessons-in-structure/SKILL.md), `pstack:principle-encode-lessons-in-structure`, turns repeated advice into a lint, check, type, or script.

Do not memorize the list. Return when the work drifts and use the name that points to the missed decision.

Next: [Make it yours](./09-make-it-yours.md).
