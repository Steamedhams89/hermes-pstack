# Security policy

## Supported versions

Security fixes are applied to the latest published Hermes port release. The immutable upstream mirror remains unchanged; any mitigation is documented as a Hermes adaptation patch.

## Report a vulnerability

Please do not open a public issue for a suspected vulnerability.

Use GitHub's private **Report a vulnerability** flow when it is available for this repository. If private reporting is unavailable, contact the maintainer privately through the GitHub profile linked to the repository owner.

Include:

- the affected plugin or skill;
- the Hermes Agent and port versions;
- reproduction steps using a disposable profile;
- the authority, capability, path, or data boundary that is crossed;
- whether the issue can trigger an external action, credential exposure, path escape, or persistent execution.

Do not include real credentials or private user data. Use synthetic fixtures.

## Scope

Particularly useful reports cover plugin installation, qualified-skill registration, symlink or path traversal, capability consent, route configuration, implicit dependency installation, external-action authorization, or source/parity verification bypasses.
