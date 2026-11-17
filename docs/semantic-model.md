# Semantic model

The [TMDL export](../fabric/semantic-model/definition/) is an English-language
migration prepared from the production model. It has not yet been deployed:
production still uses the Portuguese names. Workspace, lakehouse and model IDs
are placeholders. It is a definition export, not a complete PBIP project.

| Table | Storage | Purpose |
| --- | --- | --- |
| `Games` | Direct Lake | Games, teams, dates, scores and status |
| `Players` | Direct Lake | Player identity and profile fields |
| `Player Games` | Direct Lake | Player participation by game and raw statistics |
| `Team Statistics` | Direct Lake | Team box-score statistics by game |
| `Periods` | Direct Lake | Team scores by game and period |
| `Calendar` | Import | Date dimension |

Five active many-to-one relationships use single-direction filtering:
`Player Games[Player Id]` to `Players[Player Id]`,
`Games[Date]` to `Calendar[Date]`, and `Player Games`,
`Team Statistics` and `Periods` each link by `Game Id` to `Games`.
See the exported relationships for the exact definitions.

The six measures in `Player Games` count rows as games played, sum raw
points, and average raw points, rebounds, assists and minutes. For example:

```dax
Games Played = COUNTROWS('Player Games')
Total Points = SUM('Player Games'[Raw Points])
```

The app's [field allowlist and DAX query construction](../app_nba_stats/src/data.ts)
select raw fields and also calculate season and game metrics in TypeScript.
These client-side calculations and rankings should not be confused with the
model measures or official league rankings. The public publisher exports
only its selected fields, not every model column.
Snapshot version 1 retains its existing field keys for compatibility; the
query layer maps them to English model columns.
