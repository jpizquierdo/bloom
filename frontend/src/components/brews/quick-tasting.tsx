import {
  tastingsCreateTastingMutation,
  tastingsUpdateTastingMutation,
} from "@/client/@tanstack/react-query.gen"
import type { TastingRead } from "@/client/types.gen"
import { StarRating } from "@/components/ui/star-rating"
import { useCrudFeedback } from "@/lib/mutations"
import { useMutation, useQueryClient } from "@tanstack/react-query"

interface QuickTastingProps {
  brewId: number
  /** The current user's tasting of this brew, if any. */
  tasting: TastingRead | undefined
  size?: number
}

/** One-click overall rating: creates a stars-only tasting, or updates the existing one. */
export function QuickTasting({ brewId, tasting, size = 16 }: QuickTastingProps) {
  const feedback = useCrudFeedback()
  const queryClient = useQueryClient()
  // A stale list could make a create collide with an existing tasting (409): refetch on error.
  const onError = (error: unknown) => {
    feedback.onError(error)
    queryClient.invalidateQueries()
  }
  const create = useMutation({
    ...tastingsCreateTastingMutation(),
    onSuccess: feedback.onSuccess("Tasting added"),
    onError,
  })
  const update = useMutation({
    ...tastingsUpdateTastingMutation(),
    onSuccess: feedback.onSuccess("Rating updated"),
    onError,
  })

  function rate(stars: number) {
    if (tasting) {
      update.mutate({ path: { tasting_id: tasting.id }, body: { overall: stars || null } })
    } else if (stars > 0) {
      create.mutate({ path: { brew_id: brewId }, body: { overall: stars } })
    }
  }

  return (
    <StarRating
      value={tasting?.overall ?? 0}
      onChange={rate}
      size={size}
      disabled={create.isPending || update.isPending}
      aria-label="Overall rating"
    />
  )
}
