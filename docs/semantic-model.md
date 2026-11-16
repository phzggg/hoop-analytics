# Semantic model

The [TMDL export](../semantic-model/definition/) comes from the actual
production model, not an illustrative redesign. Workspace, lakehouse and
model IDs have been replaced with placeholders. It is a definition export,
not a complete PBIP project; replacing placeholders and deploying it has
not been tested.

| Table | Storage | Purpose |
| --- | --- | --- |
| `Partidas` | Direct Lake | Games, teams, dates, scores and status |
| `Jogadores` | Direct Lake | Player identity and profile fields |
| `Participações` | Direct Lake | Player participation by game and raw statistics |
| `Estatísticas de Times` | Direct Lake | Team box-score statistics by game |
| `Períodos` | Direct Lake | Team scores by game and period |
| `Calendário` | Import | Date dimension |

Five active many-to-one relationships use single-direction filtering:
`Participações[Jogador Id]` to `Jogadores[Jogador Id]`,
`Partidas[Data]` to `Calendário[Data]`, and `Participações`,
`Estatísticas de Times` and `Períodos` each link by `Jogo Id` to `Partidas`.
See the exported relationships for the exact definitions.

The six measures in `Participações` count rows as games played, sum raw
points, and average raw points, rebounds, assists and minutes. For example:

```dax
Jogos disputados = COUNTROWS('Participações')
Pontos totais = SUM('Participações'[Pontos brutos])
```

The app's [field allowlist and DAX query construction](../app_nba_stats/src/data.ts)
select raw fields and also calculate season and game metrics in TypeScript.
These client-side calculations and rankings should not be confused with the
model measures or official league rankings. The public publisher exports
only its selected fields, not every model column.
