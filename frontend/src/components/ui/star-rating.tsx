import { Star } from "lucide-react"
import * as React from "react"

import { cn } from "@/lib/utils"

interface StarRatingProps {
  value: number
  onChange?: (value: number) => void
  readOnly?: boolean
  /** Star edge length in pixels. */
  size?: number
  className?: string
  "aria-label"?: string
}

const STARS = [1, 2, 3, 4, 5] as const

/**
 * Google-review-style 0–5 rating. Read-only mode paints `value` filled stars; interactive
 * mode previews on hover and sets on click, and clicking the currently selected star clears
 * back to 0 (unrated).
 */
export function StarRating({
  value,
  onChange,
  readOnly = false,
  size = 20,
  className,
  "aria-label": ariaLabel,
}: StarRatingProps) {
  const [hover, setHover] = React.useState<number | null>(null)
  const shown = hover ?? value

  return (
    <div
      className={cn("inline-flex items-center gap-0.5", className)}
      role={readOnly ? "img" : "radiogroup"}
      aria-label={ariaLabel ?? `${value} of 5 stars`}
      onMouseLeave={() => setHover(null)}
    >
      {STARS.map((star) => {
        const filled = star <= shown
        const icon = (
          <Star
            className={cn(filled ? "fill-primary text-primary" : "fill-transparent text-muted-foreground")}
            style={{ width: size, height: size }}
          />
        )
        if (readOnly) return <span key={star}>{icon}</span>
        return (
          <button
            key={star}
            type="button"
            className="cursor-pointer rounded-sm transition-transform hover:scale-110 focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-hidden"
            aria-label={`${star} star${star > 1 ? "s" : ""}`}
            aria-pressed={star <= value}
            onMouseEnter={() => setHover(star)}
            onClick={() => onChange?.(star === value ? 0 : star)}
          >
            {icon}
          </button>
        )
      })}
    </div>
  )
}
