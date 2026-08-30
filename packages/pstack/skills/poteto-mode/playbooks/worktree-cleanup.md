<!-- PATCH-HERMES-SKILL-PRIMITIVES -->

> **Native Hermes mapping.** Audit only git-discovered worktrees and user-approved caches. Hermes session evidence is queried with `session_search`; this shell helper accepts no hidden host transcript location.
### Worktree and simulator cleanup

**You own the disk and the safety gate.** Prune merged or abandoned git worktrees and stale iOS simulators to reclaim space. Deletion is irreversible, so every step guards against deleting something in use or holding uncommitted work.

1. Snapshot and audit. Record `df -h /`, then run `scripts/worktree-audit.sh` (principle-build-the-lever). It reads paths from `git worktree list`, never hand-typed, since a hand-typed worktree path can miss a git-discovered worktree (principle-encode-lessons-in-structure). It classifies each worktree by size, age, merge state, uncommitted work, PR state, and available local evidence, then suggests a bucket. Query Hermes sessions with `session_search` outside this shell helper; do not background a hidden transcript scan.
2. The bucket is advice, not permission. The pinned and active chats are the real artifact (principle-prove-it-works). Get that set from the user or sidebar and cross-check every candidate. The lever has marked `safe` a worktree the user had pinned, so the pinned set wins.
3. Verify usage before deleting. For every `verify-recent-chat` row, or anything you doubt, use bounded active-session `delegate_task` reads of `session_search` evidence and report whether the chat is pinned or ongoing and which worktrees it touches. A pinned chat may have arena or repro work in sibling worktrees; treat those as in use even when their names never hit the sidebar.
4. Pause on irreversible loss. `wip:N` is N tracked uncommitted edits. Show the diff and get a decision first, since removing a clean worktree is recoverable from its branch but uncommitted work is gone. `scratch:N` is untracked throwaway, but name the files. No deletion proceeds without explicit current authorization for the exact path and action; `wip` and in-use always pause.
5. Prune only the confirmed, currently authorized set. Per path, use `git worktree remove --force <path>`; if the directory survives on ignored build artifacts, separately authorize `rm -rf <path>`, then run `git worktree prune`. After each deletion, re-list that exact worktree and record `df -h /`; branch refs survive, so no commits are lost.
6. Simulators and other reclaimers. Simulators are usually the next-biggest win. Before any `xcrun simctl` deletion, runtime delete, or cache clearing, obtain explicit current authorization for the exact target. Re-list the simulator/cache state after the authorized deletion. More when needed: Xcode `DerivedData` and `iOS DeviceSupport`; host-application caches explicitly selected by the operator; package caches (pnpm, uv, brew, yarn). Clear only caches the user has not said to keep.

This is the one playbook that deletes user state with no code review to catch a slip, so the gates above are the review.

**Reply:** `df -h /` before and after with space reclaimed, the worktrees pruned, and a one-line reason for each held back (in-use by which chat, or uncommitted work).
