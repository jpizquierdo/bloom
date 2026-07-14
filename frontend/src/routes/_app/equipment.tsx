import {
  equipmentCreateEquipmentMutation,
  equipmentListEquipmentOptions,
} from "@/client/@tanstack/react-query.gen"
import type { EquipmentRead } from "@/client/types.gen"
import { DataTable } from "@/components/data/data-table"
import { PageHeader } from "@/components/data/page-header"
import { ResourceDialog } from "@/components/data/resource-dialog"
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
import { humanize, stripEmpty } from "@/lib/format"
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

function EquipmentPage() {
  const { user } = useCurrentUser()
  const feedback = useCrudFeedback()
  const { data, isLoading } = useQuery(equipmentListEquipmentOptions())
  const [dialogOpen, setDialogOpen] = useState(false)

  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { type: "grinder", name: "", brand: "", notes: "" },
  })

  const create = useMutation({
    ...equipmentCreateEquipmentMutation(),
    onSuccess: feedback.onSuccess("Equipment created"),
    onError: feedback.onError,
  })

  function onSubmit(values: FormValues) {
    const request = create.mutateAsync({
      body: {
        type: values.type,
        name: values.name,
        ...stripEmpty({ brand: values.brand, notes: values.notes }),
      },
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
  ]

  return (
    <>
      <PageHeader
        title="Equipment"
        description="Grinders, machines and kettles. Brews reference a grinder."
        actions={
          isAdmin(user) ? (
            <Button
              onClick={() => {
                form.reset({ type: "grinder", name: "", brand: "", notes: "" })
                setDialogOpen(true)
              }}
            >
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
        title="New equipment"
        form={form}
        onSubmit={onSubmit}
        isPending={create.isPending}
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
    </>
  )
}
