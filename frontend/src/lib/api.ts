import { client } from "@/client/client.gen"
import { clearToken } from "@/lib/token"

/** The token has no refresh flow, so an expired one can only be resolved by logging in again. */
client.interceptors.response.use((response) => {
  if (response.status === 401 && !window.location.pathname.startsWith("/login")) {
    clearToken()
    window.location.href = "/login"
  }
  return response
})

/** Pull a readable message out of a FastAPI error body (`detail`, string or 422 list). */
export function errorMessage(error: unknown, fallback = "Something went wrong"): string {
  const detail = (error as { detail?: unknown } | undefined)?.detail
  if (typeof detail === "string") return detail
  if (Array.isArray(detail)) {
    const first = detail[0] as { msg?: string; loc?: unknown[] } | undefined
    if (first?.msg) {
      const field = first.loc?.at(-1)
      return field ? `${String(field)}: ${first.msg}` : first.msg
    }
  }
  if (error instanceof Error) return error.message
  return fallback
}
