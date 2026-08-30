---
name: swarm
description: "Fan out N parallel workers, drain them, and return one report. Use for /swarm, 'swarm this', or parallel coverage, races, gauntlets, and exploration."
disable-model-invocation: true
---

<!-- PATCH-HERMES-SKILL-PRIMITIVES -->

> **Native Hermes mapping.** Before fan-out, call `pstack_routes` with `{"action":"get"}` and read `effective.roles.swarm-workers`. Use `delegate_task` if that route or `delegate_with_route` is unavailable; only a supported configured route may use `delegate_with_route`. A missing tool, config, or route explicitly falls back to inherited `delegate_task`. This port does not claim cloud workers, background persistence, temporary-path conventions, or arbitrary provider-model selection.

# Swarm

Fan out N bounded workers. They may cover separate slices, race the same brief, or mix both. The parent waits for their returned results, aggregates, and returns one report.

## Start

Use `todo` with one entry per phase before launching anything.

1. Frame
2. Fan out
3. Aggregate
4. Report

## Phase A: Frame

1. State the done predicate and the artifact or report the swarm must return.
2. Choose the shape. Partition into slices, race N workers on identical briefs, or mix both. For a race or mixed shape, declare `first pass`, `rank all`, or `best-of` before spawning.
3. Set N from the user or derive it from the shape. N is total bounded workers, not a claim about hidden runtime concurrency.
4. Use the inherited parent route by default. A model race is unavailable unless a separately installed runtime exposes and the operator approves explicit route aliases; never name arbitrary provider identifiers in this content skill.
5. Give each writing worker an explicitly permitted output location. Use a user-approved worktree, branch, or repository-local directory; do not invent host paths or overlapping writer scopes.

## Phase B: Fan out

Dispatch all N workers together with `delegate_task`. Each brief names its goal, scope, permitted writes, verification target, report format, and inherited route. Use `delegate_with_route` only for a separately approved alias. The port does not claim cloud isolation, hard sandboxing, or background persistence.

When a worker must start from a non-default branch, state the already-available branch and its permitted workspace in the brief. Do not create or push branches without separate authority.

Every brief stands alone. Include the goal, scope, exact slice or race arm, how to verify, and what to report. Reports use `PASS`, `ISSUES`, or `BLOCKED` with evidence.

If a worker drops out, proceed with N-1 and note it.

## Phase C: Aggregate

Read the terminal results. For coverage, every required slice needs a result. For a race, apply the selection rule declared up front. Use first pass, rank all, or best-of. Do not paste raw worker dumps.

Keep a compact result table, one-line evidenced issues, and explicit gaps or dropouts.

## Phase D: Report

Return one consolidated in-chat report with the table, issue one-liners, gaps or dropouts, and the race rule when used.
