<!-- PATCH-HERMES-SKILL-PRIMITIVES -->

> **Native Hermes mapping.** An autonomous run continues in the active session and approved scope. A recurring wake or external handoff requires its own current authorization; unavailable persistence is reported as `capability_unavailable`.
### Autonomous run

**You own the exit condition. Define done, then drive to it within the active session and approved scope.** For "going to bed" or "run until done".

1. State the exit condition as a checkable predicate before the first iteration (tests green, repro fixed, all N PRs merged, pixel-diff zero). A vague goal stalls; a predicate lets you stop.
2. Continue in the active session while the user-approved scope remains live. Do not create a scheduler, watcher, or recurring wake without explicit recurring-automation authorization. If the task cannot honestly continue after this session, report `capability_unavailable` with the next manual re-entry point.
3. Each iteration makes the smallest change the evidence justifies, verifies it against the predicate, commits if it advanced, discards changes that didn't help. Belt-and-suspenders that "might help" gets reverted, not left to ride.
   Sequence the work via the **sequence-verifiable-units** principle skill, verifying each unit before the next instead of batching checks at the end.
4. Mid-run reversible discoveries are yours within the approved scope. Address broken skills, related bugs, flaky verifiers, review noise, tooling failures, orphaned follow-ups, and fixable drift when permitted. Keep external handoffs and irreversible actions behind their normal authority gates; use `clarify` only for a genuine product or preference call no experiment can settle.
5. Checkpoint every iteration via the **show-me-your-work** skill, a row for what changed and whether the predicate moved. A run with no trail can't be audited or resumed.
6. Stop when the predicate is met. A plateau is not a stop, so keep going and pivot your approach to push past it. Surface a genuine dead end rather than spinning, and never relax the predicate to declare victory.

**Reply:** the exit condition, iterations run, what landed, what was discarded, final predicate state.
