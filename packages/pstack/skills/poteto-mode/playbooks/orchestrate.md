<!-- PATCH-HERMES-SKILL-PRIMITIVES -->

> **Native Hermes mapping.** The native implementation is bounded, active-session coordination with `todo`, `delegate_task`, scoped files, and evidence receipts. Before route-sensitive owner or verifier work call `pstack_routes` with `{"action":"get"}` and read `effective.roles.feature` or the applicable verification role; unavailable tool/config/route retains inherited delegation. Durable cloud workers, opaque orchestration CLIs, Graphite topology, and automatic reattachment are `capability_unavailable` instead of silently simulated.
### Orchestrate

**You own the program, never the code. Author briefs, drain the queue, keep the frontier green, decide.** For a whole project handed to one standing coordinator chat: multi-day, many stacked PRs, dozens to hundreds of subagents, the human checking in twice a day instead of every five minutes. One task driven to a predicate is Autonomous run. One ambitious run needing a bespoke workflow is figure-it-out. Route here when the work outlives any single agent. Work one agent could finish inside the session's budget is not a program; measured head-to-head, this playbook's ceremony turned a half-hour 12-unit job into 1 landed unit while a plain agent landed all 12. Below that line, route to Autonomous run.

Ceremony must scale with the program. Every gate below prices in coordinator minutes; on cheap near-identical units, collapse it as each section directs rather than paying list price.

Three rules carry the rest.

- Completions are queue events, not interrupts.
- Every spawn and every resume carries the standing orders verbatim.
- The brief is the product. A vague brief fails quietly, because a worker cannot ask you a question.

Open a todolist with the steps below copied in verbatim. A step you skip stays listed with `skip: <reason>`.

#### Roles and placement

- **Coordinator (this chat).** Frames briefs, tracks active work with `todo`, drains bounded child reports, and owns the human report. It may make reversible local changes within scope, but commits, pushes, pull requests, merges, and deployments require separate authority. It uses `delegate_task` directly; no opaque orchestration controller is required.
- **Sub-coordinator.** Use only when the active-session program needs a bounded coordinating child. Give it an explicit track, child budget, scope, permitted writes, and rollup format. It is not durable across sessions and cannot hide child work from the parent.
- **Worker / verifier.** Use `delegate_task` with an explicit scope. Require a native terminal or browser surface only when the task needs it. Do not claim cloud isolation, host transcript access, local-auth inheritance, or per-child model-family isolation.

Depth stays at coordinator, track, worker. Author the track decomposition per project (build, landing, and verification are common cuts, not a required shape); hard-coded swarm trees were tried and parked as too rigid.

#### Store layout

Create a current-session evidence directory only when the operator authorizes a project-local path. Every file has exactly one writer; owners publish facts, readers aggregate at read time. Hermes has no built-in `orch` controller: use `todo` plus ordinary, explicitly permitted local files. If that local storage surface is unavailable, report `capability_unavailable` rather than inventing a controller.

- `preferences.md` is the standing-orders register: numbered lines, one constraint each (model policy, stack shape and count, verification bar, forbidden paths, escalation policy). Paste it verbatim into every spawn and every resume; directives decay across resumes, and each dropped one costs a human turn. When you catch yourself restating an instruction, append the line before you act (principle-encode-lessons-in-structure).
- `overview.md` is the durable PR and issue DB. Append; never rewrite wholesale per event.
- `units.tsv` has one row per unit: id, track, state, branch, PR, head SHA, brief path. Update rows in place.
- `frontier.json` is the computed merge frontier, per Stack safety.
- `ledger.tsv` is the verification ledger, per Verification.
- Completion pointers and human gates stay in explicitly permitted local artifacts or the session `todo`; do not depend on a host-only ask-question state store.
- `decisions.tsv` is the trail via the show-me-your-work skill.
- `status.md` is derived from `units.tsv` and `ledger.tsv` at each drain, never hand-maintained; regenerate it from the tables instead of narrating events into it, because hand-churned boards get rewritten on every event and go unreadable.

#### The brief

Your prompts to agents are your only product, and a sloppy brief compounds into slop across the whole tree. Every spawn carries all of it; a field you cannot fill is a unit you have not scoped yet.

