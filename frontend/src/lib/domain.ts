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

export const ROAST_TYPES = ["filter", "espresso", "omni", "unknown"] as const

export const BLENDS = ["single_origin", "blend", "unknown"] as const

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

function foldName(value: string): string {
  return value.trim().replace(/\s+/g, " ").toLowerCase()
}

/**
 * A bean is a duplicate of another when the same roaster already has that name. This only
 * warns before submitting: the API runs the same check (case-folded in the database) and
 * is what actually refuses, with 409.
 */
export function findDuplicateBean(
  beans: BeanRead[],
  { name, roaster, excludeId }: { name: string; roaster: string; excludeId?: number },
): BeanRead | undefined {
  const wantedName = foldName(name)
  const wantedRoaster = foldName(roaster)
  if (!wantedName || !wantedRoaster) return undefined
  return beans.find(
    (bean) =>
      bean.id !== excludeId &&
      foldName(bean.name) === wantedName &&
      foldName(bean.roaster.name) === wantedRoaster,
  )
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
