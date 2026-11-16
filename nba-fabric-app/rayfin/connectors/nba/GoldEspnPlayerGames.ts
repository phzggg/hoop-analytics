import { entity, date, decimal, int, text, role } from '@microsoft/rayfin-core';
import { Source } from '@microsoft/rayfin-connectors';

@role('authenticated', ['read'])
@entity()
export class GoldEspnPlayerGames extends Source({ schema: 'dbo', table: 'gold_espn_player_games', primaryKey: [] }) {
  @text({ optional: true, column: 'game_id', max: 8000 }) gameId?: string;
  @date({ optional: true, column: 'game_date' }) gameDate?: Date;
  @text({ optional: true, column: 'team_id', max: 8000 }) teamId?: string;
  @text({ optional: true, column: 'team_name', max: 8000 }) teamName?: string;
  @text({ optional: true, column: 'player_id', max: 8000 }) playerId?: string;
  @text({ optional: true, column: 'player_name', max: 8000 }) playerName?: string;
  @decimal({ optional: true }) minutes?: number;
  @int({ optional: true }) points?: number;
  @int({ optional: true }) rebounds?: number;
  @int({ optional: true }) assists?: number;
  @date({ optional: true, column: 'updated_at' }) updatedAt?: Date;
}
