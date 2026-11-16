import { describe, expect, it, vi } from 'vitest';
import { fetchShots, parseShots } from './shots';

const play = (overrides: Record<string, unknown> = {}) => ({
  id: '1', shootingPlay: true, pointsAttempted: 2, scoringPlay: true,
  participants: [{ athlete: { id: '10' } }, { athlete: { id: '11' } }],
  coordinate: { x: 25, y: 1 }, period: { number: 1 }, text: 'Player makes layup',
  ...overrides,
});
const summary = (plays: unknown[]) => ({ header: { id: '123' }, plays });

describe('ESPN shot map', () => {
  it('uses the first participant as shooter and excludes free throws and other players', () => {
    const result = parseShots(summary([
      play(), play({ id: '2', scoringPlay: false, period: { number: 5 }, coordinate: { x: 3, y: 2 } }),
      play({ id: '3', pointsAttempted: 1 }), play({ id: '4', participants: [{ athlete: { id: '11' } }, { athlete: { id: '10' } }] }),
    ]), '123', '10');
    expect([result.made, result.attempts, result.unplotted]).toEqual([1, 2, 0]);
    expect(result.shots.map(shot => [shot.id, shot.made, shot.period, shot.x, shot.y])).toEqual([
      ['1', true, 1, 25, 1], ['2', false, 5, 3, 2],
    ]);
  });

  it('reports attempts with missing, sentinel, out-of-court or invalid period data instead of plotting them', () => {
    const result = parseShots(summary([
      play({ coordinate: null }), play({ coordinate: { x: -214748340, y: -214748365 } }),
      play({ coordinate: { x: 25, y: 43 } }), play({ period: {} }),
    ]), '123', '10');
    expect([result.made, result.attempts, result.unplotted, result.shots.length]).toEqual([4, 4, 4, 0]);
  });

  it('rejects mismatched games and absent play-by-play rather than reporting zero attempts', () => {
    expect(() => parseShots(summary([play()]), '999', '10')).toThrow('different game');
    expect(() => parseShots(summary([]), '123', '10')).toThrow('not available');
  });

  it('surfaces HTTP failures and rejects invalid identifiers before a request', async () => {
    const request = vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response('', { status: 503 }));
    try {
      await expect(fetchShots('123', '10')).rejects.toThrow('HTTP 503');
      await expect(fetchShots('123&other=1', '10')).rejects.toThrow('Invalid');
      expect(request).toHaveBeenCalledTimes(1);
    } finally { request.mockRestore(); }
  });
});
