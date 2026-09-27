import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { Copy, MoreHorizontal, Pencil, Trash2 } from "lucide-react"
import type { ReactNode } from "react"

interface AdditionalRowAction {
  label: string
  icon?: ReactNode
  onSelect: () => void
}

interface RowActionsProps {
  onEdit: () => void
  onDelete: () => void
  /** Edit and delete are hidden for rows the current user does not own. */
  canEdit: boolean
  deleteLabel?: string
  /** Optional duplicate action, rendered between Edit and Delete when provided. */
  onDuplicate?: () => void
  duplicateLabel?: string
  additionalActions?: AdditionalRowAction[]
}

export function RowActions({
  onEdit,
  onDelete,
  canEdit,
  deleteLabel = "Delete",
  onDuplicate,
  duplicateLabel = "Duplicate",
  additionalActions = [],
}: RowActionsProps) {
  if (!canEdit && additionalActions.length === 0) return null

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
        {canEdit ? (
          <DropdownMenuItem onSelect={onEdit}>
            <Pencil className="size-4" />
            Edit
          </DropdownMenuItem>
        ) : null}
        {canEdit && onDuplicate ? (
          <DropdownMenuItem onSelect={onDuplicate}>
            <Copy className="size-4" />
            {duplicateLabel}
          </DropdownMenuItem>
        ) : null}
        {additionalActions.map((action) => (
          <DropdownMenuItem key={action.label} onSelect={action.onSelect}>
            {action.icon}
            {action.label}
          </DropdownMenuItem>
        ))}
        {canEdit ? (
          <DropdownMenuItem variant="destructive" onSelect={onDelete}>
            <Trash2 className="size-4" />
            {deleteLabel}
          </DropdownMenuItem>
        ) : null}
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
