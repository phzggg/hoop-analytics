/// <reference types="node" />

import { execFileSync, spawnSync } from 'node:child_process';
import { randomUUID } from 'node:crypto';
import { existsSync, readFileSync, unlinkSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { describe, expect, it } from 'vitest';

describe('snapshot publisher generation', () => {
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
      const invalid = spawnSync(process.execPath, ['scripts/build-publisher.mjs', 'public-db', 'invalid', output]);
      expect(invalid.status).not.toBe(0);
    } finally {
      if (existsSync(output)) unlinkSync(output);
    }
  });
});
