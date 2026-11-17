import type { AppClient, FabricClient } from './client';

type Value = string | number | boolean | null;
export type Row = Record<string, Value>;

export const fields = {
  games: ['Games', ['Jogo Id', 'Data', 'Temporada', 'Fase', 'Mandante Id', 'Mandante', 'Sigla mandante', 'Logo mandante', 'Visitante Id', 'Visitante', 'Sigla visitante', 'Logo visitante', 'Pontos mandante', 'Pontos visitante', 'Situação']],
  players: ['Players', ['Jogador Id', 'Jogador', 'Posição', 'Foto']],
  participation: ['Player Games', ['Jogo Id', 'Jogador Id', 'Data do jogo', 'Time', 'Time Id', 'Temporada', 'Fase', 'Titular', 'Pontos brutos', 'Rebotes brutos', 'Assistências brutas', 'Minutos brutos', 'Arremessos convertidos', 'Arremessos tentados', 'Bolas de três convertidas', 'Bolas de três tentadas', 'Roubos', 'Tocos', 'Perdas de bola', 'Mais menos', 'Lances livres convertidos', 'Lances livres tentados']],
  leagueParticipation: ['Player Games', ['Jogo Id', 'Jogador Id', 'Data do jogo', 'Time', 'Time Id', 'Temporada', 'Fase', 'Pontos brutos', 'Rebotes brutos', 'Assistências brutas', 'Minutos brutos', 'Arremessos convertidos', 'Arremessos tentados', 'Bolas de três convertidas', 'Bolas de três tentadas', 'Roubos', 'Tocos', 'Perdas de bola', 'Mais menos', 'Lances livres convertidos', 'Lances livres tentados']],
  teamStats: ['Team Statistics', ['Jogo Id', 'Time Id', 'Time', 'Rebotes', 'Assistências', 'Roubos', 'Tocos', 'Perdas de bola', 'Arremessos convertidos', 'Arremessos tentados', 'Bolas de três convertidas', 'Bolas de três tentadas', 'Lances livres convertidos', 'Lances livres tentados']],
  periods: ['Periods', ['Jogo Id', 'Time Id', 'Período', 'Descrição do período', 'Pontos no período']],
} as const;

// Snapshot v1 retains its existing keys; only the semantic-model names change.
const modelColumns: Record<string, string> = {
  'Jogo Id': 'Game Id', 'Jogador Id': 'Player Id', 'Data': 'Date', 'Data do jogo': 'Game Date',
  'Temporada': 'Season', 'Fase': 'Season Phase', 'Mandante Id': 'Home Team Id',
  'Mandante': 'Home Team', 'Sigla mandante': 'Home Team Abbreviation', 'Logo mandante': 'Home Team Logo',
  'Visitante Id': 'Away Team Id', 'Visitante': 'Away Team', 'Sigla visitante': 'Away Team Abbreviation',
  'Logo visitante': 'Away Team Logo', 'Pontos mandante': 'Home Score', 'Pontos visitante': 'Away Score',
  'Situação': 'Status', 'Jogador': 'Player', 'Posição': 'Position', 'Foto': 'Photo',
  'Time': 'Team', 'Time Id': 'Team Id', 'Titular': 'Starter', 'Pontos brutos': 'Raw Points',
  'Rebotes brutos': 'Raw Rebounds', 'Assistências brutas': 'Raw Assists', 'Minutos brutos': 'Raw Minutes',
  'Arremessos convertidos': 'Field Goals Made', 'Arremessos tentados': 'Field Goals Attempted',
  'Bolas de três convertidas': 'Three Pointers Made', 'Bolas de três tentadas': 'Three Pointers Attempted',
  'Lances livres convertidos': 'Free Throws Made', 'Lances livres tentados': 'Free Throws Attempted',
  'Roubos': 'Steals', 'Tocos': 'Blocks', 'Perdas de bola': 'Turnovers', 'Mais menos': 'Plus Minus',
  'Rebotes': 'Rebounds', 'Assistências': 'Assists', 'Período': 'Period',
  'Descrição do período': 'Period Description', 'Pontos no período': 'Period Points',
};

