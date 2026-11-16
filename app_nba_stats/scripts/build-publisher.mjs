import { readFile, writeFile } from 'node:fs/promises';
import { fields, queryFor } from '../src/data.ts';

const [databaseName, modelId, output] = process.argv.slice(2);
const uuid = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
if (!databaseName || !uuid.test(modelId ?? '') || !output) {
  throw new Error('Usage: node scripts\\build-publisher.mjs <database-name> <model-id> <output-ipynb>');
}
const kinds = ['games', 'players', 'participation', 'teamStats', 'periods'];
const specification = Object.fromEntries(kinds.map(kind => [
  kind, { table: fields[kind][0], columns: fields[kind][1], query: queryFor(kind) },
]));
let source = await readFile(new URL('./publish-snapshot.py', import.meta.url), 'utf8');
if (!source.includes('EXPORT_FIELDS = None') || !source.includes('DESTINATION_DATABASE = None') ||
    !source.includes('MODEL_ID = None')) {
  throw new Error('Publisher template could not be configured.');
}
source = source.replace('EXPORT_FIELDS = None', `EXPORT_FIELDS = ${JSON.stringify(specification)}`)
  .replace('DESTINATION_DATABASE = None', `DESTINATION_DATABASE = ${JSON.stringify(databaseName)}`)
  .replace('MODEL_ID = None', `MODEL_ID = ${JSON.stringify(modelId)}`);
const notebook = {
  cells: [{ cell_type: 'code', execution_count: null, metadata: {}, outputs: [], source: source.split(/(?<=\n)/) }],
  metadata: { kernelspec: { display_name: 'Synapse PySpark', language: 'python', name: 'synapse_pyspark' }, language_info: { name: 'python' } },
  nbformat: 4, nbformat_minor: 5,
};
await writeFile(output, JSON.stringify(notebook), 'utf8');
