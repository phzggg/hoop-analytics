import { anonymous, entity, int, text, uuid } from '@microsoft/rayfin-core';

@entity()
@anonymous('read')
export class SnapshotVersion {
  @uuid() id!: string;
  @text({ max: 30 }) createdAt!: string;
  @int() parts!: number;
  @text({ max: 64 }) sha256!: string;
}