function modelColumn(name: string): string {
  const column = modelColumns[name];
  if (!column) throw new Error(`Missing semantic-model mapping for ${name}.`);
  return column;
}

export function idLiteral(id: string): string {
  if (!/^\d+$/.test(id)) throw new Error('Invalid identifier.');
  return `"${id}"`;
}

export function queryFor(kind: keyof typeof fields, filter?: { column: 'Jogo Id' | 'Jogador Id' | 'Time Id'; id: string }) {
  const [table, columns] = fields[kind];
  if (filter && !(columns as readonly string[]).includes(filter.column)) throw new Error('Invalid filter.');
  const source = filter ? `FILTER('${table}', '${table}'[${modelColumn(filter.column)}] = ${idLiteral(filter.id)})` : `'${table}'`;
  return `EVALUATE SELECTCOLUMNS(${source}, ${columns.map((column, i) => `"c${i}", '${table}'[${modelColumn(column)}]`).join(', ')})`;
}

async function executeRows(client: FabricClient, query: string, names: readonly string[]): Promise<Row[]> {
  const result = await client.connectors.nba.executeQuery({ query });
  if (result.status === 'error') throw new Error(`${result.error.category}: ${result.error.message}`);
  return result.table.rows.map((values) => {
    const row: Row = {};
    for (let i = 0; i < names.length; i++) {
      const index = result.table.columns.findIndex((column) => column.name.replace(/^\[|\]$/g, '') === `c${i}`);
      if (index < 0) throw new Error(`Missing response column: ${names[i]}`);
      const value = values[index];
      if (value == null) row[names[i]] = null;
      else if (typeof value === 'string' || typeof value === 'number' || typeof value === 'boolean') row[names[i]] = value;
      else if (typeof value === 'bigint') row[names[i]] = Number(value);
      else if (value instanceof Date) row[names[i]] = value.toISOString();
      else throw new Error(`Unexpected value in column ${names[i]}.`);
    }
    return row;
  });
}

export async function readRows(client: AppClient, kind: keyof typeof fields, filter?: { column: 'Jogo Id' | 'Jogador Id' | 'Time Id'; id: string }): Promise<Row[]> {
  if ('snapshot' in client) {
    if (filter) {
      idLiteral(filter.id);
      if (!(fields[kind][1] as readonly string[]).includes(filter.column)) throw new Error('Invalid filter.');
    }
    const rows = client.snapshot.tables[kind === 'leagueParticipation' ? 'participation' : kind];
    return filter ? rows.filter(row => text(row, filter.column) === filter.id) : rows;
  }
  return executeRows(client, queryFor(kind, filter), fields[kind][1]);
}

export async function readLeagueRows(client: AppClient, season: string, phase: string): Promise<Row[]> {
  if ('snapshot' in client) {
    return client.snapshot.tables.participation.filter(row => text(row, 'Temporada') === season && text(row, 'Fase') === phase);
  }
  const [table, columns] = fields.leagueParticipation;
  const literal = (value: string) => `"${value.replace(/"/g, '""')}"`;
  const source = `FILTER('${table}', '${table}'[Season] = ${literal(season)} && '${table}'[Season Phase] = ${literal(phase)})`;
  const query = `EVALUATE SELECTCOLUMNS(${source}, ${columns.map((column, i) => `"c${i}", '${table}'[${modelColumn(column)}]`).join(', ')})`;
  return executeRows(client, query, columns);
}

export const text = (row: Row, key: string) => String(row[key] ?? '');
export const number = (row: Row, key: string) => typeof row[key] === 'number' ? row[key] as number : null;

export interface PlayerSeasonLine {
  playerId: string;
  games: number;
  points: number | null;
  rebounds: number | null;
  assists: number | null;
  minutes: number | null;
  fieldGoalsMade: number | null;
  fieldGoalsAttempted: number | null;
  threePointersMade: number | null;
  threePointersAttempted: number | null;
  freeThrowsMade: number | null;
  freeThrowsAttempted: number | null;
  steals: number | null;
  blocks: number | null;
  turnovers: number | null;
  plusMinus: number | null;
  fieldGoalPercentage: number | null;
  threePointPercentage: number | null;
}

