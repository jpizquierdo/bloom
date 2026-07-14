import type { CreateClientConfig } from "@/client/client.gen"
import { getToken } from "@/lib/token"

/**
 * Empty base URL = same origin, which is how the app ships: the API serves the built UI, so
 * requests go to a relative /api/v1/… and work behind any hostname without a rebuild. In dev
 * that relative path is proxied to the API by Vite (see vite.config.ts). Set VITE_API_URL only
 * to point the UI at an API somewhere else.
 */
export const createClientConfig: CreateClientConfig = (config) => ({
  ...config,
  baseUrl: import.meta.env.VITE_API_URL ?? "",
  auth: () => getToken() ?? undefined,
})
