import type { BrewRead } from "@/client/types.gen"
import { Badge } from "@/components/ui/badge"
import { BAND_LABEL, BAND_VARIANT, type Band } from "@/lib/domain"

/** The API classifies TDS and extraction yield into bands; we only paint what it says. */
export function BandBadge({
  band,
  label,
}: {
  band: string | null | undefined
  label: string
}) {
  if (!band) return null
  const key = band as Band
  return (
    <Badge variant={BAND_VARIANT[key] ?? "outline"} className="gap-1">
      <span className="opacity-70">{label}</span>
      {BAND_LABEL[key] ?? band}
    </Badge>
  )
}

export function BrewDiagnostics({ brew }: { brew: BrewRead }) {
  const { strength, extraction } = brew.diagnostics ?? {}
  if (!strength && !extraction) return <span className="text-muted-foreground">—</span>

  return (
    <div className="flex flex-wrap gap-1">
      <BandBadge band={strength} label="TDS" />
      <BandBadge band={extraction} label="EY" />
    </div>
  )
}