const perGame = (rows: Row[], key: string) => {
  const values = rows.map(row => number(row, key));
  return values.length && values.every(value => value !== null)
    ? values.reduce<number>((total, value) => total + (value ?? 0), 0) / rows.length
    : null;
};

const total = (rows: Row[], key: string) => {
  const values = rows.map(row => number(row, key));
  return values.length && values.every(value => value !== null)
    ? values.reduce<number>((sum, value) => sum + (value ?? 0), 0)
    : null;
};

export function playerSeasonLines(rows: Row[]): PlayerSeasonLine[] {
  const byPlayer = new Map<string, Row[]>();
  for (const row of rows) {
    const id = text(row, 'Jogador Id');
    if (!id) continue;
    byPlayer.set(id, [...(byPlayer.get(id) ?? []), row]);
  }

  return [...byPlayer].map(([playerId, playerRows]) => {
    const fieldGoalsMade = total(playerRows, 'Arremessos convertidos');
    const fieldGoalsAttempted = total(playerRows, 'Arremessos tentados');
    const threePointersMade = total(playerRows, 'Bolas de três convertidas');
    const threePointersAttempted = total(playerRows, 'Bolas de três tentadas');
    return {
      playerId,
      games: playerRows.length,
      points: perGame(playerRows, 'Pontos brutos'),
      rebounds: perGame(playerRows, 'Rebotes brutos'),
      assists: perGame(playerRows, 'Assistências brutas'),
      minutes: perGame(playerRows, 'Minutos brutos'),
      fieldGoalsMade,
      fieldGoalsAttempted,
      threePointersMade,
      threePointersAttempted,
      freeThrowsMade: total(playerRows, 'Lances livres convertidos'),
      freeThrowsAttempted: total(playerRows, 'Lances livres tentados'),
      steals: perGame(playerRows, 'Roubos'),
      blocks: perGame(playerRows, 'Tocos'),
      turnovers: perGame(playerRows, 'Perdas de bola'),
      plusMinus: perGame(playerRows, 'Mais menos'),
      fieldGoalPercentage: fieldGoalsMade !== null && fieldGoalsAttempted !== null && fieldGoalsAttempted > 0
        ? 100 * fieldGoalsMade / fieldGoalsAttempted : null,
      threePointPercentage: threePointersMade !== null && threePointersAttempted !== null && threePointersAttempted > 0
        ? 100 * threePointersMade / threePointersAttempted : null,
    };
  });
}

export type RankMetric = 'points' | 'rebounds' | 'assists' | 'steals' | 'blocks' | 'minutes' | 'fieldGoalPercentage' | 'threePointPercentage' | 'turnovers' | 'plusMinus';

export function playerRank(lines: PlayerSeasonLine[], playerId: string, key: RankMetric) {
  const value = lines.find(line => line.playerId === playerId)?.[key];
  if (value == null) return null;
  const values = lines.map(line => line[key]).filter((item): item is number => item !== null);
  return { rank: 1 + values.filter(item => item > value).length, total: values.length };
}

export function periodWinner(own: number | null, opponent: number | null) {
  return own !== null && opponent !== null && own > opponent;
}

const easternTeams = new Set([
  'Atlanta Hawks', 'Boston Celtics', 'Brooklyn Nets', 'Charlotte Hornets', 'Chicago Bulls',
  'Cleveland Cavaliers', 'Detroit Pistons', 'Indiana Pacers', 'Miami Heat', 'Milwaukee Bucks',
  'New York Knicks', 'Orlando Magic', 'Philadelphia 76ers', 'Toronto Raptors', 'Washington Wizards',
]);
const westernTeams = new Set([
  'Dallas Mavericks', 'Denver Nuggets', 'Golden State Warriors', 'Houston Rockets', 'LA Clippers',
  'Los Angeles Clippers', 'Los Angeles Lakers', 'Memphis Grizzlies', 'Minnesota Timberwolves',
  'New Orleans Pelicans', 'Oklahoma City Thunder', 'Phoenix Suns', 'Portland Trail Blazers',
  'Sacramento Kings', 'San Antonio Spurs', 'Utah Jazz',
]);

