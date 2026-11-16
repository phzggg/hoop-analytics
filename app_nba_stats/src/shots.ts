export interface Shot {
  id: string;
  period: number;
  x: number;
  y: number;
  made: boolean;
  description: string;
}

export interface ShotData {
  shots: Shot[];
  attempts: number;
  made: number;
  unplotted: number;
}

const object = (value: unknown): Record<string, unknown> | null =>
  value !== null && typeof value === 'object' && !Array.isArray(value) ? value as Record<string, unknown> : null;

export function parseShots(payload: unknown, gameId: string, playerId: string): ShotData {
  const data = object(payload);
  if (String(object(data?.header)?.id ?? '') !== gameId) throw new Error('ESPN returned a different game.');
  if (!Array.isArray(data?.plays) || data.plays.length === 0) throw new Error('Play-by-play is not available for this game.');
  const shots: Shot[] = [];
  let attempts = 0;
  let made = 0;
  let unplotted = 0;
  for (const entry of data.plays) {
    const play = object(entry);
    if (!play || play.shootingPlay !== true || (play.pointsAttempted !== 2 && play.pointsAttempted !== 3)) continue;
    const first = Array.isArray(play.participants) ? object(play.participants[0]) : null;
    if (String(object(first?.athlete)?.id ?? '') !== playerId) continue;
    attempts++;
    if (play.scoringPlay === true) made++;
    const coord = object(play.coordinate);
    const period = object(play.period)?.number;
    const x = coord?.x;
    const y = coord?.y;
    if (typeof play.scoringPlay !== 'boolean' || typeof x !== 'number' || !Number.isFinite(x) ||
      typeof y !== 'number' || !Number.isFinite(y) || x < 0 || x > 50 || y < -4.25 || y > 42.75 ||
      typeof period !== 'number' || !Number.isInteger(period) || period < 1) {
      unplotted++;
      continue;
    }
    shots.push({
      id: String(play.id ?? `shot-${attempts}`), period, x, y, made: play.scoringPlay,
      description: typeof play.text === 'string' ? play.text : 'Field-goal attempt',
    });
  }
  return { shots, attempts, made, unplotted };
}

export async function fetchShots(gameId: string, playerId: string): Promise<ShotData> {
  if (!/^\d+$/.test(gameId) || !/^\d+$/.test(playerId)) throw new Error('Invalid game or player identifier.');
  const response = await fetch(`https://site.api.espn.com/apis/site/v2/sports/basketball/nba/summary?event=${gameId}`, { credentials: 'omit' });
  if (!response.ok) throw new Error(`ESPN request failed (HTTP ${response.status}).`);
  return parseShots(await response.json(), gameId, playerId);
}
