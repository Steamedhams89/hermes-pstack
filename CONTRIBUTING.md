# Contributing

Thanks for helping keep the Hermes pstack port complete, reviewable, and honest.

## Ground rules

1. **Do not edit `upstream/pstack` directly.** It is an immutable mirror of the locked upstream commit.
2. Preserve all upstream components. Do not collapse, rename, or silently omit a skill, playbook, reference, script, guide page, image, automation resource, or agent brief.
3. Translate only runtime seams that Hermes cannot execute as written.
4. Do not replace a missing capability with optimistic prose. Report it as degraded or blocked.
5. Do not weaken approval boundaries. A skill cannot authorize an external or destructive action by naming a playbook.
6. Keep generated dependencies and caches out of the repository.

## Change process

- Open an issue for an upstream version update or a behavior-changing adapter change.
- Keep the immutable source update separate from Hermes-specific translations.
- Add or update the relevant parity-ledger rows and patch records.
- Add a test that proves the intended boundary or behavior.
- Regenerate deterministic receipts only after the exact gates pass.

## Required checks

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

The receipt command provisions Bun dependencies only inside an automatically removed temporary copy.

## Pull requests

A pull request should explain:

- the user-visible outcome;
- whether the change is upstream preservation, a mechanical translation, or a semantic adapter;
- every affected parity row and patch ID;
- the exact verification commands and results;
- any capability that remains degraded or intentionally dormant.

Do not include credentials, live profile data, session transcripts, generated dependencies, or machine-specific paths.