```
GOAL         one sentence, the outcome, executable by a stranger with no chat access
SCOPE        paths this unit may write; paths it may not; its exclusive worktree or branch
CONTEXT      pointers to files and PRs; upstream reports pasted in full when this unit
             depends on them, because workers cannot see siblings
ACCEPTANCE   checkable criteria, one per line
VERIFY       exact commands or the control-skill path, plus known gotchas
TIMEBOX      rough cap on runtime; on expiry, return partial findings and stop rather than run on
FORBIDDEN    no unauthorized topology mutation, rebase, force-push, out-of-scope fix, or external handoff; plus unit-specific bans
REPORT       status, branch, head SHA, PRs, verdict, what you actually ran, deviations,
             suggested follow-ups
STANDING     <preferences.md pasted verbatim>
```

Size the brief to the unit. A one-command unit gets a short brief that still names goal, scope, verify command, and report shape. The active session owns all context; no cloud-specific resume paste is assumed.

A sub-coordinator brief adds its track boundary, unit list, child budget, drain protocol, and rollup format. It does not promise cloud defaults, persistent workers, or automatic resumption.

A dependency is a context relay, not just ordering: undeclared upstream context makes the worker guess. Missing fields are a refuse-to-spawn condition. Audit one sampled worker brief per sub-coordinator per wave, concurrently with the wave it samples, never as a gate in front of it; a failing brief stops that track and fixes the sub-coordinator's instructions, not just the worker, because brief quality decays late in a run. Never resume-chain a brief; respawn fresh with consolidated scope.

#### Steps

1. **Frame.** State the done predicate as something countable ("all 126 units are review-ready with a current verification verdict"). Quantify scope: units, rough effort, expected stacks, and the wall-clock budget. If one agent could finish inside that budget, stop here and run Autonomous run instead. Collapsing must not depend on another document being present: it means do the work directly in this session, plain workers where they help, verification inline, and review-ready evidence as units finish. Name the tracks per project. A contested decomposition or one-way door goes through the arena skill before the pilot. Present the framing once; reversible prep proceeds without waiting.
2. **Initialize the active session.** Open the trail via the show-me-your-work skill, write standing orders before any spawn, and record units and known PRs in `todo` or explicitly permitted local artifacts. A missing authorized artifact surface is `capability_unavailable`; do not run `orch init` or infer a controller.
3. **Pilot.** Push one unit through the whole path: brief, worker, verification, local evidence, and a review-ready report. The pilot exists to falsify the brief template, the verify recipe, and the unit size while that costs one agent instead of fifty. Fix the contract from pilot evidence before any fan-out. A dedicated pilot pipeline (separate verifier agent, audit gate) is for expensive or novel unit shapes, not for clone-units where a serialized pilot has nothing to falsify. Any commit, push, PR, reply, merge, or deletion still requires explicit current authorization and its exact readback.
4. **Scale.** Spawn a bounded active-session window of workers up to the in-flight cap, refilling only as child reports arrive in this session. Spawn track sub-coordinators only past the one-drain threshold in Roles. Recompute ready work after each drain; relay upstream reports into downstream briefs; keep sibling communication upward only. The sampled brief audit runs alongside the wave it samples and stops the next refill on failure, not the current one.
5. **Drain.** Run the queue discipline below at each active-session drain point.
6. **Report review-ready units.** Never auto-land. Keep local evidence current as units verify and report the exact review-ready head SHA. Integration is an external action requiring explicit current authorization and readback; never advance a frontier from an assumed merge.
7. **Close.** Drain the final inbox, reconcile every spawned agent to a terminal row (done, abandoned, zombie-reconciled), confirm the predicate on the real artifact, confirm every review-ready PR has a verdict for its current head SHA, audit the trail per show-me-your-work including its bounded review, and encode recurring corrections into standing orders or the brief template. Leave authorized local evidence intact; it is the postmortem.

#### Queue and drain

- On a completion notification, record the status in `todo` or an explicitly permitted local artifact and return to current work. Never deep-review inline; a completion that needs review becomes a verifier unit. Never review a diff inside a drain.
- Drain in batches at the end of a critical section, a track rollup, a manual active-session re-entry, and before a human report. A persistent frontier watcher or loop command is `capability_unavailable` unless separately authorized and proven.
- Critical sections you finish first: authoring a brief, a stack operation, a conflict decision, writing a gate, updating local evidence.
- Each drain classifies every pointer (review-ready, needs-verify, failed, zombie, noise), updates `todo` or permitted evidence, then spawns the next bounded wave in one message.
- Account for every spawned child at its track's rollup: arrived, respawned, or its scope explicitly absorbed. Silently redoing a missing child's work hides both the wasted spend and the coverage gap its result existed to close.
- A drain turn ends with counts, what changed, and open gates from current `todo` and evidence. The full reply contract applies at checkpoints and close.