export function conference(name: string): 'East' | 'West' | null {
  return easternTeams.has(name) ? 'East' : westernTeams.has(name) ? 'West' : null;
}

export function teamSummary(games: Row[], stats: Row[], teamId: string) {
  const completed = games.filter(game => text(game, 'Situação') === 'FINAL' &&
    (text(game, 'Mandante Id') === teamId || text(game, 'Visitante Id') === teamId) &&
    number(game, 'Pontos mandante') !== null && number(game, 'Pontos visitante') !== null);
  const teamPoints = completed.map(game => number(game, text(game, 'Mandante Id') === teamId ? 'Pontos mandante' : 'Pontos visitante')!);
  const opponentPoints = completed.map(game => number(game, text(game, 'Mandante Id') === teamId ? 'Pontos visitante' : 'Pontos mandante')!);
  const ids = new Set(completed.map(game => text(game, 'Jogo Id')));
  const matching = stats.filter(row => text(row, 'Time Id') === teamId && ids.has(text(row, 'Jogo Id')));
  const ratio = (numerator: string, denominator: string, factor = 1) => {
    const a = total(matching, numerator);
    const b = total(matching, denominator);
    return a !== null && b !== null && b > 0 ? factor * a / b : null;
  };
  return {
    completedGames: completed.length,
    statGames: matching.length,
    points: teamPoints.length ? teamPoints.reduce((a,b) => a+b, 0) / teamPoints.length : null,
    allowed: opponentPoints.length ? opponentPoints.reduce((a,b) => a+b, 0) / opponentPoints.length : null,
    average: (key: string) => perGame(matching, key),
    ratio,
  };
}

export interface Standing {
  id: string;
  name: string;
  logo: string;
  abbreviation: string;
  wins: number;
  losses: number;
  pointsDiff: number;
  recent: ('V' | 'D')[];
  streak: string | null;
}

export function standings(games: Row[]): Standing[] {
  const teams = new Map<string, Standing>();
  const history = new Map<string, { date: string; result: 'V' | 'D' | null }[]>();
  for (const game of games) {
    if (text(game, 'Situação') !== 'FINAL') continue;
    const home = number(game, 'Pontos mandante');
    const away = number(game, 'Pontos visitante');
    const valid = home !== null && away !== null && home !== away;
    for (const side of ['mandante', 'visitante'] as const) {
      const id = text(game, side === 'mandante' ? 'Mandante Id' : 'Visitante Id');
      if (!id) throw new Error('A completed game is missing a team identifier.');
      const won = valid && (side === 'mandante' ? home > away : away > home);
      const results = history.get(id) ?? [];
      results.push({ date: text(game, 'Data').slice(0, 10), result: valid ? (won ? 'V' : 'D') : null });
      history.set(id, results);
      if (!valid) continue;
      const team = teams.get(id) ?? { id, name: text(game, side === 'mandante' ? 'Mandante' : 'Visitante'),
        logo: text(game, `Logo ${side}`), abbreviation: text(game, `Sigla ${side}`), wins: 0, losses: 0,
        pointsDiff: 0, recent: [], streak: null };
      if (won) team.wins++; else team.losses++;
      team.pointsDiff += side === 'mandante' ? home - away : away - home;
      teams.set(id, team);
    }
  }
  for (const team of teams.values()) {
    const results = (history.get(team.id) ?? []).sort((a, b) => b.date.localeCompare(a.date));
    const ordered = results.every((game, i) => /^\d{4}-\d{2}-\d{2}$/.test(game.date) &&
      (i === 0 || game.date !== results[i - 1].date));
    if (!ordered) continue;
    const recent: ('V' | 'D')[] = [];
    for (const game of results.slice(0, 5)) {
      if (game.result === null) break;
      recent.push(game.result);
    }
    team.recent = recent.reverse();
    const first = results[0]?.result;
    if (!first) continue;
    let length = 0;
    for (const game of results) {
      if (game.result === null) { length = 0; break; }
      if (game.result !== first) break;
      length++;
    }
    team.streak = length ? `${first}${length}` : null;
  }
  return [...teams.values()].sort((a, b) => b.wins / (b.wins + b.losses) - a.wins / (a.wins + a.losses) || a.name.localeCompare(b.name));
}
