import {
  equipmentCreateEquipmentMutation,
  equipmentDeleteEquipmentMutation,
  equipmentListEquipmentOptions,
  equipmentUpdateEquipmentMutation,
} from "@/client/@tanstack/react-query.gen"
import type { EquipmentRead } from "@/client/types.gen"
import { DataTable } from "@/components/data/data-table"
import { DeleteAlert } from "@/components/data/delete-alert"
import { PageHeader } from "@/components/data/page-header"
import { ResourceDialog } from "@/components/data/resource-dialog"
import { RowActions } from "@/components/data/row-actions"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form"
import { Input } from "@/components/ui/input"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Textarea } from "@/components/ui/textarea"
import { isAdmin, useCurrentUser } from "@/lib/auth"
import { EQUIPMENT_TYPES } from "@/lib/domain"
import { humanize, patchBody, stripEmpty } from "@/lib/format"
import { submitAndClose, useCrudFeedback } from "@/lib/mutations"
import { zodResolver } from "@hookform/resolvers/zod"
import { useMutation, useQuery } from "@tanstack/react-query"
import { createFileRoute } from "@tanstack/react-router"
import type { ColumnDef } from "@tanstack/react-table"
import { Plus } from "lucide-react"
import { useState } from "react"
import { useForm } from "react-hook-form"
import { z } from "zod"

export const Route = createFileRoute("/_app/equipment")({ component: EquipmentPage })

const schema = z.object({
  type: z.enum(EQUIPMENT_TYPES, "Pick a type"),
  name: z.string().min(1, "Name is required"),
  brand: z.string(),
  notes: z.string(),
})

type FormValues = z.infer<typeof schema>

const EMPTY: FormValues = { type: "grinder", name: "", brand: "", notes: "" }

function EquipmentPage() {
  const { user } = useCurrentUser()
  const feedback = useCrudFeedback()
  const { data, isLoading } = useQuery(equipmentListEquipmentOptions())

  const [editing, setEditing] = useState<EquipmentRead | null>(null)
  const [dialogOpen, setDialogOpen] = useState(false)
  const [deleting, setDeleting] = useState<EquipmentRead | null>(null)

  const form = useForm<FormValues>({ resolver: zodResolver(schema), defaultValues: EMPTY })

  const create = useMutation({
    ...equipmentCreateEquipmentMutation(),
    onSuccess: feedback.onSuccess("Equipment created"),
    onError: feedback.onError,
  })
  const update = useMutation({
    ...equipmentUpdateEquipmentMutation(),
    onSuccess: feedback.onSuccess("Equipment updated"),
    onError: feedback.onError,
  })
  const remove = useMutation({
    ...equipmentDeleteEquipmentMutation(),
    onSuccess: feedback.onSuccess("Equipment deleted"),
    onError: feedback.onError,
  })

  function openCreate() {
    setEditing(null)
    form.reset(EMPTY)
    setDialogOpen(true)
  }

  function openEdit(equipment: EquipmentRead) {
    setEditing(equipment)
    form.reset({
      type: equipment.type as FormValues["type"],
      name: equipment.name,
      brand: equipment.brand ?? "",
      notes: equipment.notes ?? "",
    })
    setDialogOpen(true)
  }

  function onSubmit(values: FormValues) {
    const request = editing
      ? update.mutateAsync({
          path: { equipment_id: editing.id },
          // Clearing brand/notes sends null (blanks it); type/name stay required.
          body: patchBody(values, ["brand", "notes"]),
        })
      : create.mutateAsync({
          body: { type: values.type, name: values.name, ...stripEmpty({ brand: values.brand, notes: values.notes }) },
        })
    return submitAndClose(request, () => setDialogOpen(false))
  }

  const columns: ColumnDef<EquipmentRead, unknown>[] = [
    { accessorKey: "name", header: "Name" },
    {
      accessorKey: "type",
      header: "Type",
      cell: ({ row }) => <Badge variant="secondary">{humanize(row.original.type)}</Badge>,
    },
    { accessorKey: "brand", header: "Brand", cell: ({ row }) => row.original.brand ?? "—" },
    {
      accessorKey: "notes",
      header: "Notes",
      enableSorting: false,
      cell: ({ row }) => row.original.notes ?? "—",
    },
    {
      id: "actions",
      header: "",
      enableSorting: false,
      cell: ({ row }) => (
        <div className="text-right">
          <RowActions
            canEdit={isAdmin(user)}
            onEdit={() => openEdit(row.original)}
            onDelete={() => setDeleting(row.original)}
          />
        </div>
      ),
    },
  ]

  return (
    <>
      <PageHeader
        title="Equipment"
        description="Grinders, machines and kettles. Brews reference a grinder."
        actions={
          isAdmin(user) ? (
            <Button onClick={openCreate}>
              <Plus className="size-4" />
              New equipment
            </Button>
          ) : null
        }
      />

      <DataTable
        columns={columns}
        data={data}
        isLoading={isLoading}
        searchPlaceholder="Search equipment…"
        emptyMessage="No equipment yet. An admin can add your grinder."
      />

      <ResourceDialog
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        title={editing ? "Edit equipment" : "New equipment"}
        form={form}
        onSubmit={onSubmit}
        isPending={create.isPending || update.isPending}
      >
        <FormField
          control={form.control}
          name="type"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Type</FormLabel>
              <Select value={field.value} onValueChange={field.onChange}>
                <FormControl>
                  <SelectTrigger className="w-full">
                    <SelectValue />
                  </SelectTrigger>
                </FormControl>
                <SelectContent>
                  {EQUIPMENT_TYPES.map((type) => (
                    <SelectItem key={type} value={type}>
                      {humanize(type)}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <FormMessage />
            </FormItem>
          )}
        />
        <FormField
          control={form.control}
          name="name"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Name</FormLabel>
              <FormControl>
                <Input placeholder="Niche Zero" {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        <FormField
          control={form.control}
          name="brand"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Brand</FormLabel>
              <FormControl>
                <Input placeholder="Niche" {...field} />
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
                <Textarea rows={3} {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
      </ResourceDialog>

      <DeleteAlert
        open={deleting !== null}
        onOpenChange={(open) => !open && setDeleting(null)}
        description={`Delete "${deleting?.name}"? Brews that used it keep their data, just unlinked from the grinder.`}
        isPending={remove.isPending}
        onConfirm={() => {
          if (deleting) remove.mutate({ path: { equipment_id: deleting.id } })
          setDeleting(null)
        }}
      />
    </>
  )
}
