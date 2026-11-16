import { execFileSync } from 'node:child_process';
import { writeFile, rename, unlink } from 'node:fs/promises';
import { fields, queryFor } from '../src/data.ts';

const kinds = ['games', 'players', 'participation', 'teamStats', 'periods'];
const [workspaceId, modelId, destination] = process.argv.slice(2);
const uuid = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
if (!uuid.test(workspaceId ?? '') || !uuid.test(modelId ?? '') || !destination) {
  throw new Error('Usage: node scripts\\export-snapshot.mjs <workspace-id> <model-id> <output-file>');
}

const token = process.platform === 'win32'
  ? execFileSync(process.env.ComSpec || 'cmd.exe', ['/d', '/s', '/c', 'az.cmd account get-access-token --resource https://analysis.windows.net/powerbi/api --query accessToken -o tsv'], { encoding: 'utf8' }).trim()
  : execFileSync('az', ['account', 'get-access-token', '--resource', 'https://analysis.windows.net/powerbi/api', '--query', 'accessToken', '-o', 'tsv'], { encoding: 'utf8' }).trim();
if (!token) throw new Error('Azure CLI did not return an access token.');

async function query(dax) {
  const response = await fetch(`https://api.powerbi.com/v1.0/myorg/groups/${workspaceId}/datasets/${modelId}/executeQueries`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
    body: JSON.stringify({ queries: [{ query: dax }], serializerSettings: { includeNulls: true } }),
  });
  if (!response.ok) throw new Error(`Model query failed (HTTP ${response.status}).`);
  const result = await response.json();
  const queryResult = result.results?.[0];
  const table = queryResult?.tables?.[0];
  if (result.error || queryResult?.error || table?.error || !Array.isArray(table?.rows)) {
    throw new Error('Model query returned an error or an invalid result.');
  }
  return table.rows;
}

const tables = {};
for (const kind of kinds) {
  const [table, columns] = fields[kind];
  const countRows = await query(`EVALUATE ROW("n", COUNTROWS('${table}'))`);
  const count = countRows[0]?.['[n]'];
  if (!Number.isInteger(count) || count < 0) throw new Error(`Invalid row count for ${kind}.`);
  if (count > 100000 || count * columns.length > 1000000) throw new Error(`${kind} exceeds query limits; partitioned export is required.`);
  const source = await query(queryFor(kind));
  if (source.length !== count) throw new Error(`${kind} returned ${source.length} of ${count} rows; snapshot was not written.`);
  tables[kind] = source.map((record, rowIndex) => {
    const row = {};
    columns.forEach((column, index) => {
      const key = `[c${index}]`;
      if (!Object.hasOwn(record, key)) throw new Error(`Missing ${column} in ${kind} row ${rowIndex + 1}.`);
      const value = record[key];
      if (value !== null && typeof value !== 'string' && typeof value !== 'number' && typeof value !== 'boolean') {
        throw new Error(`Invalid ${column} in ${kind} row ${rowIndex + 1}.`);
      }
      row[column] = value;
    });
    return row;
  });
  console.log(`${kind}: ${count} rows`);
}
if (!tables.games.length || !tables.players.length) throw new Error('Required game or player data is empty.');
const snapshot = { version: 1, generatedAt: new Date().toISOString(), tables };
const temporary = `${destination}.${process.pid}.tmp`;
try {
  await writeFile(temporary, JSON.stringify(snapshot), { encoding: 'utf8', flag: 'wx' });
  await rename(temporary, destination);
} catch (error) {
  try {
    await unlink(temporary);
  } catch (cleanupError) {
    if (cleanupError.code !== 'ENOENT') throw new AggregateError([error, cleanupError], 'Snapshot export and temporary-file cleanup failed.');
  }
  throw error;
}
console.log(`Snapshot written to ${destination}.`);
