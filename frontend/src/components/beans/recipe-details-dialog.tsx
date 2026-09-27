import {
  brewMethodsListBrewMethodsOptions,
  equipmentListEquipmentOptions,
} from "@/client/@tanstack/react-query.gen"
import type { RecipeRead } from "@/client/types.gen"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { formatDateTime, formatNumber, formatSeconds } from "@/lib/format"
import { useQuery } from "@tanstack/react-query"
import type { ReactNode } from "react"

interface RecipeDetailsDialogProps {
  recipe: RecipeRead | null
  onOpenChange: (open: boolean) => void
}

export function RecipeDetailsDialog({ recipe, onOpenChange }: RecipeDetailsDialogProps) {
  const { data: methods } = useQuery(brewMethodsListBrewMethodsOptions())
  const { data: equipment } = useQuery(equipmentListEquipmentOptions())
  const method = methods?.find((item) => item.id === recipe?.method_id)
  const grinder = equipment?.find((item) => item.id === recipe?.grinder_id)

  return (
    <Dialog open={recipe !== null} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-xl">
        <DialogHeader>
          <DialogTitle>{recipe?.name ?? "Recipe"}</DialogTitle>
          {recipe ? (
            <DialogDescription>
              Created by {recipe.owner.username} · {formatDateTime(recipe.created_at)}
            </DialogDescription>
          ) : null}
        </DialogHeader>

        {recipe ? (
          <div className="grid gap-5">
            <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
              <Metric label="Method" value={method?.name ?? `#${recipe.method_id}`} />
              <Metric label="Dose" value={`${formatNumber(recipe.dose_grams)} g`} />
              <Metric
                label="Yield"
                value={recipe.yield_grams ? `${formatNumber(recipe.yield_grams)} g` : "—"}
              />
              <Metric
                label="Water"
                value={recipe.water_grams ? `${formatNumber(recipe.water_grams)} g` : "—"}
              />
              <Metric label="Grinder" value={grinder?.name ?? "—"} />
              <Metric label="Grind setting" value={recipe.grind_setting ?? "—"} />
              <Metric
                label="Temperature"
                value={
                  recipe.water_temp_celsius
                    ? `${formatNumber(recipe.water_temp_celsius)} °C`
                    : "—"
                }
              />
              <Metric label="Target time" value={formatSeconds(recipe.brew_time_seconds)} />
            </div>
            {recipe.notes ? (
              <div className="grid gap-1">
                <span className="text-xs text-muted-foreground">Recipe notes</span>
                <p className="whitespace-pre-wrap text-sm">{recipe.notes}</p>
              </div>
            ) : null}
          </div>
        ) : null}
      </DialogContent>
    </Dialog>
  )
}

function Metric({ label, value }: { label: string; value: ReactNode }) {
  return (
    <div className="grid gap-1">
      <span className="text-xs text-muted-foreground">{label}</span>
      <span className="font-medium tabular-nums">{value}</span>
    </div>
  )
}
