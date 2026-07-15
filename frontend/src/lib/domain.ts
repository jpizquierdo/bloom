import type { BeanRead } from "@/client/types.gen"

export const PROCESSES = [
  "washed",
  "natural",
  "honey",
  "anaerobic",
  "carbonic_maceration",
  "other",
] as const

export const ROAST_LEVELS = ["light", "medium_light", "medium", "medium_dark", "dark"] as const

export const BREW_CATEGORIES = ["espresso", "filter", "immersion"] as const

export const EQUIPMENT_TYPES = ["grinder", "espresso_machine", "kettle", "other"] as const

export const TASTING_SCORES = [
  "aroma",
  "acidity",
  "sweetness",
  "body",
  "bitterness",
  "aftertaste",
  "overall",
] as const

export type TastingScore = (typeof TASTING_SCORES)[number]

export function beanLabel(bean: BeanRead): string {
  return `${bean.name} — ${bean.roaster.name}`
}

/**
 * The API returns a band per metric ("below" / "within" / "above") against the control-chart
 * targets in docs/ARCHITECTURE.md; we only choose how to paint it.
 */
export type Band = "below" | "within" | "above"

export const BAND_VARIANT: Record<Band, "default" | "secondary" | "destructive" | "outline"> = {
  within: "default",
  below: "secondary",
  above: "destructive",
}

export const BAND_LABEL: Record<Band, string> = {
  below: "Under",
  within: "On target",
  above: "Over",
}
