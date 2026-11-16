# Implementation and reproduction guide

This is a manual adaptation guide, not a tested one-click deployment. You need
a Fabric-enabled workspace and capacity, a Lakehouse, rights to create/run
notebooks, a semantic model, a pipeline and a Fabric App, plus an execution
identity permitted to read and refresh the model and write the app database.
Use your own tenant, resources and permitted source data. Fabric availability,
licensing and capacity costs depend on your environment.

## Data and model

1. Attach a Lakehouse as the default for the Fabric notebooks. Import/adapt
   the real Python notebook sources numbered 17 and 11–16 in
   [`notebooks`](../notebooks/). Their `# Cell` markers are source boundaries,
   not an automatically validated import format. Inspect paths, libraries,
   model naming and dependencies before running.
2. Execute ingestion and transformations in the order shown in
   [data engineering](./data-engineering.md). Confirm the Delta tables and
   actual schemas exist before configuring the semantic model.
3. Use the [sanitized TMDL](../semantic-model/definition/) as the actual model
   reference. Replace `<WORKSPACE_ID>`, `<LAKEHOUSE_ID>` and
   `<SEMANTIC_MODEL_ID>` for your resources, then configure the connection and
   permissions using a supported Fabric/Power BI workflow. The export is not a
   complete PBIP project and this deployment process has not been validated.
   Notebook 16 looks up the model by the name `NBA Analise Jogadores`; adapt
   the code or use that name and ensure it is unique.

## App and orchestration

1. In `app_nba_stats`, install dependencies with `npm install`. Copy
   [`rayfin.example.yml`](../app_nba_stats/rayfin/rayfin.example.yml) to the
   local ignored `rayfin/rayfin.yml` and replace placeholders with your own
   app host and Fabric IDs. Configure Rayfin authentication, the `nba`
   connector, the app database and data permissions. Review the
   [`rayfin/data`](../app_nba_stats/rayfin/data/) schemas: only intended
   public data should allow anonymous reads; anonymous writes must be denied.
   Do not copy production credentials or deploy the template unchanged.
2. Build the public publisher from the actual allowlist. Run from
   `app_nba_stats` on a Node.js version that supports the current tooling:

   ```powershell
   node scripts\build-publisher.mjs YOUR_DATABASE_NAME YOUR_MODEL_ID publisher.ipynb
   ```

   Import the generated notebook into Fabric, attach the Lakehouse, and test
   it with an authorized identity. The generated file contains your model ID;
   treat it as environment-specific. The existing production notebook is not
   modified by changing the local template.
3. Adapt the [sanitized pipeline JSON](../fabric-artifacts/pipeline/ESPN_Processar_Lotes.json)
   by binding every notebook activity and workspace placeholder to your own
   items. Validate the graph and retry policies. The exported JSON is a
   reference, not a validated import package.
4. Configure a separate daily Fabric schedule at the desired time and time
   zone, with an identity that can run the notebooks, refresh the model and
   write the public database. Confirm end-to-end execution, the published
   timestamp, anonymous reads and denial of anonymous writes. Set an alert and
   monitor history and schedule expiry.

For local development, use [`.env.example`](../app_nba_stats/.env.example)
as a guide; `npm test` and `npm run build` validate the app locally. A static
snapshot is an alternative development path described in the
[app README](../app_nba_stats/README.md); do not distribute its contents
without confirming rights. Local build success does not prove Fabric
permissions, source access, end-to-end deployment or scheduling.

The historical `reorganize_notebooks.py` requires `--workspace-id`; it targets
the earlier notebook set, not the active ESPN pipeline. The manual ESPN
ingestion scripts and historical Python deployment script require
`--workspace`; the PowerShell deployment and reorganization scripts require
`-WorkspaceName`. These parameters avoid embedding a workspace identifier.

## Troubleshooting

- **No updated data:** inspect collector, each pipeline activity, capacity,
  model refresh and publisher; the last complete snapshot may still be shown.
- **Refresh fails:** check the execution identity, model name and model
  connection in Fabric; correct permissions or credentials in the portal.
- **Publishing fails:** check model row counts and API limits, database write
  access and Spark capacity. The publisher fails rather than publishing a
  partial snapshot.
- **Empty/missing shots or biography:** ESPN browser endpoints or coordinates
  may be unavailable; this does not establish a model failure.
- **Database growth:** old snapshot versions and incomplete parts are not
  automatically removed; design and validate a retention process before use.
