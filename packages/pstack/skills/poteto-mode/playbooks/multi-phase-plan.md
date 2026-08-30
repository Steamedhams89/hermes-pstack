<!-- PATCH-HERMES-SKILL-PRIMITIVES -->

> **Native Hermes mapping.** Program coordination is native `todo` plus bounded `delegate_task` work. Before route-sensitive owner work, call `pstack_routes` with `{"action":"get"}` and read `effective.roles.feature`; an unavailable tool/config/route keeps inherited delegation. This port does not create cloud VMs, persistent active-session state, scheduled audit ticks, or Graphite stacks; those needs are explicitly degraded until separately authorized.
### Multi-phase or multi-PR plan

**You own the plan, not the code. The plan is a checklist an owner runs box by box and the operator audits from the evidence.** For work that spans phases or stacked PRs. The plan is the deliverable. Do not implement.

1. When the change is one or two files with an obvious approach, skip the plan. Say so and stop.
2. Settle open questions by prototype before you write. For a question about layout, timing, behavior, or whether an API works, run `playbooks/prototype.md`. Keep the branch, the SHA, and the screenshots for Appendix A. Ask the operator only about a product or preference call that no run can settle. Give options (the **never-block-on-the-human** principle skill).
3. Explore with bounded `delegate_task` children. Load `skill_view('pstack-runtime:poteto-agent')` when available and include its brief; otherwise state the degraded role path. Each child returns file pointers, conventions, test commands, and entry points. No inlined dumps.
4. Copy the skeleton below into the plan file and fill every placeholder. Unless the operator names a path, write the file under the agent store's `docs/`. Keep every heading and every sub-block in the order shown. One section per PR. One PR is one change with its own evidence (the **sequence-verifiable-units** principle skill). Name the execution playbook in **How to read this**. Pick between `playbooks/autopilot-full.md` and `playbooks/autopilot-stack.md` per the rule at the end of `playbooks/autopilot-stack.md`. A standing program takes `playbooks/orchestrate.md`.
5. Write with `skill_view('pstack:technical-writing')`, then `skill_view('pstack:unslop')`. The body is one Diátaxis mode, how-to. Appendices hold explanation and reference. Two rules apply verbatim. "i dont want any abstract metaphors" and "write like hemingway". Each heading states the task or finding. No long dashes. No mid-sentence colons.
6. Run the packaged `check-plan.mjs` helper against `<plan.md>` and fix every line it prints (the **encode-lessons-in-structure** principle skill). It enforces the skeleton's shape, the verification rule in every verification block, and the punctuation rules.
7. Hand back. Post the plan path and the script's output, then stop. Execution starts on the operator's explicit go, under the execution playbook the plan names.

**Verification.** Tests alone are not sufficient verification. A review unit is verified only when its unit, live, and perf boxes are all checked (the **prove-it-works** principle skill). That sentence is the verification rule. Every verification block opens with it. The live block is mandatory. Ten native evidence lanes at the review head drive the real surface through the available terminal, browser, or desktop capability, per `skill_view('pstack:swarm')`. Each lane is one box with a concrete scenario, the screenshot it saves, and its pass predicate. The perf block names the metric, the probe, the trunk baseline measured first, and the rule with the number that fails. A review unit that changes an interaction is review-gated. The operator reviews it in chat with screenshots and a video before any separately authorized merge. A review unit that changes no interaction writes `**Review gate.** None. <review id> is not review-gated.` and no boxes under it.

**Native surface.** Use the Hermes terminal for CLI/TUI checks and the available browser or desktop surface for web, Electron, or UI checks. A surface with no native driver is a risk in Appendix C, and its live block names the manual evidence required.

````markdown
# <Program> plan

<Under ten lines. What changes, for whom, the rule the program enforces, and the PR ids in order.>

## How to read this

One box is one unit of work. Every box names the evidence that checks it. A nested box is a sub-step of the box above it. Check a box only when its evidence exists, a file, a log line, a screenshot, a test run, or a SHA. The body is a how-to. The appendices explain and record.

The program uses the selected Poteto playbook and explicit loads of the exact qualified skills it names. <Who decides any merge, and which review ids are the operator's items that stop at review-ready.>

Tests alone are not sufficient verification. A review unit is verified only when its unit, live, and perf boxes are all checked.

## Program checklist

### Arm the program

- [ ] State the protocol and this plan to the operator, then stop. Start execution only on her explicit go.
- [ ] On her go, record the approved objective in `todo` for this active session. It does not survive as sticky continuation.
- [ ] Read the selected execution playbook and required sibling skills from the installed plugin at program start. Re-read them at each manual re-entry or separately authorized tick.
  - [ ] For example: `skill_view(name='pstack:poteto-mode', file_path='playbooks/feature.md')`; choose another existing file under `playbooks/` only when that is the selected playbook.
  - [ ] `skill_view('pstack:swarm')`
  - [ ] <native surface evidence path>
  - [ ] `skill_view('pstack:poteto-mode')`
  - [ ] load each other leaf skill by its exact registered `pstack:` identity
- [ ] Do not arm an audit tick unless recurring Hermes automation is separately authorized. Otherwise record a manual re-entry point and current evidence.
- [ ] If recurring automation is separately authorized, use this tick prompt with that approved job. Otherwise do not claim a background status message.
- [ ] On the operator's hold or stand-down, send every owner a zero-writes order at once.

### Spawn owners

- [ ] Dispatch one bounded owner per review unit with the lifecycle the execution playbook names.
- [ ] Follow this dependency graph. Start dependent work only after its parent merges, or base it on the parent branch when the execution playbook stacks.
  - [ ] <PR id> and <PR id> are independent and first. Both branch from `main`.
  - [ ] <PR id> after <PR id>.
