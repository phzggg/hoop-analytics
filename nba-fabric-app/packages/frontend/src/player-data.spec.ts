import { describe, expect, it, vi } from 'vitest';
import { createRayfinPlayerDataSource, SourceContractError } from './player-data';

describe('consultas Rayfin somente leitura', () => {
  it('passa o ID sem construir SQL e percorre páginas', async () => {
    const games = vi.fn()
      .mockResolvedValueOnce({ items: [], hasNextPage: true, endCursor: 'next' })
      .mockResolvedValueOnce({ items: [], hasNextPage: false });
    const source = createRayfinPlayerDataSource({ summary: vi.fn(), games });
    await expect(source.listGames("p'1")).resolves.toEqual([]);
    expect(games).toHaveBeenNthCalledWith(1, "p'1", undefined);
    expect(games).toHaveBeenNthCalledWith(2, "p'1", 'next');
  });

  it('normaliza nomes e inteiros seguros sem inventar valores', async () => {
    const summary = vi.fn().mockResolvedValue({ items: [{
      playerId: '1', playerName: 'Player', gamesPlayed: '4', totalPoints: 98,
      avgPoints: 24.5, avgRebounds: null, avgAssists: 2, avgMinutes: 30,
    }], hasNextPage: false });
    const source = createRayfinPlayerDataSource({ summary, games: vi.fn() });
    await expect(source.listPlayers()).resolves.toEqual([{
      player_id: '1', player_name: 'Player', games_played: 4, total_points: 98,
      avg_points: 24.5, avg_rebounds: null, avg_assists: 2, avg_minutes: 30,
    }]);
  });

  it('rejeita bigint inseguro e cursor ausente', async () => {
    const summary = vi.fn().mockResolvedValueOnce({ items: [{
      playerId: '1', playerName: 'Player', gamesPlayed: '9007199254740993',
      totalPoints: 1, avgPoints: 1, avgRebounds: 1, avgAssists: 1, avgMinutes: 1,
    }], hasNextPage: false }).mockResolvedValueOnce({ items: [], hasNextPage: true });
    const source = createRayfinPlayerDataSource({ summary, games: vi.fn() });
    await expect(source.listPlayers()).rejects.toBeInstanceOf(SourceContractError);
    await expect(source.listPlayers()).rejects.toBeInstanceOf(SourceContractError);
  });
});
