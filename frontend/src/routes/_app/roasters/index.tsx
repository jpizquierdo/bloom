import {
  roastersCreateRoasterMutation,
  roastersDeleteRoasterMutation,
  roastersListRoastersOptions,
  roastersUpdateRoasterMutation,
} from "@/client/@tanstack/react-query.gen"
import type { RoasterRead } from "@/client/types.gen"
import { DataTable } from "@/components/data/data-table"
import { DeleteAlert } from "@/components/data/delete-alert"
import { PageHeader } from "@/components/data/page-header"
import { ResourceDialog } from "@/components/data/resource-dialog"
import { RowActions } from "@/components/data/row-actions"
import { Button } from "@/components/ui/button"
import {
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { isAdmin, useCurrentUser } from "@/lib/auth"
import { stripEmpty } from "@/lib/format"
import { submitAndClose, useCrudFeedback } from "@/lib/mutations"
import { zodResolver } from "@hookform/resolvers/zod"
import { useMutation, useQuery } from "@tanstack/react-query"
import { createFileRoute, useNavigate } from "@tanstack/react-router"
import type { ColumnDef } from "@tanstack/react-table"
import { Plus } from "lucide-react"
import { useState } from "react"
import { useForm } from "react-hook-form"
import { z } from "zod"

export const Route = createFileRoute("/_app/roasters/")({ component: RoastersPage })

const schema = z.object({
  name: z.string().min(1, "Name is required"),
  country: z.string(),
  city: z.string(),
  website: z.union([z.literal(""), z.url("Enter a valid URL")]),
  notes: z.string(),
})

type FormValues = z.infer<typeof schema>

const EMPTY: FormValues = { name: "", country: "", city: "", website: "", notes: "" }

function RoastersPage() {
  const { user } = useCurrentUser()
  const navigate = useNavigate()
  const feedback = useCrudFeedback()
  const { data, isLoading } = useQuery(roastersListRoastersOptions())

  const [editing, setEditing] = useState<RoasterRead | null>(null)
  const [dialogOpen, setDialogOpen] = useState(false)
  const [deleting, setDeleting] = useState<RoasterRead | null>(null)

  const form = useForm<FormValues>({ resolver: zodResolver(schema), defaultValues: EMPTY })

  const create = useMutation({
    ...roastersCreateRoasterMutation(),
    onSuccess: feedback.onSuccess("Roaster created"),
    onError: feedback.onError,
  })
  const update = useMutation({
    ...roastersUpdateRoasterMutation(),
    onSuccess: feedback.onSuccess("Roaster updated"),
    onError: feedback.onError,
  })
  const remove = useMutation({
    ...roastersDeleteRoasterMutation(),
    onSuccess: feedback.onSuccess("Roaster deleted"),
    onError: feedback.onError,
  })

  function openCreate() {
    setEditing(null)
    form.reset(EMPTY)
    setDialogOpen(true)
  }

  function openEdit(roaster: RoasterRead) {
    setEditing(roaster)
    form.reset({
      name: roaster.name,
      country: roaster.country ?? "",
      city: roaster.city ?? "",
      website: roaster.website ?? "",
      notes: roaster.notes ?? "",
    })
    setDialogOpen(true)
  }

  function onSubmit(values: FormValues) {
    const body = stripEmpty(values)
    const request = editing
      ? update.mutateAsync({ path: { roaster_id: editing.id }, body })
      : create.mutateAsync({ body: { ...body, name: values.name } })
    return submitAndClose(request, () => setDialogOpen(false))
  }

  const columns: ColumnDef<RoasterRead, unknown>[] = [
    { accessorKey: "name", header: "Name" },
    {
      accessorKey: "country",
      header: "Country",
      cell: ({ row }) => row.original.country ?? "—",
    },
    { accessorKey: "city", header: "City", cell: ({ row }) => row.original.city ?? "—" },
    {
      accessorKey: "website",
      header: "Website",
      enableSorting: false,
      cell: ({ row }) =>
        row.original.website ? (
          <a
            href={row.original.website}
            target="_blank"
            rel="noreferrer"
            className="text-primary underline-offset-4 hover:underline"
          >
            {row.original.website.replace(/^https?:\/\//, "")}
          </a>
        ) : (
          "—"
        ),
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
        title="Roasters"
        description="Everyone can add a roaster; only admins can rename or remove one."
        actions={
          <Button onClick={openCreate}>
            <Plus className="size-4" />
            New roaster
          </Button>
        }
      />

      <DataTable
        columns={columns}
        data={data}
        isLoading={isLoading}
        searchPlaceholder="Search roasters…"
        emptyMessage="No roasters yet. Add one, or just name it when you create a bean."
        onRowClick={(roaster) =>
          navigate({ to: "/roasters/$roasterId", params: { roasterId: String(roaster.id) } })
        }
      />

      <ResourceDialog
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        title={editing ? "Edit roaster" : "New roaster"}
        description={
          editing
            ? "Renaming a roaster updates every bean that references it."
            : "Beans can also create a roaster on the fly, just by naming it."
        }
        form={form}
        onSubmit={onSubmit}
        isPending={create.isPending || update.isPending}
      >
        <FormField
          control={form.control}
          name="name"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Name</FormLabel>
              <FormControl>
                <Input placeholder="Nomad Coffee" {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        <div className="grid gap-4 sm:grid-cols-2">
          <FormField
            control={form.control}
            name="country"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Country</FormLabel>
                <FormControl>
                  <Input placeholder="Spain" {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
          <FormField
            control={form.control}
            name="city"
            render={({ field }) => (
              <FormItem>
                <FormLabel>City</FormLabel>
                <FormControl>
                  <Input placeholder="Barcelona" {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
        </div>
        <FormField
          control={form.control}
          name="website"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Website</FormLabel>
              <FormControl>
                <Input placeholder="https://nomadcoffee.es" {...field} />
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
        description={`Delete "${deleting?.name}"? This only works if no bean references it.`}
        isPending={remove.isPending}
        onConfirm={() => {
          if (deleting) remove.mutate({ path: { roaster_id: deleting.id } })
          setDeleting(null)
        }}
      />
    </>
  )
}
