import {
  beansCreateBeanMutation,
  beansDeleteBeanMutation,
  beansListBeansOptions,
  beansUpdateBeanMutation,
  roastersListRoastersOptions,
} from "@/client/@tanstack/react-query.gen"
import type { BeanRead } from "@/client/types.gen"
import { CreatableCombobox } from "@/components/data/creatable-combobox"
import { DataTable } from "@/components/data/data-table"
import { DeleteAlert } from "@/components/data/delete-alert"
import { PageHeader } from "@/components/data/page-header"
import { ResourceDialog } from "@/components/data/resource-dialog"
import { RowActions } from "@/components/data/row-actions"
import { Button } from "@/components/ui/button"
import {
  FormControl,
  FormDescription,
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
import { canEdit, useCurrentUser } from "@/lib/auth"
import { PROCESSES, ROAST_LEVELS } from "@/lib/domain"
import { humanize, stripEmpty } from "@/lib/format"
import { submitAndClose, useCrudFeedback } from "@/lib/mutations"
import { zodResolver } from "@hookform/resolvers/zod"
import { useMutation, useQuery } from "@tanstack/react-query"
import { createFileRoute, useNavigate } from "@tanstack/react-router"
import type { ColumnDef } from "@tanstack/react-table"
import { Plus, X } from "lucide-react"
import { useState } from "react"
import { useForm } from "react-hook-form"
import { z } from "zod"

export const Route = createFileRoute("/_app/beans/")({ component: BeansPage })

// A bean is the coffee concept; per-purchase data (roast/purchase date, price,
// weight, finished) lives on its lots — see the bean detail page.
const schema = z.object({
  name: z.string().min(1, "Name is required"),
  roaster: z.string().min(1, "Roaster is required"),
  origin_country: z.string(),
  region: z.string(),
  producer: z.string(),
  variety: z.string(),
  process: z.enum(PROCESSES).or(z.literal("")),
  roast_level: z.enum(ROAST_LEVELS).or(z.literal("")),
  altitude_masl: z.string(),
  tasting_notes_label: z.string(),
  notes: z.string(),
})

type FormValues = z.infer<typeof schema>

const EMPTY: FormValues = {
  name: "",
  roaster: "",
  origin_country: "",
  region: "",
  producer: "",
  variety: "",
  process: "",
  roast_level: "",
  altitude_masl: "",
  tasting_notes_label: "",
  notes: "",
}

/** Text inputs give strings; altitude wants a number, and empty means "absent". */
function toPayload(values: FormValues) {
  const { altitude_masl, process, roast_level, ...rest } = values
  return {
    ...stripEmpty(rest),
    ...stripEmpty({ altitude_masl: altitude_masl === "" ? undefined : Number(altitude_masl) }),
    ...(process === "" ? {} : { process }),
    ...(roast_level === "" ? {} : { roast_level }),
  }
}

function BeansPage() {
  const { user } = useCurrentUser()
  const navigate = useNavigate()
  const feedback = useCrudFeedback()
  const { data, isLoading } = useQuery(beansListBeansOptions())
  const { data: roasters } = useQuery(roastersListRoastersOptions())

  const [editing, setEditing] = useState<BeanRead | null>(null)
  const [dialogOpen, setDialogOpen] = useState(false)
  const [deleting, setDeleting] = useState<BeanRead | null>(null)
  const [roasterFilter, setRoasterFilter] = useState("all")

  const filtered = (data ?? []).filter(
    (bean) => roasterFilter === "all" || String(bean.roaster.id) === roasterFilter,
  )

  const form = useForm<FormValues>({ resolver: zodResolver(schema), defaultValues: EMPTY })

  const create = useMutation({
    ...beansCreateBeanMutation(),
    onSuccess: feedback.onSuccess("Bean added"),
    onError: feedback.onError,
  })
  const update = useMutation({
    ...beansUpdateBeanMutation(),
    onSuccess: feedback.onSuccess("Bean updated"),
    onError: feedback.onError,
  })
  const remove = useMutation({
    ...beansDeleteBeanMutation(),
    onSuccess: feedback.onSuccess("Bean deleted"),
    onError: feedback.onError,
  })

  function openCreate() {
    setEditing(null)
    form.reset(EMPTY)
    setDialogOpen(true)
  }

  function openEdit(bean: BeanRead) {
    setEditing(bean)
    form.reset({
      name: bean.name,
      roaster: bean.roaster.name,
      origin_country: bean.origin_country ?? "",
      region: bean.region ?? "",
      producer: bean.producer ?? "",
      variety: bean.variety ?? "",
      process: bean.process ?? "",
      roast_level: bean.roast_level ?? "",
      altitude_masl: bean.altitude_masl?.toString() ?? "",
      tasting_notes_label: bean.tasting_notes_label ?? "",
      notes: bean.notes ?? "",
    })
    setDialogOpen(true)
  }

  function onSubmit(values: FormValues) {
    const body = toPayload(values)
    const request = editing
      ? update.mutateAsync({ path: { bean_id: editing.id }, body })
      : create.mutateAsync({ body: { ...body, name: values.name, roaster: values.roaster } })
    return submitAndClose(request, () => setDialogOpen(false))
  }

  const columns: ColumnDef<BeanRead, unknown>[] = [
    {
      accessorKey: "name",
      header: "Bean",
      cell: ({ row }) => (
        <div className="grid">
          <span className="font-medium">{row.original.name}</span>
          <span className="text-xs text-muted-foreground">{row.original.roaster.name}</span>
        </div>
      ),
    },
    {
      id: "origin",
      accessorFn: (bean) => bean.origin_country ?? "",
      header: "Origin",
      cell: ({ row }) => (
        <div className="grid">
          <span>{row.original.origin_country ?? "—"}</span>
          {row.original.region ? (
            <span className="text-xs text-muted-foreground">{row.original.region}</span>
          ) : null}
        </div>
      ),
    },
    {
      accessorKey: "process",
      header: "Process",
      cell: ({ row }) => humanize(row.original.process),
    },
    {
      accessorKey: "roast_level",
      header: "Roast",
      cell: ({ row }) => humanize(row.original.roast_level),
    },
    {
      id: "owner",
      accessorFn: (bean) => bean.owner.username,
      header: "Owner",
      cell: ({ row }) => (
        <span className="text-muted-foreground">{row.original.owner.username}</span>
      ),
    },
    {
      id: "actions",
      header: "",
      enableSorting: false,
      cell: ({ row }) => (
        <div className="text-right">
          <RowActions
            canEdit={canEdit(row.original, user)}
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
        title="Beans"
        description="Every coffee in the shared log. Open one to manage its lots and brews."
        actions={
          <Button onClick={openCreate}>
            <Plus className="size-4" />
            New bean
          </Button>
        }
      />

      <DataTable
        columns={columns}
        data={filtered}
        isLoading={isLoading}
        searchPlaceholder="Search beans…"
        emptyMessage="No beans yet. Add the coffee you are drinking."
        onRowClick={(bean) =>
          navigate({ to: "/beans/$beanId", params: { beanId: String(bean.id) } })
        }
        toolbar={
          <>
            <Select value={roasterFilter} onValueChange={setRoasterFilter}>
              <SelectTrigger className="w-44">
                <SelectValue placeholder="All roasters" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All roasters</SelectItem>
                {(roasters ?? []).map((roaster) => (
                  <SelectItem key={roaster.id} value={String(roaster.id)}>
                    {roaster.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            {roasterFilter !== "all" ? (
              <Button variant="ghost" size="sm" onClick={() => setRoasterFilter("all")}>
                <X className="size-4" />
                Clear
              </Button>
            ) : null}
          </>
        }
      />

      <ResourceDialog
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        title={editing ? "Edit bean" : "New bean"}
        description="Only the name and the roaster are required. Add lots (bags) from the bean's page."
        form={form}
        onSubmit={onSubmit}
        isPending={create.isPending || update.isPending}
        wide
      >
        <FormField
          control={form.control}
          name="name"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Name</FormLabel>
              <FormControl>
                <Input placeholder="Kirinyaga AA" {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        <FormField
          control={form.control}
          name="roaster"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Roaster</FormLabel>
              <FormControl>
                <CreatableCombobox
                  value={field.value}
                  onChange={field.onChange}
                  options={(roasters ?? []).map((roaster) => roaster.name)}
                  placeholder="Select or type a roaster"
                />
              </FormControl>
              <FormDescription>A roaster you type is created automatically.</FormDescription>
              <FormMessage />
            </FormItem>
          )}
        />
        <FormField
          control={form.control}
          name="origin_country"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Origin country</FormLabel>
              <FormControl>
                <Input placeholder="Kenya" {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        <FormField
          control={form.control}
          name="region"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Region</FormLabel>
              <FormControl>
                <Input placeholder="Kirinyaga" {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        <FormField
          control={form.control}
          name="producer"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Producer</FormLabel>
              <FormControl>
                <Input placeholder="Kiangoi Factory" {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        <FormField
          control={form.control}
          name="variety"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Variety</FormLabel>
              <FormControl>
                <Input placeholder="SL28, SL34" {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        <FormField
          control={form.control}
          name="process"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Process</FormLabel>
              <Select value={field.value} onValueChange={field.onChange}>
                <FormControl>
                  <SelectTrigger className="w-full">
                    <SelectValue placeholder="Select a process" />
                  </SelectTrigger>
                </FormControl>
                <SelectContent>
                  {PROCESSES.map((process) => (
                    <SelectItem key={process} value={process}>
                      {humanize(process)}
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
          name="roast_level"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Roast level</FormLabel>
              <Select value={field.value} onValueChange={field.onChange}>
                <FormControl>
                  <SelectTrigger className="w-full">
                    <SelectValue placeholder="Select a roast level" />
                  </SelectTrigger>
                </FormControl>
                <SelectContent>
                  {ROAST_LEVELS.map((level) => (
                    <SelectItem key={level} value={level}>
                      {humanize(level)}
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
          name="altitude_masl"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Altitude (masl)</FormLabel>
              <FormControl>
                <Input type="number" min={0} placeholder="1750" {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        <FormField
          control={form.control}
          name="tasting_notes_label"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Notes on the label</FormLabel>
              <FormControl>
                <Input placeholder="Blackcurrant, grapefruit" {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        <FormField
          control={form.control}
          name="notes"
          render={({ field }) => (
            <FormItem className="sm:col-span-2">
              <FormLabel>Your notes</FormLabel>
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
        description={`Delete "${deleting?.name}"? Its lots, brews and tastings go with it.`}
        isPending={remove.isPending}
        onConfirm={() => {
          if (deleting) remove.mutate({ path: { bean_id: deleting.id } })
          setDeleting(null)
        }}
      />
    </>
  )
}
