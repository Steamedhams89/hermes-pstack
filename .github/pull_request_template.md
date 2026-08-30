## Outcome

<!-- What changes for the user? -->

## Porting classification

- [ ] Upstream preservation
- [ ] Mechanical Hermes translation
- [ ] Semantic Hermes adapter
- [ ] Documentation or release tooling only

## Source and parity

- [ ] `upstream/pstack` remains byte-identical to the locked source
- [ ] Every affected upstream path is accounted for
- [ ] Patch IDs and receipts are updated where required
- [ ] No capability or approval boundary was weakened

## Verification

<!-- Paste the exact commands and results. -->

- [ ] Python suite
- [ ] Bun tests and strict TypeScript
- [ ] `tools/verify.py --require-complete`
- [ ] All three `hermes plugins doctor --ci` checks
- [ ] Plugin-pack validation
- [ ] No generated dependencies, caches, secrets, or machine paths
