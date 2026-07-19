import {
  tastingsCreateTastingMutation,
  tastingsUpdateTastingMutation,
} from "@/client/@tanstack/react-query.gen"
import type { TastingRead } from "@/client/types.gen"
import { ResourceDialog } from "@/components/data/resource-dialog"
import { TagInput } from "@/components/data/tag-input"
import {
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form"
import { Input } from "@/components/ui/input"
import { StarRating } from "@/components/ui/star-rating"
import { Textarea } from "@/components/ui/textarea"
import { TASTING_SCORES } from "@/lib/domain"
import { humanize, stripEmpty, toDateTimeLocal } from "@/lib/format"
import { submitAndClose, useCrudFeedback } from "@/lib/mutations"
import { useMutation } from "@tanstack/react-query"
import { useEffect } from "react"
import { useForm } from "react-hook-form"

/** Scores are 1–5 stars or absent; 0 means "not scored" and is dropped on submit. */
type FormValues = {
  aroma: number
  acidity: number
  sweetness: number
  body: number
  bitterness: number
  aftertaste: number
  overall: number
  descriptors: string[]
  notes: string
  tasted_at: string
}

const EMPTY: FormValues = {
  aroma: 0,
  acidity: 0,
  sweetness: 0,
  body: 0,
  bitterness: 0,
  aftertaste: 0,
  overall: 0,
  descriptors: [],
  notes: "",
  tasted_at: "",
}

interface TastingDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  brewId: number
  tasting: TastingRead | null
}

export function TastingDialog({ open, onOpenChange, brewId, tasting }: TastingDialogProps) {
  const feedback = useCrudFeedback()
  const form = useForm<FormValues>({ defaultValues: EMPTY })

  useEffect(() => {
    if (!open) return
    form.reset(
      tasting
        ? {
            aroma: tasting.aroma ?? 0,
            acidity: tasting.acidity ?? 0,
            sweetness: tasting.sweetness ?? 0,
            body: tasting.body ?? 0,
            bitterness: tasting.bitterness ?? 0,
            aftertaste: tasting.aftertaste ?? 0,
            overall: tasting.overall ?? 0,
            descriptors: tasting.descriptors ?? [],
            notes: tasting.notes ?? "",
            tasted_at: toDateTimeLocal(tasting.tasted_at),
          }
        : EMPTY,
    )
  }, [open, tasting, form])

  const create = useMutation({
    ...tastingsCreateTastingMutation(),
    onSuccess: feedback.onSuccess("Tasting added"),
    onError: feedback.onError,
  })
  const update = useMutation({
    ...tastingsUpdateTastingMutation(),
    onSuccess: feedback.onSuccess("Tasting updated"),
    onError: feedback.onError,
  })

  function onSubmit(values: FormValues) {
    // 0 stars = unrated: send an explicit null (not omit), and keep the scores out of
    // stripEmpty (which would drop null), so clearing a score on PATCH actually clears it.
    const scores = Object.fromEntries(
      TASTING_SCORES.map((score) => [score, values[score] === 0 ? null : values[score]]),
    )
    const body = {
      ...stripEmpty({
        notes: values.notes,
        tasted_at:
          values.tasted_at === "" ? undefined : new Date(values.tasted_at).toISOString(),
      }),
      ...scores,
      descriptors: values.descriptors,
    }

    const request = tasting
      ? update.mutateAsync({ path: { tasting_id: tasting.id }, body })
      : create.mutateAsync({ path: { brew_id: brewId }, body })
    return submitAndClose(request, () => onOpenChange(false))
  }

  return (
    <ResourceDialog
      open={open}
      onOpenChange={onOpenChange}
      title={tasting ? "Edit tasting" : "Add a tasting"}
      description="Score what you noticed; leave a rating empty to skip it."
      form={form}
      onSubmit={onSubmit}
      isPending={create.isPending || update.isPending}
    >
      <div className="grid gap-5">
        {TASTING_SCORES.map((score) => (
          <FormField
            key={score}
            control={form.control}
            name={score}
            render={({ field }) => (
              <FormItem>
                <div className="flex items-center justify-between">
                  <FormLabel>{humanize(score)}</FormLabel>
                  <FormControl>
                    <StarRating
                      value={field.value}
                      onChange={field.onChange}
                      aria-label={humanize(score)}
                    />
                  </FormControl>
                </div>
              </FormItem>
            )}
          />
        ))}
      </div>

      <FormField
        control={form.control}
        name="descriptors"
        render={({ field }) => (
          <FormItem>
            <FormLabel>Descriptors</FormLabel>
            <FormControl>
              <TagInput
                value={field.value}
                onChange={field.onChange}
                placeholder="blackcurrant, then Enter"
              />
            </FormControl>
            <FormDescription>Press Enter or comma to add each one.</FormDescription>
            <FormMessage />
          </FormItem>
        )}
      />
      <FormField
        control={form.control}
        name="tasted_at"
        render={({ field }) => (
          <FormItem>
            <FormLabel>Tasted at</FormLabel>
            <FormControl>
              <Input type="datetime-local" {...field} />
            </FormControl>
            <FormMessage />
          </FormItem>
        )}
      />
      <FormField
        control={form.control}
        name="notes"
        render={({ field }) => (
          <FormItem>
            <FormLabel>Notes</FormLabel>
            <FormControl>
              <Textarea rows={3} placeholder="Juicy, a little thin at the end." {...field} />
            </FormControl>
            <FormMessage />
          </FormItem>
        )}
      />
    </ResourceDialog>
  )
}
