import {
  recipesCreateRecipeMutation,
  recipesUpdateRecipeMutation,
} from "@/client/@tanstack/react-query.gen"
import type { BrewRead, RecipeRead } from "@/client/types.gen"
import { PreparationFields } from "@/components/brews/preparation-fields"
import { ResourceDialog } from "@/components/data/resource-dialog"
import {
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import {
  MAX_BREWING_NOTES_LENGTH,
  MAX_RECIPE_NAME_LENGTH,
  brewingNotesSchema,
  preparationFieldSchema,
  recipeNameSchema,
} from "@/lib/brewing-validation"
import { patchBody, stripEmpty } from "@/lib/format"
import { submitAndClose, useCrudFeedback } from "@/lib/mutations"
import { zodResolver } from "@hookform/resolvers/zod"
import { useMutation } from "@tanstack/react-query"
import { useEffect } from "react"
import { useForm } from "react-hook-form"
import { z } from "zod"

const schema = z.object({
  name: recipeNameSchema,
  ...preparationFieldSchema,
  notes: brewingNotesSchema,
})

type FormValues = z.infer<typeof schema>

const CLEARABLE = [
  "grinder_id",
  "yield_grams",
  "water_grams",
  "grind_setting",
  "water_temp_celsius",
  "brew_time_seconds",
  "notes",
] as const

const EMPTY: FormValues = {
  name: "",
  method_id: "",
  grinder_id: "",
  dose_grams: "",
  yield_grams: "",
  water_grams: "",
  grind_setting: "",
  water_temp_celsius: "",
  brew_time_seconds: "",
  notes: "",
}

interface RecipeDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  beanId: number
  suggestedName: string
  recipe: RecipeRead | null
  /** Seed a new recipe from reusable brew parameters. Brew notes stay on the brew. */
  prefillFrom?: BrewRead
}

export function RecipeDialog({
  open,
  onOpenChange,
  beanId,
  suggestedName,
  recipe,
  prefillFrom,
}: RecipeDialogProps) {
  const feedback = useCrudFeedback()
  const form = useForm<FormValues>({ resolver: zodResolver(schema), defaultValues: EMPTY })

  useEffect(() => {
    if (!open) return
    const source = recipe ?? prefillFrom
    form.reset(
      source
        ? {
            name: recipe?.name ?? suggestedName,
            method_id: String(source.method_id),
            grinder_id: source.grinder_id ? String(source.grinder_id) : "",
            dose_grams: source.dose_grams,
            yield_grams: source.yield_grams ?? "",
            water_grams: source.water_grams ?? "",
            grind_setting: source.grind_setting ?? "",
            water_temp_celsius: source.water_temp_celsius ?? "",
            brew_time_seconds: source.brew_time_seconds?.toString() ?? "",
            notes: recipe?.notes ?? "",
          }
        : { ...EMPTY, name: suggestedName },
    )
  }, [open, recipe, prefillFrom, suggestedName, form])

  const create = useMutation({
    ...recipesCreateRecipeMutation(),
    onSuccess: feedback.onSuccess("Recipe created"),
    onError: feedback.onError,
  })
  const update = useMutation({
    ...recipesUpdateRecipeMutation(),
    onSuccess: feedback.onSuccess("Recipe updated"),
    onError: feedback.onError,
  })

  function onSubmit(values: FormValues) {
    const parameters = {
      grinder_id: values.grinder_id === "" ? undefined : Number(values.grinder_id),
      yield_grams: values.yield_grams === "" ? undefined : Number(values.yield_grams),
      water_grams: values.water_grams === "" ? undefined : Number(values.water_grams),
      grind_setting: values.grind_setting,
      water_temp_celsius:
        values.water_temp_celsius === "" ? undefined : Number(values.water_temp_celsius),
      brew_time_seconds:
        values.brew_time_seconds === "" ? undefined : Number(values.brew_time_seconds),
      notes: values.notes,
    }
    const required = {
      name: values.name.trim(),
      method_id: Number(values.method_id),
      dose_grams: Number(values.dose_grams),
    }
    const request = recipe
      ? update.mutateAsync({
          path: { recipe_id: recipe.id },
          body: { ...patchBody(parameters, CLEARABLE), ...required },
        })
      : create.mutateAsync({
          path: { bean_id: beanId },
          body: { ...stripEmpty(parameters), ...required },
        })
    return submitAndClose(request, () => onOpenChange(false))
  }

  return (
    <ResourceDialog
      open={open}
      onOpenChange={onOpenChange}
      title={recipe ? "Edit recipe" : prefillFrom ? "Save brew as recipe" : "Add recipe"}
      description="Reusable preparation targets. Notes stay with the recipe and are not copied to brews."
      form={form}
      onSubmit={onSubmit}
      isPending={create.isPending || update.isPending}
      submitLabel={recipe ? "Save" : prefillFrom ? "Save recipe" : "Add recipe"}
      wide
    >
      <FormField
        control={form.control}
        name="name"
        render={({ field }) => (
          <FormItem className="sm:col-span-2">
            <FormLabel>Name</FormLabel>
            <FormControl>
              <Input
                maxLength={MAX_RECIPE_NAME_LENGTH}
                placeholder="Brazil: recipe #1"
                {...field}
              />
            </FormControl>
            <FormMessage />
          </FormItem>
        )}
      />
      <PreparationFields />
      <FormField
        control={form.control}
        name="notes"
        render={({ field }) => (
          <FormItem className="sm:col-span-2">
            <FormLabel>Recipe notes</FormLabel>
            <FormControl>
              <Textarea
                rows={3}
                maxLength={MAX_BREWING_NOTES_LENGTH}
                placeholder="Preparation guidance for next time."
                {...field}
              />
            </FormControl>
            <FormMessage />
          </FormItem>
        )}
      />
    </ResourceDialog>
  )
}
