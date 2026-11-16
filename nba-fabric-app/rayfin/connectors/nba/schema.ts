import type { GraphQLBackedConnector } from '@microsoft/rayfin-connector-fabric-graphql';
import type { ConnectorConfig } from '@microsoft/rayfin-connectors';
import { GoldEspnPlayerGames } from './GoldEspnPlayerGames.js';
import { GoldEspnPlayerSummary } from './GoldEspnPlayerSummary.js';

export { GoldEspnPlayerGames } from './GoldEspnPlayerGames.js';
export { GoldEspnPlayerSummary } from './GoldEspnPlayerSummary.js';

export const connectorConfig = {
  connector: 'fabric-sqlanalytics',
  operations: ['read'],
  entities: { GoldEspnPlayerGames, GoldEspnPlayerSummary },
} as const satisfies ConnectorConfig;

export type NbaSchema = GraphQLBackedConnector<
  { GoldEspnPlayerGames: typeof GoldEspnPlayerGames; GoldEspnPlayerSummary: typeof GoldEspnPlayerSummary },
  typeof connectorConfig
>;
