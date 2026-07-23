import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { Copy, MoreHorizontal, Pencil, Trash2 } from "lucide-react"

interface RowActionsProps {
  onEdit: () => void
  onDelete: () => void
  /** Rows you don't own are read-only (shared log): the menu is hidden entirely. */
  canEdit: boolean
  deleteLabel?: string
  /** Optional duplicate action, rendered between Edit and Delete when provided. */
  onDuplicate?: () => void
  duplicateLabel?: string
}

export function RowActions({
  onEdit,
  onDelete,
  canEdit,
  deleteLabel = "Delete",
  onDuplicate,
  duplicateLabel = "Duplicate",
}: RowActionsProps) {
  if (!canEdit) return null

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant="ghost"
          size="icon"
          className="size-8"
          aria-label="Row actions"
          onClick={(event) => event.stopPropagation()}
        >
          <MoreHorizontal className="size-4" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" onClick={(event) => event.stopPropagation()}>
        <DropdownMenuItem onSelect={onEdit}>
          <Pencil className="size-4" />
          Edit
        </DropdownMenuItem>
        {onDuplicate ? (
          <DropdownMenuItem onSelect={onDuplicate}>
            <Copy className="size-4" />
            {duplicateLabel}
          </DropdownMenuItem>
        ) : null}
        <DropdownMenuItem variant="destructive" onSelect={onDelete}>
          <Trash2 className="size-4" />
          {deleteLabel}
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
