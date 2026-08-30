# pstack for Hermes

[![CI](https://github.com/Steamedhams89/hermes-pstack/actions/workflows/ci.yml/badge.svg)](https://github.com/Steamedhams89/hermes-pstack/actions/workflows/ci.yml)
[![Upstream pstack](https://img.shields.io/badge/upstream-pstack%200.14.5-6f42c1)](https://github.com/cursor/plugins/tree/6fecddba65801f9b9c08b8b328d998ee5b09d290/pstack)
[![Hermes Agent](https://img.shields.io/badge/Hermes%20Agent-0.20.6%2B-1f6feb)](https://github.com/NousResearch/hermes-agent)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

Lauren Tan's complete **pstack 0.14.5**, ported to [Hermes Agent](https://github.com/NousResearch/hermes-agent) without flattening the skill set or pretending Cursor-only runtime features exist.

**45 first-class skills · 157 upstream paths accounted · 7 adaptation patches receipted**

> [!IMPORTANT]
> This is an unofficial community port. It is not endorsed by Lauren Tan, Cursor, or the upstream pstack maintainers.

## Why this port exists

pstack is a coherent engineering system, not a bag of prompts. Partial ports lose the playbook routing, principles, support files, agent briefs, and verification machinery that make the system useful.

This repository preserves the whole upstream product while translating only the runtime seams:

- every upstream path is represented in a machine-readable parity ledger;
- the original source is kept as an immutable, byte-identical mirror;
- Cursor-specific tools, model selectors, paths, transcripts, and slash commands are replaced with explicit Hermes equivalents;
- unsupported capabilities fail closed or report a degraded state instead of being replaced with plausible prose;
- all skills use qualified names such as `pstack:architect`, so the full set does not flood Hermes' startup skill index.

## Install

Plugin-pack installation requires **Hermes Agent 0.20.6 or newer**. The pack displays its contents before installation and pins each plugin to an exact commit.

```bash
PACK_URL=https://raw.githubusercontent.com/Steamedhams89/hermes-pstack/v0.14.5-hermes.1/hermes-pack.yaml

# Read-only review
hermes plugins pack show "$PACK_URL"

# Interactive install and per-plugin capability review
hermes plugins pack install "$PACK_URL"
```

The default pack installs:

1. **`pstack`** — the complete 45-skill content plugin;
2. **`pstack-runtime`** — the optional route/state companion and its single local configuration tool.

It deliberately does **not** install `pstack-benny`. Benny's three automation procedures are preserved in this repository but remain dormant until an operator separately reviews and authorizes their external integrations.

Restart the Hermes gateway after installation when prompted:

```bash
hermes gateway restart
```

## Use

Load a workflow explicitly:

```text
skill_view(name="pstack:poteto-mode")
```

Then state the outcome and the evidence:

```text
Goal: add a --json flag without changing the existing text output.
Evidence: run and verify both forms.
```

Other useful entry points:

```text
skill_view(name="pstack:how")          # understand a codebase
skill_view(name="pstack:why")          # recover design rationale
skill_view(name="pstack:architect")    # compare designs before coding
skill_view(name="pstack:interrogate")  # adversarial multi-lens review
skill_view(name="pstack:reflect")      # review the work and process
```

The complete adapted guide starts at [`docs/upstream-guide/README.md`](docs/upstream-guide/README.md).

## What is included

| Package | Contents | Runtime surface | Default pack |
|---|---|---|---|
| [`pstack`](packages/pstack) | 24 workflows, 21 principles, all linked references, playbooks, and scripts | No tools, hooks, networking, or background work | Yes |
| [`pstack-runtime`](packages/pstack-runtime) | Two preserved role briefs, validated route mapping, local state and health descriptors | One local tool: `pstack_routes` | Yes |
| [`pstack-benny`](packages/pstack-benny) | Three Benny procedures and all support material | Dormant; external adapters are not configured | No |

<details>
<summary><strong>All 24 workflows</strong></summary>

`architect` · `arena` · `automate-me` · `blast-radius` · `bro` · `create-verification-skill` · `figure-it-out` · `how` · `interrogate` · `maintain-verification-skill` · `make-bot-ui` · `no-comments` · `poteto-mode` · `recall` · `reflect` · `setup-pstack` · `show-me-your-work` · `swarm` · `tdd` · `teach` · `technical-writing` · `typescript-best-practices` · `unslop` · `why`

</details>

<details>
<summary><strong>All 21 principles</strong></summary>

`boundary-discipline` · `build-the-lever` · `encode-lessons-in-structure` · `exhaust-the-design-space` · `experience-first` · `fix-root-causes` · `foundational-thinking` · `guard-the-context-window` · `laziness-protocol` · `make-operations-idempotent` · `migrate-callers-then-delete-legacy-apis` · `minimize-reader-load` · `model-the-domain` · `never-block-on-the-human` · `outcome-oriented-execution` · `prove-it-works` · `redesign-from-first-principles` · `separate-before-serializing-shared-state` · `sequence-verifiable-units` · `subtract-before-you-add` · `type-system-discipline`

</details>

## Source accounting

| Field | Locked value |
|---|---|
| Upstream | [`cursor/plugins/pstack`](https://github.com/cursor/plugins/tree/6fecddba65801f9b9c08b8b328d998ee5b09d290/pstack) |
| Upstream version | `0.14.5` |
| Upstream commit | `6fecddba65801f9b9c08b8b328d998ee5b09d290` |
| Source files | `157` |
| Source bytes | `3,091,772` |
| Canonical tree SHA-256 | `0b261012eb982e45472b5e368592da26a8c15c92bb12dd680d3786b997c57177` |
| Registered skills | `45` — 24 workflows + 21 principles |
| Documented adaptation patches | `7` |

The authoritative records are:

- [`provenance/UPSTREAM.lock.json`](provenance/UPSTREAM.lock.json) — immutable source identity;
- [`upstream/pstack`](upstream/pstack) — byte-identical upstream mirror;
- [`provenance/parity-ledger.json`](provenance/parity-ledger.json) — one row per upstream path;
- [`provenance/patches/index.json`](provenance/patches/index.json) — every mechanical or semantic translation;
- [`provenance/test-receipts.json`](provenance/test-receipts.json) — deterministic verification receipts.

See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for the package and authority boundaries.

## Safety model

- `pstack` registers content only. It has no tools, hooks, network clients, background workers, or implicit installers.
- `pstack-runtime` exposes one local route-configuration tool. It does not start delegation or external work itself.
- The versioned pack pins exact commits and cannot pre-grant capabilities or carry secrets.
- `pstack-benny` is excluded from the default pack.
- The source and installed package trees reject symlinks and path escapes.
- A workflow never grants its own authority. Publishing or installing this repository does not authorize messages, pushes, merges, deployments, deletion, credentials, payments, recurring automation, or non-loopback exposure.

## Verify from source

Development verification uses Python 3.11+, Bun 1.4.0, and a Hermes Agent source checkout:

```bash
export HERMES_SOURCE_ROOT=/path/to/hermes-agent
export PYTHONDONTWRITEBYTECODE=1

python -B -m pytest -q -p no:cacheprovider
python -B tools/receipt.py --write --provision-script-deps
python -B tools/verify.py --require-complete

hermes plugins doctor --ci packages/pstack
hermes plugins doctor --ci packages/pstack-runtime
hermes plugins doctor --ci packages/pstack-benny
hermes plugins pack show hermes-pack.yaml
```

`--provision-script-deps` is an explicit networked development step. It runs `bun install --frozen-lockfile`, the 52 preserved Bun tests, and strict TypeScript checking inside an automatically removed temporary copy. It never writes `node_modules` into the release tree.

CI repeats the source-lock, parity, receipt, Python, Bun, TypeScript, plugin-doctor, pack, and residue gates against a pinned Hermes Agent revision.

## Repository layout

```text
packages/
  pstack/          complete content plugin
  pstack-runtime/  optional Hermes runtime companion
  pstack-benny/    preserved, dormant automation resources
upstream/pstack/   immutable upstream source mirror
provenance/        lock, parity ledger, patches, notices, receipts
docs/              architecture and the adapted pstack guide
tools/             source-accounting and receipt tooling
tests/             parity, authority, runtime, and packaging gates
```

## Contributing

Read [`CONTRIBUTING.md`](CONTRIBUTING.md) before changing the port. Do not edit `upstream/pstack` directly. Every upstream update must replace the locked mirror, account for every path, document every translation, and regenerate passing receipts.

Security reports should follow [`SECURITY.md`](SECURITY.md).

## License and attribution

Upstream pstack is MIT licensed, Copyright © 2026 Lauren Tan. The Hermes adaptation and release tooling are also MIT licensed. See [`LICENSE`](LICENSE), [`NOTICE.md`](NOTICE.md), and [`provenance/NOTICE.md`](provenance/NOTICE.md).

This project preserves upstream attribution and clearly separates original source from Hermes-specific adaptation work.
