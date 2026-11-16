import { getRayfinClient } from './lib/rayfin-client';

/** Gold contract used by the dashboard. */
export interface PlayerSummary {
  player_id: string;
  player_name: string;
  games_played: number | null;
  total_points: number | null;
  avg_points: number | null;
  avg_rebounds: number | null;
  avg_assists: number | null;
  avg_minutes: number | null;
}

export interface PlayerGame {
  game_id: string;
  game_date: string | null;
  team_id: string | null;
  team_name: string | null;
  player_id: string;
  player_name: string;
  minutes: number | null;
  points: number | null;
  rebounds: number | null;
  assists: number | null;
  updated_at: string | null;
}

/** Interface keeps the authenticated connector separate from presentation. */
export interface PlayerDataSource {
  listPlayers(): Promise<PlayerSummary[]>;
  listGames(playerId: string): Promise<PlayerGame[]>;
}

export class SourceNotReadyError extends Error {
  constructor() {
    super('Conector de jogadores ainda não configurado.');
    this.name = 'SourceNotReadyError';
  }
}

export class SourceContractError extends Error {
  constructor() {
    super('A resposta do conector não corresponde ao contrato de jogadores.');
    this.name = 'SourceContractError';
  }
}

export interface PlayerPages {
  summary(cursor?: string): Promise<Page>;
  games(playerId: string, cursor?: string): Promise<Page>;
}
interface Page {
  items: unknown[];
  hasNextPage: boolean;
  endCursor?: string;
}

const summaryFields = [
  'playerId', 'playerName', 'gamesPlayed', 'totalPoints',
  'avgPoints', 'avgRebounds', 'avgAssists', 'avgMinutes',
] as const;
const gameFields = [
  'gameId', 'gameDate', 'teamId', 'teamName', 'playerId',
  'playerName', 'minutes', 'points', 'rebounds', 'assists', 'updatedAt',
] as const;
const nullableNumber = (value: unknown) => value === null || (typeof value === 'number' && Number.isFinite(value));
const nullableString = (value: unknown) => value === null || typeof value === 'string';

function isRecord(value: unknown): value is Record<string, unknown> {
  return value !== null && typeof value === 'object' && !Array.isArray(value);
}
function isSummary(value: unknown): value is PlayerSummary {
  if (!isRecord(value) || typeof value.player_id !== 'string' || typeof value.player_name !== 'string') return false;
  return ['games_played', 'total_points', 'avg_points', 'avg_rebounds', 'avg_assists', 'avg_minutes']
    .every((field) => nullableNumber(value[field]));
}
function isGame(value: unknown): value is PlayerGame {
  if (!isRecord(value) || typeof value.game_id !== 'string' || typeof value.player_id !== 'string' || typeof value.player_name !== 'string') return false;
  return ['game_date', 'team_id', 'team_name', 'updated_at'].every((field) => nullableString(value[field]))
    && ['minutes', 'points', 'rebounds', 'assists'].every((field) => nullableNumber(value[field]));
}

async function readPages<T>(
  fetchPage: (cursor?: string) => Promise<Page>,
  normalize: (row: unknown) => unknown,
  validate: (row: unknown) => row is T,
): Promise<T[]> {
  const rows: T[] = [];
  let cursor: string | undefined;
  // Fail explicitly instead of presenting a truncated result as complete.
  for (let pageNumber = 0; pageNumber < 25; pageNumber += 1) {
    const page = await fetchPage(cursor);
    if (!Array.isArray(page.items)) throw new SourceContractError();
    const normalized = page.items.map(normalize);
    if (!normalized.every(validate)) throw new SourceContractError();
    rows.push(...normalized);
    if (!page.hasNextPage) return rows;
    if (!page.endCursor || page.endCursor === cursor) throw new SourceContractError();
    cursor = page.endCursor;
  }
  throw new SourceContractError();
}

