import { beansUpdateBeanMutation } from "@/client/@tanstack/react-query.gen"
import type { BeanRead } from "@/client/types.gen"
import { StarRating } from "@/components/ui/star-rating"
import { canEdit, useCurrentUser } from "@/lib/auth"
import { useCrudFeedback } from "@/lib/mutations"
import { useMutation } from "@tanstack/react-query"

/** Bean rating that the creator (or an admin) can set in one click; read-only for others. */
export function QuickBeanRating({ bean, size = 16 }: { bean: BeanRead; size?: number }) {
  const { user } = useCurrentUser()
  const feedback = useCrudFeedback()
  const update = useMutation({
    ...beansUpdateBeanMutation(),
    onSuccess: feedback.onSuccess("Rating updated"),
    onError: feedback.onError,
  })
  const editable = canEdit(bean, user)
  const value = bean.rating ?? 0

  if (!editable) return value > 0 ? <StarRating value={value} readOnly size={size} /> : null

  return (
    <StarRating
      value={value}
      size={size}
      disabled={update.isPending}
      aria-label="Bean rating"
      onChange={(stars) =>
        update.mutate({ path: { bean_id: bean.id }, body: { rating: stars || null } })
      }
    />
  )
}
