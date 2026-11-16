import { fields, type Row } from './data';

type SnapshotKind = 'games' | 'players' | 'participation' | 'teamStats' | 'periods';
const kinds: SnapshotKind[] = ['games', 'players', 'participation', 'teamStats', 'periods'];

export interface PublicSnapshot {
  version: 1;
  generatedAt: string;
  tables: Record<SnapshotKind, Row[]>;
}

function object(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

export function parsePublicSnapshot(value: unknown): PublicSnapshot {
  if (!object(value) || value.version !== 1 || typeof value.generatedAt !== 'string' ||
      !Number.isFinite(Date.parse(value.generatedAt)) || !object(value.tables)) {
    throw new Error('Invalid public snapshot metadata.');
  }
  const tables = {} as Record<SnapshotKind, Row[]>;
  for (const kind of kinds) {
    const source = value.tables[kind];
    if (!Array.isArray(source)) throw new Error(`Missing snapshot table: ${kind}.`);
    const columns: readonly string[] = fields[kind][1];
    tables[kind] = source.map((item, index) => {
      if (!object(item) || Object.keys(item).some(key => !columns.includes(key))) {
        throw new Error(`Invalid snapshot row: ${kind} #${index + 1}.`);
      }
      const row: Row = {};
      for (const column of columns) {
        const cell = item[column];
        if (cell === null || typeof cell === 'string' || typeof cell === 'boolean' ||
            (typeof cell === 'number' && Number.isFinite(cell))) row[column] = cell;
        else throw new Error(`Invalid or missing ${column} in ${kind} #${index + 1}.`);
      }
      return row;
    });
  }
  if (!tables.games.length || !tables.players.length) throw new Error('The public snapshot is incomplete.');
  return { version: 1, generatedAt: value.generatedAt, tables };
}

export async function loadPublicSnapshot(url: string): Promise<PublicSnapshot> {
  const response = await fetch(url);
  if (!response.ok) throw new Error(`Snapshot request failed (HTTP ${response.status}).`);
  return parsePublicSnapshot(await response.json());
}
