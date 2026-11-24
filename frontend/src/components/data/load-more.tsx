import { Button } from "@/components/ui/button"
import { Loader2 } from "lucide-react"

interface LoadMoreProps {
  shown: number
  total: number
  hasNextPage: boolean
  isFetchingNextPage: boolean
  onLoadMore: () => void
}

/** "Showing N of M" under a paged list, with a button to fetch the next page. */
export function LoadMore({ shown, total, hasNextPage, isFetchingNextPage, onLoadMore }: LoadMoreProps) {
  if (total === 0) return null
  return (
    <div className="mt-6 flex flex-col items-center gap-2">
      <p className="text-xs text-muted-foreground" aria-live="polite">
        Showing {shown} of {total}
      </p>
      {hasNextPage ? (
        <Button variant="outline" onClick={onLoadMore} disabled={isFetchingNextPage}>
          {isFetchingNextPage ? <Loader2 className="size-4 animate-spin" /> : null}
          Load more
        </Button>
      ) : null}
    </div>
  )
}
