import { describe, expect, it, vi } from 'vitest';
import { fields, readLeagueRows, readRows } from './data';
import { loadPublicSnapshot, parsePublicSnapshot } from './snapshot';
import { decodePublishedSnapshot } from './public-data';

const row = (kind: Exclude<keyof typeof fields, 'leagueParticipation'>, values: Record<string, string | number | boolean | null> = {}) =>
  Object.fromEntries(fields[kind][1].map(column => [column, values[column] ?? null]));

const fixture = () => ({
  version: 1,
  generatedAt: '2026-11-16T12:00:00Z',
  tables: {
    games: [row('games', { 'Jogo Id': '1' })],
    players: [row('players', { 'Jogador Id': '10' })],
    participation: [
      row('participation', { 'Jogo Id': '1', 'Jogador Id': '10', 'Time Id': '2', 'Temporada': '2026-27', 'Fase': 'Regular Season' }),
      row('participation', { 'Jogo Id': '2', 'Jogador Id': '11', 'Time Id': '3', 'Temporada': '2026-27', 'Fase': 'Playoffs' }),
    ],
    teamStats: [],
    periods: [],
  },
});

describe('public snapshot', () => {
  it('filters game, team, player and league rows without querying the model', async () => {
    const client = { snapshot: parsePublicSnapshot(fixture()) };
    expect(await readRows(client, 'participation', { column: 'Jogo Id', id: '1' })).toHaveLength(1);
    expect(await readRows(client, 'participation', { column: 'Time Id', id: '3' })).toHaveLength(1);
    expect(await readRows(client, 'participation', { column: 'Jogador Id', id: '10' })).toHaveLength(1);
    expect(await readLeagueRows(client, '2026-27', 'Regular Season')).toHaveLength(1);
    await expect(readRows(client, 'games', { column: 'Time Id', id: '1' })).rejects.toThrow('Invalid filter');
    await expect(readRows(client, 'games', { column: 'Jogo Id', id: 'invalid' })).rejects.toThrow('Invalid identifier');
  });

  it('rejects missing tables, incomplete rows and unexpected fields', () => {
    const missing = fixture();
    expect(() => parsePublicSnapshot({ ...missing, tables: { ...missing.tables, periods: undefined } })).toThrow('Missing snapshot table');
    expect(() => parsePublicSnapshot({ ...missing, tables: { ...missing.tables, games: [{ 'Jogo Id': '1' }] } })).toThrow('Invalid or missing');
    expect(() => parsePublicSnapshot({ ...missing, tables: { ...missing.tables, games: [{ ...missing.tables.games[0], privateField: 'secret' }] } })).toThrow('Invalid snapshot row');
    expect(() => parsePublicSnapshot({ ...missing, generatedAt: 'invalid' })).toThrow('Invalid public snapshot metadata');
  });

  it('surfaces HTTP failures instead of presenting empty data', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, status: 503 }));
    try {
      await expect(loadPublicSnapshot('/snapshot.json')).rejects.toThrow('HTTP 503');
    } finally {
      vi.unstubAllGlobals();
    }
  });

  it('accepts a complete version and rejects missing parts or a wrong checksum', async () => {
    const bytes = new TextEncoder().encode(JSON.stringify(fixture()));
    const digest = Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256', bytes)),
      byte => byte.toString(16).padStart(2, '0')).join('');
    const compressed = await new Response(new Blob([bytes]).stream().pipeThrough(new CompressionStream('gzip'))).arrayBuffer();
    const encoded = btoa(String.fromCharCode(...new Uint8Array(compressed)));
    const midpoint = Math.floor(encoded.length / 2);
    const parts = [{ part: 0, content: encoded.slice(0, midpoint) }, { part: 1, content: encoded.slice(midpoint) }];
    const version = { parts: 2, sha256: digest, createdAt: fixture().generatedAt };
    expect((await decodePublishedSnapshot(version, parts)).tables.games).toHaveLength(1);
    await expect(decodePublishedSnapshot(version, parts.slice(0, 1))).rejects.toThrow('incomplete');
    await expect(decodePublishedSnapshot({ ...version, sha256: '0'.repeat(64) }, parts)).rejects.toThrow('integrity');
  });
});
