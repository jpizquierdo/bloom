import { cn } from "@/lib/utils"
import { Coffee } from "lucide-react"

export function Brand({ className }: { className?: string }) {
  return (
    <div className={cn("flex items-center gap-2", className)}>
      <span className="flex size-8 items-center justify-center rounded-lg bg-primary text-primary-foreground">
        <Coffee className="size-4.5" />
      </span>
      <span className="text-lg font-semibold tracking-tight">Bloom</span>
    </div>
  )
}