- [ ] Hold the file boundaries. <PR id or class> touches only `<glob>`.
- [ ] Hold the review gate. <PR ids> change an interaction. They wait for the operator's review in chat with screenshots and a video before merge.

### PR mechanics, for every PR

- [ ] Prepare the local review handoff evidence. Before every commit, push, pull-request creation or update, reply, merge, or deletion, obtain explicit current authorization. After every authorized external GitHub write, read back the exact PR/thread/head state; after a local deletion, re-list the exact target state.
- [ ] Run the repo's lint and typecheck once before any separately authorized PR-facing push. Push with hooks on only after that authorization.
- [ ] Run `skill_view('pstack:unslop')` before any separately authorized commit and `skill_view('pstack:no-comments')` before review.
- [ ] Triage every Bugbot and security-reviewer comment per `../references/bugbot-triage.md`.
- [ ] Rebase onto current trunk before babysit and again before the merge-ready report.

### Verdict and merge, for every PR

- [ ] At the review-ready head SHA, run `skill_view('pstack:swarm')`. One gates lane, the ten live lanes from the review unit's **Verify, live** block, the perf lane from **Verify, perf**, and one audit lane that reads the diff and receipts and distrusts the review body.
- [ ] Clean only when every lane is `PASS`. Findings go back to the owner. A new head gets a fresh swarm and a fresh verdict.
- [ ] <The integration rule from the execution playbook. It remains review-ready until explicit current merge authorization; after an authorized merge, read back the exact remote PR and target-branch state.>

### Boot recipe, for every live lane

Each live lane uses the explicitly available native surface and evidence path. Do not claim an unproven isolated environment, host control skill, or hidden child runtime.

- [ ] `git fetch origin <head-branch> && git checkout <head SHA>`.
- [ ] <Start the backend and the surface. Wait for ready.>
- [ ] <Deliver input only through the available native terminal, browser, or desktop route. Name the read-only diagnostics.>
- [ ] Save every screenshot to `<artifact dir>/<review-id>-<lane>-<slug>.png` and return the paths with the report.

## <Change as a verb phrase> (<review id>)

**Depends on.** <PR id, or None.>

**Files.**

- [ ] Edit `<path>`.
- [ ] Create `<path>`.
- [ ] Delete `<path>`.

**Build.**

- [ ] <One change. Name the symbol and the file.>

**You see.**

- [ ] <One observable result, with the exact log line or screen state.>

**Verify, unit.** Tests alone are not sufficient verification. A review unit is verified only when its unit, live, and perf boxes are all checked.

- [ ] <Test file and the case it gains.> Run `<command>`.

**Verify, live.** Tests alone are not sufficient verification. A review unit is verified only when its unit, live, and perf boxes are all checked. Ten native evidence lanes at the review head, per the boot recipe.

- [ ] Lane 1. <Scenario.> Save `<slug>.png`. Pass when <predicate>.
- [ ] Lane 2. <Scenario.> Save `<slug>.png`. Pass when <predicate>.
- [ ] Lane 3. <Scenario.> Save `<slug>.png`. Pass when <predicate>.
- [ ] Lane 4. <Scenario.> Save `<slug>.png`. Pass when <predicate>.
- [ ] Lane 5. <Scenario.> Save `<slug>.png`. Pass when <predicate>.
- [ ] Lane 6. <Scenario.> Save `<slug>.png`. Pass when <predicate>.
- [ ] Lane 7. <Scenario.> Save `<slug>.png`. Pass when <predicate>.
- [ ] Lane 8. <Scenario.> Save `<slug>.png`. Pass when <predicate>.
- [ ] Lane 9. <Scenario.> Save `<slug>.png`. Pass when <predicate>.
- [ ] Lane 10. <Scenario.> Save `<slug>.png`. Pass when <predicate>.

**Verify, perf.** Tests alone are not sufficient verification. A review unit is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. <What is measured.>
- [ ] Probe. <The command or procedure, run at trunk and at the head, interleaved.>
- [ ] Baseline. Record the trunk <value> first.
- [ ] Rule. <Head against trunk, with the number that fails.>

**Review gate.** The operator reviews before merge.

- [ ] Copy lane <n> screenshots into `<media path>/<pr-id>-review-<slug>.png`.
- [ ] Record a 30 to 60 second video of the change on the native surface. Save it as `<media path>/<review-id>-review.mp4`.
- [ ] Present the screenshots and video in chat. Stop at review-ready. Wait for the operator's decision.

**Merge.**

- [ ] Root's clean verdict at the exact head SHA.
- [ ] Bugbot triage done.
- [ ] Rebased onto current trunk after the verdict, patch-id unchanged.
- [ ] <The operator decides any merge or external handoff after reviewing the evidence.>

## Close the program

- [ ] Every box above is checked with its evidence.
- [ ] Reply to the operator with the report the execution playbook names.

## Appendix A. Prototype evidence

<Each open question a prototype answered, with the branch, the SHA, and the artifact links. Each question that stays unproven.>

## Appendix B. Alternatives rejected

<Each approach weighed and why it lost.>

## Appendix C. Risks

<Each risk with the PR it lands in and what the owner watches.>

## Appendix D. Links and reading list

<Docs to read before editing. Which review units load `skill_view('pstack:how')` and `skill_view('pstack:interrogate')`. The trail uses `skill_view('pstack:show-me-your-work')`.>
````

**Reply:** the plan path, the PR ids with their dependencies and the review-gated set, what the prototypes proved and what stays unproven, and the check script's output.
