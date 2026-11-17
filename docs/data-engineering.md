# Data engineering

## Source and ingestion

The active flow uses ESPN scoreboard and game-summary endpoints, not the
older `nba_api` prototype. The integration uses publicly reachable,
unofficial endpoints that can change or become unavailable. Player, team and
game identifiers are ESPN identifiers.

[`17_ESPN_Coleta_Automatica.py`](../notebooks/17_ESPN_Coleta_Automatica.py)
fetches the season calendar, daily scoreboards and game summaries, storing
JSONL under OneLake and writing a checkpoint only after a successful pass.
The first pass starts at the source's season start; later passes revisit at
least seven days and recover from the last completed checkpoint. Games in
progress are revisited. A source outage can delay data.

## Notebook sequence

| Notebook | Responsibility |
| --- | --- |
| [11 ESPN Bronze](../notebooks/11_ESPN_Bronze.py) | Preserve scoreboard snapshots in `bronze_espn_scoreboards` |
| [12 ESPN Silver](../notebooks/12_ESPN_Silver.py) | Select current games into `silver_espn_games`, retaining season and phase |
| [13 ESPN Gold](../notebooks/13_ESPN_Gold.py) | Write games, team games, team summary and period facts |
| [14 Players Bronze](../notebooks/14_ESPN_Players_Bronze.py) | Preserve box scores in `bronze_espn_boxscores` |
| [15 Players Silver](../notebooks/15_ESPN_Players_Silver.py) | Prepare player-game and team-game box scores |
| [16 Players Gold](../notebooks/16_ESPN_Players_Gold.py) | Write player, participation and team box-score facts and refresh the semantic model during pipeline runs |

Gold includes `gold_espn_games` (one row per game), `gold_espn_game_periods`
(team/game/period), `gold_espn_team_games`, `gold_espn_team_summary`,
`gold_espn_team_boxscores`, `gold_espn_player_games` (participating
player/game), `gold_espn_players` and `gold_espn_player_summary`. Preseason
is filtered; nonparticipants do not count as played games. Missing or
incomplete upstream statistics affect downstream results.

## Orchestration and quality

The [pipeline definition](../fabric-artifacts/pipeline/ESPN_Processar_Lotes.json)
is an export of the actual activity graph, with workspace and notebook IDs
replaced. Notebook activities have retries; 60-second waits separate stages,
including the final wait before `Hoop_Public_Publish`. Notebook 16 resolves
the uniquely named `NBA Player Analysis` model in its current workspace,
requests refresh and waits for completion; the scheduled identity must be
allowed to refresh it. This name is part of the prepared migration; the
production notebook and model still use the previous Portuguese name until
the coordinated deployment.

The existing schedule is 03:00 `E. South America Standard Time`, expiring
30 June 2027. A successful isolated scheduled test exercised Gold, the wait
and publishing; the first complete scheduled execution after the final retry
change still needs monitoring. Schedule start is not the time data becomes
available. Spark capacity, source availability, permission changes and
refresh failures can prevent publication. Check each activity's run history
and the timestamp in the app.
