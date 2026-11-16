import { entity, decimal, int, text, role } from '@microsoft/rayfin-core';
import { Source } from '@microsoft/rayfin-connectors';

@role('authenticated', ['read'])
@entity()
export class GoldEspnPlayerSummary extends Source({ schema: 'dbo', table: 'gold_espn_player_summary', primaryKey: [] }) {
  @text({ optional: true, column: 'player_id', max: 8000 }) playerId?: string;
  @text({ optional: true, column: 'player_name', max: 8000 }) playerName?: string;
  @int({ optional: true, column: 'games_played' }) gamesPlayed?: number;
  @int({ optional: true, column: 'total_points' }) totalPoints?: number;
  @decimal({ optional: true, column: 'avg_points' }) avgPoints?: number;
  @decimal({ optional: true, column: 'avg_rebounds' }) avgRebounds?: number;
  @decimal({ optional: true, column: 'avg_assists' }) avgAssists?: number;
  @decimal({ optional: true, column: 'avg_minutes' }) avgMinutes?: number;
}
