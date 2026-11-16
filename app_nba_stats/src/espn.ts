const object = (value: unknown): Record<string, unknown> | null =>
  value !== null && typeof value === 'object' && !Array.isArray(value) ? value as Record<string, unknown> : null;

async function getJson(url: string): Promise<unknown> {
  const response = await fetch(url, { credentials: 'omit' });
  if (!response.ok) throw new Error(`ESPN request failed (HTTP ${response.status}).`);
  return response.json();
}

export function seasonProgress(start: string, end: string, now: number) {
  const first = Date.parse(start), last = Date.parse(end);
  if (!Number.isFinite(first) || !Number.isFinite(last) || last <= first || !Number.isFinite(now)) throw new Error('Invalid season dates.');
  return Math.max(0, Math.min(100, 100 * (now - first) / (last - first)));
}

export async function fetchSeasonDates(season: string) {
  const match = /^(\d{4})-(\d{2})$/.exec(season);
  if (!match || (Number(match[1]) + 1) % 100 !== Number(match[2])) throw new Error('Unrecognized season.');
  const year = Number(match[1]) + 1;
  const base = `https://sports.core.api.espn.com/v2/sports/basketball/leagues/nba/seasons/${year}/types`;
  const [regular, postseason] = await Promise.all([getJson(`${base}/2`), getJson(`${base}/3`)]);
  const start = object(regular)?.startDate, end = object(postseason)?.endDate;
  if (typeof start !== 'string' || typeof end !== 'string') throw new Error('Season dates are unavailable.');
  seasonProgress(start, end, Date.now());
  return { start, end };
}

export async function fetchPlayerProfile(id: string) {
  if (!/^\d+$/.test(id)) throw new Error('Invalid player identifier.');
  const athlete = object(await getJson(`https://sports.core.api.espn.com/v2/sports/basketball/leagues/nba/athletes/${id}`));
  if (String(athlete?.id ?? '') !== id) throw new Error('ESPN returned a different player.');
  const value = (key: string) => typeof athlete?.[key] === 'string' ? athlete[key] as string : '';
  return {
    birthDate: value('dateOfBirth'), height: value('displayHeight'), weight: value('displayWeight'),
    age: typeof athlete?.age === 'number' && Number.isFinite(athlete.age) ? athlete.age : null,
    jersey: value('jersey'),
    country: typeof object(athlete?.birthPlace)?.country === 'string' ? String(object(athlete?.birthPlace)?.country) : '',
  };
}
