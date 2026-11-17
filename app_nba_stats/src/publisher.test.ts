/// <reference types="node" />

import { execFileSync, spawnSync } from 'node:child_process';
import { randomUUID } from 'node:crypto';
import { existsSync, readFileSync, unlinkSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { describe, expect, it } from 'vitest';
import { fields, queryFor } from './data';

describe('snapshot publisher generation', () => {
  it('references columns present in the prepared semantic model', () => {
    for (const kind of Object.keys(fields) as (keyof typeof fields)[]) {
      const [table] = fields[kind];
      const definition = readFileSync(new URL(`../../fabric/semantic-model/definition/tables/${table}.tmdl`, import.meta.url), 'utf8');
      const columns = new Set([...definition.matchAll(/^\s*column (.+)$/gm)]
        .map(match => match[1].replace(/^'|'$/g, '')));
      const references = [...queryFor(kind).matchAll(/'([^']+)'\[([^\]]+)\]/g)];
      expect(references.length).toBe(fields[kind][1].length);
      for (const [, referencedTable, column] of references) {
        expect(referencedTable).toBe(table);
        expect(columns.has(column), `${table}[${column}]`).toBe(true);
      }
    }
  });

  it('requires a model ID and injects it into the generated notebook', () => {
    const output = join(tmpdir(), `hoop-publisher-${randomUUID()}.ipynb`);
    const modelId = '12345678-1234-1234-1234-123456789abc';
    try {
      execFileSync(process.execPath, ['scripts/build-publisher.mjs', 'public-db', modelId, output]);
      const notebook = JSON.parse(readFileSync(output, 'utf8'));
      const source = notebook.cells[0].source.join('');
      expect(source).toContain(`MODEL_ID = "${modelId}"`);
      expect(source).toContain('DESTINATION_DATABASE = "public-db"');
      expect(source).toContain('"participation"');
      expect(source).toContain(`'Player Games'[Game Id]`);
      expect(source).toContain('"Jogo Id"');
      const invalid = spawnSync(process.execPath, ['scripts/build-publisher.mjs', 'public-db', 'invalid', output]);
      expect(invalid.status).not.toBe(0);
    } finally {
      if (existsSync(output)) unlinkSync(output);
    }
  });
});
