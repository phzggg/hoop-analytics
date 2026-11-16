# AI-assisted development and lessons learned

The visible development conversation shows the project owner supplying product
requirements and visual references and an AI coding assistant helping inspect
the Fabric environment, implement and refine the app, publisher and pipeline,
and run targeted checks. The user reviewed the experience and requested
changes. This does not establish authorship of every historical file or the
complete development history, and private conversations are not reproduced.

Useful practices illustrated by this work:

- Translate visual requests into explicit behavior: navigation, selected
  state, data sources and limitations matter as much as appearance.
- Validate the actual data path. A public app can read a curated copy while
  the original semantic model remains private, but the copy and permissions
  must be reviewed independently.
- Treat AI suggestions as unverified until code, outputs, identities and
  permissions are checked. UI build success alone does not establish that a
  scheduled end-to-end refresh works.
- An initial publication encountered Spark capacity limits; introducing waits
  and retries was followed by an isolated scheduled test. The complete daily
  chain still needs observation after that change.
- ESPN data and assets are external dependencies. Source availability,
  completeness, licensing and browser behavior remain independent risks.
- A failed snapshot should not replace the last complete one. Validation and
  a commit-like manifest reduce partial-publication risk, but introduce
  storage-retention work.
