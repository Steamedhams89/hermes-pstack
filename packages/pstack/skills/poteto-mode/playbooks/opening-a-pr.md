<!-- PATCH-HERMES-SKILL-PRIMITIVES -->

> **Native Hermes mapping.** This is a local review-handoff checklist. Use explicit sibling skills and ordinary Git/GitHub only after current authorization; no cloud PR tool, Graphite command, commit, push, or pull-request creation is implied.
### Opening a PR

Invoked at the end of every other playbook.

**Worktree.** Work from a git worktree when the current approved scope needs one. Bounded `delegate_task` children receive their permitted workspace explicitly; do not assume host-created worktrees.

**Commits.** Commit liberally; rebase into small, ordered commits before opening PRs. Each commit is a future PR: landable, ordered to tell the story. Amend when the fix belongs in a just-made commit; new commit when separable.

**Review prose.** Run `skill_view(name='pstack:unslop')` over the diff before proposing a pull request. Run `skill_view(name='pstack:no-comments')` before review. Write any title, description, or commit body with `skill_view(name='pstack:technical-writing')`, then apply `skill_view(name='pstack:unslop')`. Do not commit, push, create a pull request, or publish without separate authorization.

**Titles.** Use Conventional Commits in the form `type(scope): subject`. Use `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, or `perf` as the type. Use the changed area, such as `pstack` or `poteto-mode`, as the scope. Keep the subject short and imperative. Apply the same `skill_view(name='pstack:technical-writing')` and `skill_view(name='pstack:unslop')` pass as the body. Name a real symbol when one carries the change. For example, `fix(pstack): retarget opening-a-pr babysit trigger`. Do not add a trailing period.

**Descriptions.** Use these sections in order. Drop a section when it is empty.

- `## Why`. State the intent and why this approach fits.
- `## Scope`. State facts from the diff. Name real symbols and paths. Name both sides of a rename or retarget. State what is in and out when the boundary matters.
- `## Tradeoffs`. State real choices only. Skip this section when there are none.
- `## Blast Radius`. State who and what the change touches. Explain why the change is safe or risky. If main is red without the fix, name the continuing cost.
- `## Verification`. State how you ran each check and its rigor. Name the real native path, such as terminal, browser, or targeted tests. State each outcome, not only the command name.

After these sections, attach videos or screenshots when they prove a claim. Do not use `## Summary` or `## Test plan` boilerplate. A commit body does not restate its subject.

**Size and ordered review.** Prefer five narrow review units to one large one. Preserve their dependency order in local evidence. Graphite operations and remote stack mutation are outside this content-only port unless separately authorized.

**Readiness.** Prepare every pull request with complete evidence. This port does not invoke a hosted PR controller or a host-specific ready command; use authorized ordinary Git/GitHub tooling only after the operator approves the external action.

**Babysit.** Opening a PR does not start a babysit. Post the URL and keep building. Finish the phase or stack first. Run a separate babysit pass only when the user asks for one after the whole stack exists. A babysit for each new PR stalls the build and spends checks on commits that later waves restart. Push back when feedback drifts from intent.

A subagent that proposes a PR calls `skill_view(name='pstack:interrogate')`, `skill_view(name='pstack:unslop')`, and `skill_view(name='pstack:no-comments')`. It returns the local review-handoff evidence; an external PR URL exists only after separately authorized creation and exact GitHub readback. Return to the parent.
