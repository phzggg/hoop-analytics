import { anonymous, entity, int, text, uuid } from '@microsoft/rayfin-core';

@entity()
@anonymous('read')
export class SnapshotPart {
  @uuid() id!: string;
  @text({ max: 36 }) versionId!: string;
  @int() part!: number;
  @text({ max: 3900 }) content!: string;
}