#### Stack safety

- Keep any review ordering as a local, evidence-backed list. Graphite frontier computation and stack metadata are unavailable in this port; do not infer remote topology.
- Exactly one coordinator may propose ordering changes. Do not run Graphite or automatic restacks from this content-only playbook; report the required authorized Git/GitHub action instead.
- Workers do not rebase, force-push, or mutate review topology unless separately authorized. Babysitting remains a scoped evidence activity, not stack control.
- PR closes and retargets require explicit current authorization and exact GitHub readback; closing a base PR can orphan every chain above it. Merges and stack surgery are separate authorized actions with bounded briefs.
- A retro watcher is `capability_unavailable` unless separately authorized recurring automation is installed and behavior-tested. Record a manual follow-up point instead.

#### Verification

Scale verification to the unit. When VERIFY is a single cheap command, the worker runs it and reports the output, and the coordinator spot-checks receipts; a dedicated verifier is for units whose verification is expensive, judgment-laden, or high-blast-radius. This port makes no model-family or provider-diversity claim; use only an actually configured route or inherited delegation. A verifier whose entire product would be rerunning one command is ceremony, not verification.

Keep one locally readable verdict per PR/head SHA in `todo` or explicitly permitted evidence: `live-ui-verified | unit-test-verified | type-check-only | verifier-blocked | verifier-failed`. CI green is an input to a verdict, not a verdict. Behavioral work needs better than `type-check-only`. `verifier-blocked` is not a pass; respawn when the environment heals. `verifier-failed` gets a fix unit, not a re-verify. A worker may self-report; a verifier overrides it on the same key. A new head SHA voids the record, so re-verify after a reported authorized update. The record answers "was this verified", not memory and not the transcript.

A unit is not done until its result has local evidence and a review-ready report. A worker never pushes its branch or creates an external receipt without explicit current authorization; after any authorized write, read back the exact remote state.

#### Liveness and failure

- Do not claim a host resume/status channel. Check only explicit child results, `todo`, and authorized local or GitHub evidence. If liveness cannot be observed, report `capability_unavailable`.
- A silent death gets a synthetic postmortem row in the inbox (unit, failure mode, last evidence, options). Replan on evidence as it arrives; never wait for full quiescence.
- Retry by mode: cap-hit or oom, respawn with smaller scope; network-drop, retry as-is; tool-error, retry only through the configured named route if available, otherwise inherit-parent; unknown, retry once. Two retries, then abandon the unit and replan around it.
- A zombie that returns hours late reconciles against the current frontier and ledger before anything is accepted; the world moved while it slept. Salvage unique findings through a fresh unit, never a blind merge.
- When continued spawning would produce garbage tree-wide (bad upstream output, broken acceptance, dead infra), write a stop line at the top of the standing orders, let in-flight work finish, fix the cause, clear it.
- Bound your own infra retries the same way you bound a child's. After a few consecutive tool aborts, stop retrying: write a terminal handoff to durable state (what is done, where it lives, the exact command to resume) and end the run. Hours of retry loops against a dead executor produce nothing a handoff would not.
- After a Hermes restart, treat child continuity as unavailable unless the actual session evidence proves otherwise. Re-read the standing brief, local artifacts, and `todo`; never claim a cloud worker survived or can be reattached.

#### Escalation

Reaches the human, batched into the status page rather than per item: irreversible actions (force-push to shared branches, deploys, deletions, closing someone else's PR), genuine product or preference calls no experiment settles, a standing order that contradicts observed reality, a program-level dead end that survived a replan. Park each as a `gates.md` entry before asking, and route work around it.

Never reaches the human: frontier nudges, restack mechanics, retries, CI flake triage, review-thread triage, format fixes, scope the brief already forbids (refuse and continue), and "should I keep going". When in doubt, act and log; deferring is the measured failure mode.

Mid-run discoveries fix only what blocks the frontier. Everything else parks in follow-ups; at this fan-out a small scope leak multiplies into PRs nobody asked for.

**Reply:** at checkpoints and close: the predicate and the count against it from `units.tsv` and `ledger.tsv`, tracks and what each landed, the frontier (PR list plus SHAs), verdicts summary, what was abandoned and why, gates awaiting the human (the only asks), the store path, and the trail path. Numbers from the tables, not narrative. Include PR links.
