<!-- PATCH-HERMES-SKILL-PRIMITIVES -->

> **Native Hermes mapping.** Use `skill_view('pstack:how')` and `skill_view('pstack:why')` for investigation. A stubborn hunt continues only in the active session unless separate recurring automation is approved.
### Bug fix

**You own this task. Plan, review, verify.** Delegate investigation and the fix to subagents, stay in the lead.

Be scientific. Every shipped line traces to runtime evidence. Belt-and-suspenders that "might help" is a hypothesis, not a fix; it does not ship. When evidence refutes a hypothesis, revert what it motivated. The smallest change the evidence justifies ships, nothing more. Same discipline for Perf, where the evidence is the trace.

1. Reproduce it yourself on the matching native terminal, browser, or desktop surface. Do not hand the repro to the user. A debug or instrumentation protocol that says to ask the user does not override this; you drive the instrumented runtime. Ask the user only with a stated, specific reason no available native surface can reach the target, and only after driving it as far as it goes. If it will not reproduce directly, synthesize the trigger, tighten conditions, or instrument until it fires. A bug you cannot reproduce, you cannot prove fixed.
2. Binary-search the cause. Form the candidate hypotheses, then rule them out until one survives. Seed them with `skill_view('pstack:how')` over the affected subsystem and `skill_view('pstack:why')` for regression history. Each pass, take the split that cuts the most remaining problem space, get runtime evidence, eliminate. When program state is unclear, add instrumentation or logging and read it as the code runs. Don't guess. Drive a long or stubborn hunt within the active session; do not create a recurring loop without separate authorization. Confirm the surviving *mechanism* with runtime evidence before the step-3 architect/interrogate fan-out; a design grounded on a plausible-but-unconfirmed cause can be unanimously wrong while the real cause sits one subsystem over.
3. Plan the fix. If it crosses a function boundary, `skill_view('pstack:architect')` first. Delegate implementation with `delegate_task` on the inherited route and a specific permitted scope; use `delegate_with_route` only for a separately approved alias. Review the diff yourself.
4. Verify on the same surface; the original repro now passes. "Inconclusive" or wrong-surface is not a pass; flag it. Unit tests show branch behavior, not bug absence.
5. Stage a local review sequence so the failing repro precedes the fix in git history when version-control work is separately authorized; the diff tells the story. See `skill_view('pstack:tdd')` for the failing-test-first cadence when the bug has a cheap local test path; skip it when the test would be expensive, integration-heavy, or unclear.
   This is the canonical **sequence-verifiable-units** principle skill, the failing test first and the fix on top.
6. Prepare the local review evidence through `playbooks/opening-a-pr.md`. Creating or updating a pull request remains separately authorized.

Investigation fans out `how` + `why` as parallel subagents.

**Reply:** what was broken, root cause, fix, how you verified. Paste failing-then-passing repro output verbatim.
