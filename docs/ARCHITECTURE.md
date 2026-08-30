# Architecture

## Goal

Preserve the whole upstream pstack while replacing only Cursor-bound runtime seams with explicit Hermes adapters.

## Planes

### `pstack`

A native content plugin named `pstack`. It registers exactly 45 qualified skills and keeps their bodies out of the startup `<available_skills>` index. Registration is preflighted as one complete package before any skill is registered.

### `pstack-runtime`

A separate companion for behavior a skill document cannot provide. Its initial local candidate exposes route validation, preserved agent briefs, capability health, and honest degraded states. It does not claim hard sandboxing, arbitrary model routing, sticky continuation, or persistent loops without runtime proof.

### `pstack-benny`

A separate disabled companion preserving all three operational procedures and all Benny support material. Tests use fake adapters only. External messaging, trackers, GitHub writes, and UI automation remain blocked pending explicit authorization.

## Translation policy

1. Keep `upstream/pstack` byte-identical.
2. Keep materialized files byte-identical when they make no Cursor runtime claim.
3. Apply small deterministic patches to direct tool, path, model, transcript, and slash-command seams.
4. Use a semantic adapter only when Hermes lacks a direct primitive.
5. Expose missing capability as degraded or blocked. Never replace it silently with weaker prose.
6. Preserve the operator's approval boundaries. A workflow never authorizes commit, push, PR, merge, deploy, external messages, payment, deletion, credential changes, or non-loopback exposure.

## Required parity

- 45 registered skills: 24 workflows and 21 independent principles.
- 3 dormant Benny SKILL files.
- 2 agent prompts.
- 23 Poteto playbook files: 22 routes and one shared PR postlude.
- 33 skill references, 21 script-tree files, 4 executable suites with 52 declared tests, 11 guide documents, and 6 images.
- 157 accounted source paths with no omitted, folded, renamed, or orphaned component.

## Authority boundary

Publication and installation do not grant runtime authority. Live-profile enablement, persistent execution, external automation, messaging, deployment, destructive work, and non-loopback exposure still require the operator's explicit current authorization and proof.
