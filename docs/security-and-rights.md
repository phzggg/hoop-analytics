# Security, rights and release checklist

**This workspace is not yet cleared for public release.** The configuration
template and sanitized pipeline/model exports reduce exposure, but are not a
substitute for a full review.

## Before making a repository public

- Review every intended tracked file and generated notebook, including old
  documentation, outputs, logs and samples, for secrets, personal details,
  internal identifiers and endpoints. The workspace root has no Git history
  available here, so previous commits have not been checked.
- `.gitignore` protects only untracked files; it does not remove previously
  tracked files or sanitize history. Review `git status`, tracked files and
  history in the actual repository; do not rewrite history without approval.
- Production `rayfin.yml`, deployment metadata, generated connector metadata,
  local environments, generated static snapshots, samples and logs are ignored.
  Verify ignore rules before staging. Legacy deployment and manual ingestion
  scripts require an explicit workspace rather than embedding its name or ID.
- Review the snapshot allowlist and data entity rules. Confirm anonymous users
  cannot mutate data and have no direct model access, and use least privilege
  for the scheduled identity. Avoid exposing tokens or connection strings.
- Inventory dependency licenses, external API terms and the rights for data,
  logos, photos, team branding and screenshots. Publicly accessible content
  is not automatically licensed for redistribution. ESPN endpoints are
  unofficial and may change. The NBA's
  [terms of use](https://www.nba.com/termsofuse) place conditions on use of
  its content and marks; confirm applicable ESPN terms for the actual service.
  The package-lock files record licenses for all 549 external packages in
  the active app and 754 of 757 package entries in the earlier app; the three
  without license metadata are its local workspace packages. This metadata
  inventory is not a legal review or proof of trademark or asset rights.
- The Zod advisory
  [GHSA-mrhx-c7xc-m3w5](https://github.com/advisories/GHSA-mrhx-c7xc-m3w5)
  is addressed locally with an override to Zod 4.6.7. This is outside the
  range declared by `@microsoft/rayfin-tools-common`; app tests, build, CLI
  startup and a manifest-validation smoke test pass, but authenticated Fabric
  deployment with the override has not been validated. Reassess the override
  when Rayfin supports a patched Zod release.
- A local `npm audit --omit=dev --audit-level=high` reports no production
  vulnerabilities. The full audit still reports two high and five moderate
  findings in development dependencies, including the Rayfin CLI's MSAL Node
  dependency ([GHSA-xcx6-jx8p-x3h5](https://github.com/advisories/GHSA-xcx6-jx8p-x3h5)).
  npm proposes breaking changes; a major authentication dependency override
  was not applied without end-to-end validation. Review the full audit and
  use a trusted development environment while awaiting a compatible fix.
- Project-owned code is offered under the [MIT License](../LICENSE). The
  earlier app's separate license and third-party dependency licenses still
  apply where relevant. MIT does not grant rights to third-party data,
  imagery or marks; confirm the necessary rights before distribution.

Screenshots and sample data are intentionally not supplied for redistribution
until rights are clarified. The public app itself may display externally hosted
assets, so its availability is not evidence that rehosting them is permitted.
No external publication, repository visibility change or Git history rewrite
was performed as part of this preparation.
