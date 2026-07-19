/**
 * The API rejects an explicit `null` on fields backed by NOT NULL columns
 * (see `bloom/schemas/common.py:reject_null`), and PATCH means "only what is present".
 * So empty form fields must be dropped from the payload, never sent as null or "".
 */
export function stripEmpty<T extends Record<string, unknown>>(values: T): Partial<T> {
  return Object.fromEntries(
    Object.entries(values).filter(([, v]) => v !== undefined && v !== null && v !== ""),
  ) as Partial<T>
}

/**
 * Build a PATCH body. An empty value (undefined / null / "") for a `clearable` field — one
 * backed by a *nullable* column — becomes an explicit `null` so the API clears it. Every
 * other empty value is omitted (PATCH leaves it unchanged), which also avoids sending `null`
 * to a NOT NULL-backed field, since the API rejects that (`reject_null` → 422).
 */
export function patchBody<T extends Record<string, unknown>>(
  values: T,
  clearable: readonly (keyof T)[],
): Partial<{ [K in keyof T]: T[K] | null }> {
  const clear = new Set<keyof T>(clearable)
  const out: Record<string, unknown> = {}
  for (const key of Object.keys(values) as (keyof T)[]) {
    const value = values[key]
    if (value !== undefined && value !== null && value !== "") out[key as string] = value
    else if (clear.has(key)) out[key as string] = null
  }
  return out as Partial<{ [K in keyof T]: T[K] | null }>
}

/** Numeric columns arrive as strings ("18.50"); render them without trailing noise. */
export function formatNumber(value: string | number | null | undefined, digits = 1): string {
  if (value === null || value === undefined || value === "") return "—"
  const n = typeof value === "string" ? Number.parseFloat(value) : value
  return Number.isNaN(n) ? "—" : n.toFixed(digits).replace(/\.0+$/, "")
}

export function formatDate(value: string | null | undefined): string {
  if (!value) return "—"
  const date = new Date(value)
  return Number.isNaN(date.getTime())
    ? "—"
    : date.toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" })
}

export function formatDateTime(value: string | null | undefined): string {
  if (!value) return "—"
  const date = new Date(value)
  return Number.isNaN(date.getTime())
    ? "—"
    : date.toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" })
}

/** Seconds as m:ss — how brew times are read on a timer. */
export function formatSeconds(value: number | null | undefined): string {
  if (value === null || value === undefined) return "—"
  const minutes = Math.floor(value / 60)
  const seconds = value % 60
  return `${minutes}:${seconds.toString().padStart(2, "0")}`
}

/** "washed" → "Washed", "medium_dark" → "Medium dark". */
export function humanize(value: string | null | undefined): string {
  if (!value) return "—"
  const spaced = value.replace(/_/g, " ")
  return spaced.charAt(0).toUpperCase() + spaced.slice(1)
}

/** Datetime-local inputs want "YYYY-MM-DDTHH:mm"; date inputs want "YYYY-MM-DD". */
export function toDateTimeLocal(value: string | null | undefined): string {
  if (!value) return ""
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return ""
  const offset = date.getTimezoneOffset() * 60_000
  return new Date(date.getTime() - offset).toISOString().slice(0, 16)
}

export function toDateInput(value: string | null | undefined): string {
  return value ? value.slice(0, 10) : ""
}
