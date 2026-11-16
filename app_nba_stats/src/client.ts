import { ConnectorsRayfinClient, resolveRayfinConfig } from '@microsoft/rayfin-client';
import { fabricSemanticModel } from '@microsoft/rayfin-connector-fabric-semanticmodel';
import { connectorConfig, type NbaSchema } from '../rayfin/connectors/nba/schema';
import type { PublicSnapshot } from './snapshot';

export async function createClient() {
  const config = await resolveRayfinConfig({
    apiUrl: import.meta.env.VITE_RAYFIN_API_URL,
    publishableKey: import.meta.env.VITE_RAYFIN_PUBLISHABLE_KEY,
    workspaceId: import.meta.env.VITE_FABRIC_WORKSPACE_ID,
    itemId: import.meta.env.VITE_FABRIC_ITEM_ID,
    portalUrl: import.meta.env.VITE_FABRIC_PORTAL_URL,
  });
  if (!config.baseUrl || !config.publishableKey || !config.runtimeConfig?.workspaceId ||
      !config.runtimeConfig.itemId || !config.runtimeConfig.portalUrl) {
    throw new Error('Fabric app configuration is incomplete. Publish the app to enable access.');
  }
  const client = new ConnectorsRayfinClient<Record<string, never>, Record<string, never>, { nba: NbaSchema }>(
    { baseUrl: config.baseUrl, publishableKey: config.publishableKey, authStorage: true,
      runtimeConfig: config.runtimeConfig, connectors: { nba: connectorConfig } },
    { nba: fabricSemanticModel() },
  );
  return {
    client,
    options: {
      workspaceId: config.runtimeConfig.workspaceId,
      projectId: config.runtimeConfig.itemId,
      fabricPortalUrl: config.runtimeConfig.portalUrl,
      returnOrigin: window.location.origin,
    },
  };
}

export type FabricClient = Awaited<ReturnType<typeof createClient>>['client'];
export type AppClient = FabricClient | { snapshot: PublicSnapshot; scheduled?: boolean };
