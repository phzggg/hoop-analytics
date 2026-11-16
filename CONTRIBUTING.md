# Contributing

Thank you for helping improve HoopMetrics. Before proposing a change, check the
[architecture](docs/architecture.md) and [implementation guide](docs/implementation-guide.md)
to understand the active ESPN pipeline and Fabric App. Historical prototypes
are kept for reference and do not represent the deployed data flow.

Keep changes focused, explain any behavior or configuration changes, and
include tests for new or corrected behavior. Do not deploy to another
person's Fabric workspace or change production schedules or permissions
without their approval.

For app changes, use Node.js 24 and run:

```powershell
cd app_nba_stats
npm install
npm test
npm run build
```

For the manual ESPN collectors, run the relevant Python tests in `tests/`.
Fabric-dependent functionality also requires testing in an appropriately
configured workspace; local tests alone do not validate a deployment.

Do not commit credentials, private endpoints, environment-specific configuration,
raw snapshots, logs or personally identifiable information. Check the
[security and rights guide](docs/security-and-rights.md) before sharing data,
images, logos or other third-party content. Dependencies and tools may have
their own licenses and advisories.
