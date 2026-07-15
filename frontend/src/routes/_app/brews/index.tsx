import {
  beansListBeansOptions,
  brewMethodsListBrewMethodsOptions,
  brewsDeleteBrewMutation,
  brewsListBrewsOptions,
  roastersListRoastersOptions,
} from "@/client/@tanstack/react-query.gen"
import type { BrewRead } from "@/client/types.gen"
import { BrewDialog } from "@/components/brews/brew-dialog"
import { BrewDiagnostics } from "@/components/brews/diagnostics"
import { Combobox } from "@/components/data/combobox"
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
import { canEdit, useCurrentUser } from "@/lib/auth"
import { beanLabel } from "@/lib/domain"
import { formatDateTime, formatNumber, formatSeconds } from "@/lib/format"
import { useCrudFeedback } from "@/lib/mutations"
import { useMutation, useQuery } from "@tanstack/react-query"
import { createFileRoute, useNavigate } from "@tanstack/react-router"
import type { ColumnDef } from "@tanstack/react-table"
import { Plus, X } from "lucide-react"
import { useState } from "react"

export const Route = createFileRoute("/_app/brews/")({ component: BrewsPage })

function BrewsPage() {
  const { user } = useCurrentUser()
  const navigate = useNavigate()
  const feedback = useCrudFeedback()

  const { data, isLoading } = useQuery(brewsListBrewsOptions())
  const { data: beans } = useQuery(beansListBeansOptions())
  const { data: methods } = useQuery(brewMethodsListBrewMethodsOptions())
  const { data: roasters } = useQuery(roastersListRoastersOptions())

  const [editing, setEditing] = useState<BrewRead | null>(null)
  const [dialogOpen, setDialogOpen] = useState(false)
  const [deleting, setDeleting] = useState<BrewRead | null>(null)
  const [roasterFilter, setRoasterFilter] = useState("all")
  const [beanFilter, setBeanFilter] = useState("all")

  const remove = useMutation({
    ...brewsDeleteBrewMutation(),
    onSuccess: feedback.onSuccess("Brew deleted"),
    onError: feedback.onError,
  })

  const beanName = (id: number) => beans?.find((bean) => bean.id === id)?.name ?? `#${id}`
  const methodName = (id: number) =>
    methods?.find((method) => method.id === id)?.name ?? `#${id}`
  const roasterIdForBean = (beanId: number) =>
    beans?.find((bean) => bean.id === beanId)?.roaster.id

  // When a roaster is picked, the bean dropdown only offers that roaster's beans.
  const beanOptions = (beans ?? []).filter(
    (bean) => roasterFilter === "all" || String(bean.roaster.id) === roasterFilter,
  )

  const filtered = (data ?? []).filter((brew) => {
    if (roasterFilter !== "all" && String(roasterIdForBean(brew.bean_id)) !== roasterFilter) {
      return false
    }
    if (beanFilter !== "all" && String(brew.bean_id) !== beanFilter) return false
    return true
  })

  const hasFilters = roasterFilter !== "all" || beanFilter !== "all"

  function pickRoaster(value: string) {
    setRoasterFilter(value)
    setBeanFilter("all") // the previously chosen bean may not belong to the new roaster
  }

  function clearFilters() {
    setRoasterFilter("all")
    setBeanFilter("all")
  }

  const columns: ColumnDef<BrewRead, unknown>[] = [
    {
      id: "bean",
      accessorFn: (brew) => beanName(brew.bean_id),
      header: "Bean",
      cell: ({ row }) => (
        <div className="grid">
          <span className="font-medium">{beanName(row.original.bean_id)}</span>
          <span className="text-xs text-muted-foreground">
            {methodName(row.original.method_id)}
          </span>
        </div>
      ),
    },
    {
      accessorKey: "brewed_at",
      header: "Brewed",
      cell: ({ row }) => formatDateTime(row.original.brewed_at),
    },
    {
      id: "author",
      accessorFn: (brew) => brew.author.username,
      header: "By",
      cell: ({ row }) => (
        <span className="text-muted-foreground">{row.original.author.username}</span>
      ),
    },
    {
      id: "recipe",
      header: "Dose → yield",
      enableSorting: false,
      cell: ({ row }) => (
        <span className="tabular-nums">
          {formatNumber(row.original.dose_grams)} g
          {row.original.yield_grams ? ` → ${formatNumber(row.original.yield_grams)} g` : ""}
        </span>
      ),
    },
    {
      accessorKey: "ratio",
      header: "Ratio",
      cell: ({ row }) =>
        row.original.ratio ? (
          <span className="tabular-nums">1:{formatNumber(row.original.ratio, 2)}</span>
        ) : (
          "—"
        ),
    },
    {
      accessorKey: "brew_time_seconds",
      header: "Time",
      cell: ({ row }) => (
        <span className="tabular-nums">{formatSeconds(row.original.brew_time_seconds)}</span>
      ),
    },
    {
      accessorKey: "tds_percent",
      header: "TDS",
      cell: ({ row }) => (
        <span className="tabular-nums">{formatNumber(row.original.tds_percent, 2)}</span>
      ),
    },
    {
      id: "diagnostics",
      header: "Diagnostics",
      enableSorting: false,
      cell: ({ row }) => <BrewDiagnostics brew={row.original} />,
    },
    {
      id: "actions",
      header: "",
      enableSorting: false,
      cell: ({ row }) => (
        <div className="text-right">
          <RowActions
            canEdit={canEdit(row.original, user)}
            onEdit={() => {
              setEditing(row.original)
              setDialogOpen(true)
            }}
            onDelete={() => setDeleting(row.original)}
          />
        </div>
      ),
    },
  ]

  return (
    <>
      <PageHeader
        title="Brews"
        description="Every extraction in the log. Open one to taste it."
        actions={
          <Button
            onClick={() => {
              setEditing(null)
              setDialogOpen(true)
            }}
          >
            <Plus className="size-4" />
            Log brew
          </Button>
        }
      />

      <DataTable
        columns={columns}
        data={filtered}
        isLoading={isLoading}
        searchPlaceholder="Search brews…"
        emptyMessage="No brews yet. Log the last coffee you made."
        onRowClick={(brew) => navigate({ to: "/brews/$brewId", params: { brewId: String(brew.id) } })}
        toolbar={
          <>
            <Select value={roasterFilter} onValueChange={pickRoaster}>
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

            <Combobox
              value={beanFilter}
              onChange={setBeanFilter}
              options={[
                { value: "all", label: "All beans" },
                ...beanOptions.map((bean) => ({ value: String(bean.id), label: beanLabel(bean) })),
              ]}
              placeholder="All beans"
              searchPlaceholder="Search beans…"
              className="w-56"
            />

            {hasFilters ? (
              <Button variant="ghost" size="sm" onClick={clearFilters}>
                <X className="size-4" />
                Clear
              </Button>
            ) : null}
          </>
        }
      />

      <BrewDialog open={dialogOpen} onOpenChange={setDialogOpen} brew={editing} />

      <DeleteAlert
        open={deleting !== null}
        onOpenChange={(open) => !open && setDeleting(null)}
        description="Delete this brew? Its tastings go with it."
        isPending={remove.isPending}
        onConfirm={() => {
          if (deleting) remove.mutate({ path: { brew_id: deleting.id } })
          setDeleting(null)
        }}
      />
    </>
  )
}
