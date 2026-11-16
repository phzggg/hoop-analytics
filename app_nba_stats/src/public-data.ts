import { RayfinClient, resolveRayfinConfig } from '@microsoft/rayfin-client';
import type { PublicDataSchema } from '../rayfin/data/schema';
import { parsePublicSnapshot } from './snapshot';

export async function decodePublishedSnapshot(
  version: { parts: number; sha256: string; createdAt: string },
  parts: { part: number; content: string }[],
) {
  if (parts.length !== version.parts || parts.some((part, index) => part.part !== index || !part.content)) {
    throw new Error('Public snapshot is incomplete.');
  }
  const binary = atob(parts.map(part => part.content).join(''));
  const compressed = Uint8Array.from(binary, character => character.charCodeAt(0));
  const stream = new Blob([compressed]).stream().pipeThrough(new DecompressionStream('gzip'));
  const bytes = await new Response(stream).arrayBuffer();
  const digest = Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256', bytes)),
    byte => byte.toString(16).padStart(2, '0')).join('');
  if (digest !== version.sha256) throw new Error('Public snapshot integrity check failed.');
  const snapshot = parsePublicSnapshot(JSON.parse(new TextDecoder('utf-8', { fatal: true }).decode(bytes)));
  if (Date.parse(snapshot.generatedAt) !== new Date(version.createdAt).getTime()) {
    throw new Error('Public snapshot timestamp does not match.');
  }
  return snapshot;
}

export async function loadVersionedSnapshot(client: RayfinClient<PublicDataSchema>) {
  const versions = await client.data.SnapshotVersion.select(['id', 'createdAt', 'parts', 'sha256'])
    .orderBy({ createdAt: 'desc' }).first(1).execute();
  const version = versions[0];
  if (!version || !Number.isInteger(version.parts) || version.parts < 1 || version.parts > 5000 ||
      !/^[0-9a-f]{64}$/.test(version.sha256)) {
    throw new Error('Public snapshot version is missing or invalid.');
  }
  const parts: { part: number; content: string }[] = [];
  let cursor: string | undefined;
  do {
    let query = client.data.SnapshotPart.select(['part', 'content'])
      .where({ versionId: { eq: version.id.toLowerCase() } })
      .orderBy({ part: 'asc' }).first(100);
    if (cursor) query = query.after(cursor);
    const page = await query.executePaginated();
    parts.push(...page.items);
    if (parts.length > version.parts) throw new Error('Public snapshot has unexpected parts.');
    if (!page.hasNextPage) break;
    if (!page.endCursor || page.endCursor === cursor) throw new Error('Public snapshot pagination failed.');
    cursor = page.endCursor;
  } while (true);
  return decodePublishedSnapshot(version, parts);
}

export async function loadPublishedSnapshot() {
  const config = await resolveRayfinConfig({
    apiUrl: import.meta.env.VITE_RAYFIN_API_URL,
    publishableKey: import.meta.env.VITE_RAYFIN_PUBLISHABLE_KEY,
  });
  if (!config.baseUrl || !config.publishableKey) throw new Error('Public data configuration is incomplete.');
  const client = new RayfinClient<PublicDataSchema>({
    baseUrl: config.baseUrl, publishableKey: config.publishableKey, authStorage: false,
  });
  return loadVersionedSnapshot(client);
}
