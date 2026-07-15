import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Form } from "@/components/ui/form"
import { cn } from "@/lib/utils"
import { Loader2 } from "lucide-react"
import type { ReactNode } from "react"
import type { FieldValues, UseFormReturn } from "react-hook-form"

interface ResourceDialogProps<T extends FieldValues> {
  open: boolean
  onOpenChange: (open: boolean) => void
  title: string
  description?: string
  form: UseFormReturn<T>
  onSubmit: (values: T) => void
  isPending?: boolean
  submitLabel?: string
  /** Two columns for the wider forms (brews, beans). */
  wide?: boolean
  children: ReactNode
}

export function ResourceDialog<T extends FieldValues>({
  open,
  onOpenChange,
  title,
  description,
  form,
  onSubmit,
  isPending,
  submitLabel = "Save",
  wide,
  children,
}: ResourceDialogProps<T>) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className={cn("max-h-[90svh] overflow-y-auto", wide && "sm:max-w-2xl")}>
        <DialogHeader>
          <DialogTitle>{title}</DialogTitle>
          {description ? <DialogDescription>{description}</DialogDescription> : null}
        </DialogHeader>

        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="grid gap-4">
            <div className={cn("grid gap-4", wide && "sm:grid-cols-2")}>{children}</div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
                Cancel
              </Button>
              <Button type="submit" disabled={isPending}>
                {isPending ? <Loader2 className="animate-spin" /> : null}
                {submitLabel}
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  )
}