/** Builds real bounded, read-only queries; no SQL or user input is concatenated. */
export function createRayfinPlayerDataSource(
  pages: PlayerPages,
): PlayerDataSource {
  return {
    async listPlayers() {
      return readPages((cursor) => pages.summary(cursor), normalizeSummary, isSummary);
    },
    async listGames(playerId) {
      return readPages((cursor) => pages.games(playerId, cursor), normalizeGame, isGame);
    },
  };
}

function safeInteger(value: unknown): unknown {
  if (typeof value === 'string' && /^-?\d+$/.test(value)) {
    const number = Number(value);
    return Number.isSafeInteger(number) ? number : value;
  }
  return typeof value === 'number' && !Number.isSafeInteger(value) ? undefined : value;
}

function normalizeSummary(row: unknown): unknown {
  if (!isRecord(row)) return row;
  return {
    player_id: row.playerId, player_name: row.playerName,
    games_played: safeInteger(row.gamesPlayed), total_points: safeInteger(row.totalPoints),
    avg_points: row.avgPoints, avg_rebounds: row.avgRebounds,
    avg_assists: row.avgAssists, avg_minutes: row.avgMinutes,
  };
}

function normalizeGame(row: unknown): unknown {
  if (!isRecord(row)) return row;
  return {
    game_id: row.gameId, game_date: row.gameDate, team_id: row.teamId,
    team_name: row.teamName, player_id: row.playerId, player_name: row.playerName,
    minutes: row.minutes, points: row.points, rebounds: row.rebounds,
    assists: row.assists, updated_at: row.updatedAt,
  };
}

/** Actual client calls are read-only and use structured filters, never SQL text. */
export const playerDataSource = createRayfinPlayerDataSource({
  async summary(cursor) {
    const client = await getRayfinClient();
    let query = client.connectors.nba.GoldEspnPlayerSummary.select([...summaryFields]).first(100);
    if (cursor) query = query.after(cursor);
    return query.executePaginated();
  },
  async games(playerId, cursor) {
    const client = await getRayfinClient();
    let query = client.connectors.nba.GoldEspnPlayerGames.select([...gameFields])
      .where({ playerId: { eq: playerId } }).first(100);
    if (cursor) query = query.after(cursor);
    return query.executePaginated();
  },
});

/** Do not display raw provider errors, which may contain endpoint details. */
export function explainDataError(error: unknown): string {
  if (error instanceof SourceNotReadyError) {
    return 'O conector de jogadores ainda não está configurado. Aguarde a publicação das tabelas Gold e a verificação do endpoint SQL.';
  }
  if (error instanceof SourceContractError) {
    return 'O esquema ou a paginação retornados pelo endpoint não correspondem ao contrato esperado. Verifique os metadados antes de usar o painel.';
  }
  const message = error instanceof Error ? error.message : String(error);
  if (/\b(401|403)\b|permission|forbidden|unauthori[sz]ed|access denied/i.test(message)) {
    return 'Acesso negado. Verifique a permissão de leitura no app e no Lakehouse para esta conta.';
  }
  if (/invalid object|not found|does not exist|not exist|404/i.test(message)) {
    return 'A tabela de jogadores não está disponível no endpoint SQL. Verifique a criação da Gold e a sincronização dos metadados.';
  }
  return 'Não foi possível consultar os dados. Verifique a conexão e tente novamente.';
}

export function formatMetric(value: number | null, digits = 1): string {
  return value == null || !Number.isFinite(value)
    ? '—'
    : new Intl.NumberFormat('pt-BR', { maximumFractionDigits: digits }).format(value);
}

export function formatGameDate(value: string | null): string {
  if (!value) return '—';
  // SQL date-only values are calendar dates, not instants in the user's zone.
  const date = /^(\d{4})-(\d{2})-(\d{2})/.exec(value);
  return date ? `${date[3]}/${date[2]}/${date[1]}` : '—';
}
