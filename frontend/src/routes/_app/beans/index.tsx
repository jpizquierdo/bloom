import {
  beansDeleteBeanMutation,
  beansListBeansOptions,
  roastersListRoastersOptions,
} from "@/client/@tanstack/react-query.gen"
import type { BeanRead } from "@/client/types.gen"
import { BeanDialog } from "@/components/beans/bean-dialog"
import { DataTable } from "@/components/data/data-table"
import { DeleteAlert } from "@/components/data/delete-alert"
import { PageHeader } from "@/components/data/page-header"
import { RowActions } from "@/components/data/row-actions"
import { Button } from "@/components/ui/button"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { StarRating } from "@/components/ui/star-rating"
import { canEdit, useCurrentUser } from "@/lib/auth"
import { humanize } from "@/lib/format"
import { useCrudFeedback } from "@/lib/mutations"
import { useMutation, useQuery } from "@tanstack/react-query"
import { createFileRoute, useNavigate } from "@tanstack/react-router"
import type { ColumnDef } from "@tanstack/react-table"
import { Plus, X } from "lucide-react"
import { useState } from "react"

export const Route = createFileRoute("/_app/beans/")({ component: BeansPage })

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

  const remove = useMutation({
    ...beansDeleteBeanMutation(),
    onSuccess: feedback.onSuccess("Bean deleted"),
    onError: feedback.onError,
  })

  function openCreate() {
    setEditing(null)
    setDialogOpen(true)
  }

  function openEdit(bean: BeanRead) {
    setEditing(bean)
    setDialogOpen(true)
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
      accessorKey: "rating",
      header: "Rating",
      cell: ({ row }) =>
        (row.original.rating ?? 0) > 0 ? (
          <StarRating value={row.original.rating ?? 0} readOnly size={14} />
        ) : (
          <span className="text-muted-foreground">—</span>
        ),
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

      <BeanDialog open={dialogOpen} onOpenChange={setDialogOpen} bean={editing} />

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
