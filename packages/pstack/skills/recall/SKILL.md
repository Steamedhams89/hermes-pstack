---
name: recall
description: "Reconstruct your recent working context from your own chat history, live state, and the shared record (user reports, prior fixes, incidents), then hand back a tight current-state brief. Use for 'recall my work on X', 'catch me up', 'what have I been working on', 'where did I leave off', before starting or resuming work."
disable-model-invocation: true
---

<!-- PATCH-HERMES-SKILL-PRIMITIVES -->

> **Native Hermes mapping.** Use `session_search` for Hermes conversation evidence and `delegate_task` only for bounded, read-only history slices. Host transcript directories and automatic cross-workspace mining are unavailable.

# Recall

**Before you start or resume work, you rebuild the user's recent working context and hand back a tight capsule of where things stand now and what to do next.** Use for "recall my work on X", "catch me up", "what have I been working on", or "where did I leave off".

Keep it tight and on-topic. Read only what the in-scope threads need, then stop. Use bounded `delegate_task` readers only when several independent history slices need coverage. The parent keeps only their findings and the final brief.

Your context lives in two records. Your own chat history holds what you did and decided. The shared record holds everything that happened around the same code under other names: the symptoms users keep reporting, the fixes that shipped and got reverted, the errors still firing in prod. That second record is what the **why** skill searches, across source control, the issue tracker, chat and issue channels, long-form docs, and error tracking. A feature with a long bug tail keeps most of its story there, so don't reconstruct it from your transcripts alone.

Hermes session evidence is read through `session_search`. It returns the scoped messages and metadata without exposing a host transcript-directory contract. A missing or inaccessible session is a stated evidence gap, not a path to guess.

1. Classify, then route. One specific prior chat to resume is the `session-pickup` playbook, not this. Turning habits into a durable skill is `automate-me`. A human-readable summary of your work is a different task. Recall loads working context across recent chats before you act. If the user already gave you a full state capsule (paths, branch, the change), use it and skip the mining.
2. Lock the scope before searching. Pin the window ("recent" is a real range, default the last 7 days), the topic if named, and the workspace (default the active one; never read another project's transcripts without being asked). State the scope back. Never quietly turn "all" into "recent N".
3. Search scoped Hermes session history. Use `session_search` for the topic and time window, then read only matching conversations and relevant regions. For several independent slices, dispatch bounded read-only `delegate_task` readers with the same scope; each returns topic, user goal, decisions, open threads, corrections, and artifact pointers. Do not scan unrelated sessions, infer transcript paths, or claim a child has private-history access it was not given.

4. Sweep the shared record whenever the topic names a feature, file, subsystem, area, or bug. This is the default, not a judgment call, and "my work on X" does not exempt it. A named target carries history you never see in your own transcripts, and that history is the point of the sweep. Hand it to `skill_view('pstack:why')` with the question "what is the current state, what has been tried and did not hold, and what are users still reporting?" Reuse its evidence categories and preserve its posture: one bounded investigator per available source, null results are findings, and an unavailable MCP is a named gap. Fold what comes back into the brief. Skip this step only for pure activity recall with no named target ("what did I do this week"), where your own history and live state are the entire answer.
5. Verify against live state. A transcript or a stale ticket is history, not current truth, so take the PRs, branches, and tickets that the mining and the sweep surfaced and check them with `git` and `gh`. When the answer hinges on what an agent actually did, read the available full Hermes session evidence and concrete artifacts, not a self-report or a trimmed excerpt.
6. Write the brief to the contract below. Group by thread. Stay on the named topic.

## Output contract

Lead with the capsule, then the thread status, then the problems, then the next move. Deeper detail goes below or gets cut.

- **Capsule.** At most 5 bullets. What this work is and where it stands overall.
- **Threads.** One line each, prefixed with exactly one status tag: `[merged #N]`, `[open PR #N]`, `[in flight <branch>]`, `[verified, uncommitted]`, `[reverted #N]`, or `[planned, not started]`. A thread with no tag is not done yet, so tag it.
- **Problems.** At most 5, the recurring ones. Include the symptoms users keep reporting and any fix that shipped and was reverted, so the next attempt starts where the last one failed.
- **Next move.** The single most useful next action, concrete.

An adjacent feature or ticket stays out unless it blocks this one. When the capsule and thread lines outgrow a screen, cut detail before you cut threads. Write the brief through `skill_view('pstack:unslop')`, cite Hermes session findings by their session reference and shared-record findings by their source (PR #, ticket ID, chat permalink, error-tracker issue), and sanitize private context before any authorized public output.

**Reply:** the brief, to the contract above.
