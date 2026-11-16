# Fabric App

The active app lives in [`app_nba_stats`](../app_nba_stats/). It uses React,
TypeScript, Vite and Microsoft Rayfin services. Its existing
[app README](../app_nba_stats/README.md) contains operational notes.

## Features and interactions

| View | User workflow and data |
| --- | --- |
| League | Switch phase, conference/league standings, overview and leader statistics; standings are computed from available final scores |
| Games | Browse finished or upcoming games in a list or calendar; open a game |
| Game | Inspect period scores, player box score, team comparison and current calculated standings |
| Teams | Browse teams and open a team for standings, overview, games, participant list and leaders |
| Players | Browse the historical player dimension and open a profile; it is not an official current roster |
| Player | Inspect game and season statistics, rankings, biography and a shot map for a selected game |

The latest available season is selected automatically. Aggregate shooting
percentages use total makes divided by total attempts; missing values are
not silently treated as valid statistics. Rankings have no official minimum
qualification. The season timeline is based on ESPN season dates, not the
number of games played. The map uses ESPN play-by-play, excludes free throws
and identifies missing coordinates or mismatches with the box score; its
coordinates are approximate and it is not a season-wide shot map.

[`dashboard.tsx`](../app_nba_stats/src/dashboard.tsx) implements routes,
tabs and views; [`data.ts`](../app_nba_stats/src/data.ts) implements field
selection, data access and derived metrics. [`espn.ts`](../app_nba_stats/src/espn.ts)
and [`shots.ts`](../app_nba_stats/src/shots.ts) support browser-side ESPN
requests and shot interpretation. [`style.css`](../app_nba_stats/src/style.css)
contains layout and interaction styles.

## Data modes and integrity

[`main.tsx`](../app_nba_stats/src/main.tsx) chooses published public data
when `VITE_PUBLIC_DATA=true`, an optional static snapshot when
`VITE_PUBLIC_SNAPSHOT_URL` is set, and authenticated delegated model access
otherwise. Changes to Vite variables require a new build.

The public publisher generates versioned gzip/base64 parts and a manifest
after validation. The reader pages through data, verifies part sequence and
SHA-256 and validates the decoded shape. Incomplete versions are not selected;
errors are shown rather than presented as empty success. The snapshot time is
shown in the app. Existing old versions and abandoned parts require an
operational retention strategy.

Browser requests to ESPN for profile information, season dates and shots are
separate from the snapshot and depend on that service and browser access.
See [security and rights](./security-and-rights.md) before redistributing
content or enabling anonymous access in another deployment.
