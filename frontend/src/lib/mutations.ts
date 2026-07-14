import { errorMessage } from "@/lib/api"
import { useQueryClient } from "@tanstack/react-query"
import { toast } from "sonner"

/**
 * Shared mutation callbacks. Deletes cascade server-side (a bean takes its brews and
 * tastings with it) and rows are cross-referenced, so a blanket invalidation is both the
 * simplest and the most correct refresh — the lists are small and unpaginated.
 */
export function useCrudFeedback() {
  const queryClient = useQueryClient()

  return {
    onSuccess: (message: string) => () => {
      toast.success(message)
      queryClient.invalidateQueries()
    },
    onError: (error: unknown) => {
      toast.error(errorMessage(error))
    },
  }
}

/**
 * `mutateAsync` rejects when the API refuses (a 409 on a duplicate name, a 422 on a bad
 * field). `onError` has already raised the toast, so swallow the rejection — otherwise it
 * escapes the form's submit handler as an unhandled rejection — and leave the dialog open
 * on the values the user still needs to fix.
 */
export async function submitAndClose(request: Promise<unknown>, close: () => void) {
  try {
    await request
    close()
  } catch {
    // Already surfaced by onError.
  }
}
