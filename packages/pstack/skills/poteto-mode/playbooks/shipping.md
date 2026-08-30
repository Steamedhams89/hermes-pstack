<!-- PATCH-HERMES-SKILL-PRIMITIVES -->

> **Native Hermes mapping.** This playbook prepares independently verified review evidence. It does not control Graphite, auto-merge, cloud agents, persistent watchers, or GitHub writes; those require separately authorized ordinary Git/GitHub action.
### Shipping

**You own what lands. Verify each PR independently, land only the verified run from the root, then keep your hands off the queue.** For "land the stack", "ship it", "enable merge when ready", or the second half of a stack that **Babysit** already drove to green.

This is the half after `playbooks/babysit.md`. Babysit gathers review evidence; Shipping decides what evidence is safe to present for an operator-approved integration. Green is not sufficient, and this port does not control a Graphite queue.

1. **Verify every review-ready change independently before any handoff.** Dispatch a read-only/no-write `delegate_task` verifier per change when authorized, using the real available terminal or browser surface. Each returns `PASS`, `PASS+NOTES`, or `FAIL` to the parent; do not post externally without authority.
2. **Land only the contiguous verified run rooted at the bottom.** Walk up from the lowest unmerged PR and stop at the first one without a passing verdict, where both `PASS` and `PASS+NOTES` pass. A verified PR sitting above an unverified one is not landable, because merging it would pull the gap in underneath it. Report the ceiling as a PR number and say what breaks the chain.
3. **Re-check that the verdicts still describe the code.** A restack rewrites every SHA above it and silently invalidates every verdict without touching a single check. Compare `git patch-id` at the verdict SHA against the current head before trusting an older verdict, and re-verify anything that actually drifted. Twenty-one verdicts went stale this way in one run with no signal at all.
4. **Do not arm merge-when-ready from this port.** Graphite queue control is unavailable. Present the verified evidence and required operator action instead.
   ```bash
   No Graphite command is supplied by this Hermes content port.
   ```
5. **Do not enable GitHub auto-merge or mutate stack topology from this playbook.** If the operator explicitly authorizes integration, use ordinary Git/GitHub tooling and verify the resulting state separately.
6. **Do not infer an external queue state from partial metadata.** This port has no queue controller; say when the required external state cannot be verified.
7. **After presenting verified evidence, stop mutating the review sequence.** Diagnose a reported stall from authorized evidence before proposing any action.
8. **Do not claim a persistent drain watcher.** Monitoring beyond the active session requires separately authorized Hermes automation. Report each verified external change only after reading it back.
9. **Stop at the ceiling.** When the verified run is merged, report what landed, what the next unverified PR is, and what verifying it would take. Extending the run is a new pass through step 1, not a judgment call you make at 3am.

**Reply:** the verified run and its ceiling, each PR's verdict and who produced it, what you armed and how you confirmed it, what landed, and what the next gap needs.
