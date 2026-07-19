import {
  beansGetBeanOptions,
  brewMethodsListBrewMethodsOptions,
  brewsListBrewsOptions,
  lotsDeleteLotMutation,
  lotsListLotsOptions,
} from "@/client/@tanstack/react-query.gen"
import type { BeanLotRead, BrewRead } from "@/client/types.gen"
import { LotDialog } from "@/components/beans/lot-dialog"
import { BrewDialog } from "@/components/brews/brew-dialog"
import { DataTable } from "@/components/data/data-table"
import { DeleteAlert } from "@/components/data/delete-alert"
import { PageHeader } from "@/components/data/page-header"
import { RowActions } from "@/components/data/row-actions"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { StarRating } from "@/components/ui/star-rating"
import { canEdit, useCurrentUser } from "@/lib/auth"
import { formatDate, formatDateTime, formatNumber, humanize } from "@/lib/format"
import { useCrudFeedback } from "@/lib/mutations"
import { useMutation, useQuery } from "@tanstack/react-query"
import { Link, createFileRoute, useNavigate } from "@tanstack/react-router"
import type { ColumnDef } from "@tanstack/react-table"
import { ArrowLeft, Plus } from "lucide-react"
import type { ReactNode } from "react"
import { useState } from "react"

export const Route = createFileRoute("/_app/beans/$beanId")({ component: BeanDetailPage })

function BeanDetailPage() {
  const { beanId } = Route.useParams()
  const id = Number(beanId)
  const navigate = useNavigate()
  const { user } = useCurrentUser()
  const feedback = useCrudFeedback()

  const { data: bean, isLoading } = useQuery(beansGetBeanOptions({ path: { bean_id: id } }))
  const { data: lots } = useQuery(lotsListLotsOptions({ path: { bean_id: id } }))
  const { data: allBrews } = useQuery(brewsListBrewsOptions())
  const { data: methods } = useQuery(brewMethodsListBrewMethodsOptions())

  const [brewDialogOpen, setBrewDialogOpen] = useState(false)
  const [lotDialogOpen, setLotDialogOpen] = useState(false)
  const [editingLot, setEditingLot] = useState<BeanLotRead | null>(null)
  const [deletingLot, setDeletingLot] = useState<BeanLotRead | null>(null)

  const removeLot = useMutation({
    ...lotsDeleteLotMutation(),
    onSuccess: feedback.onSuccess("Lot deleted"),
    onError: feedback.onError,
  })

  if (isLoading || !bean) {
    return <Skeleton className="h-64 w-full" />
  }

  const brews = allBrews?.filter((brew) => brew.bean_id === id) ?? []
  const methodName = (methodId: number) =>
    methods?.find((method) => method.id === methodId)?.name ?? `#${methodId}`

  const lotColumns: ColumnDef<BeanLotRead, unknown>[] = [
    {
      accessorKey: "purchase_date",
      header: "Bought",
      cell: ({ row }) => formatDate(row.original.purchase_date),
    },
    {
      accessorKey: "roast_date",
      header: "Roasted",
      cell: ({ row }) => formatDate(row.original.roast_date),
    },
    {
      accessorKey: "weight_grams",
      header: "Weight",
      cell: ({ row }) =>
        row.original.weight_grams ? `${formatNumber(row.original.weight_grams, 0)} g` : "—",
    },
    {
      accessorKey: "price",
      header: "Price",
      cell: ({ row }) => (row.original.price ? formatNumber(row.original.price, 2) : "—"),
    },
    {
      accessorKey: "is_finished",
      header: "Status",
      cell: ({ row }) =>
        row.original.is_finished ? (
          <Badge variant="outline">Finished</Badge>
        ) : (
          <Badge variant="secondary">Open</Badge>
        ),
    },
    {
      id: "owner",
      accessorFn: (lot) => lot.owner.username,
      header: "By",
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
            onEdit={() => {
              setEditingLot(row.original)
              setLotDialogOpen(true)
            }}
            onDelete={() => setDeletingLot(row.original)}
          />
        </div>
      ),
    },
  ]

  const brewColumns: ColumnDef<BrewRead, unknown>[] = [
    {
      accessorKey: "brewed_at",
      header: "Brewed",
      cell: ({ row }) => formatDateTime(row.original.brewed_at),
    },
    {
      id: "method",
      accessorFn: (brew) => methodName(brew.method_id),
      header: "Method",
    },
    {
      accessorKey: "ratio",
      header: "Ratio",
      cell: ({ row }) =>
        row.original.ratio ? `1:${formatNumber(row.original.ratio, 2)}` : "—",
    },
    {
      id: "author",
      accessorFn: (brew) => brew.author.username,
      header: "By",
      cell: ({ row }) => (
        <span className="text-muted-foreground">{row.original.author.username}</span>
      ),
    },
  ]

  return (
    <>
      <Button asChild variant="ghost" size="sm" className="mb-2 -ml-2">
        <Link to="/beans">
          <ArrowLeft className="size-4" />
          All beans
        </Link>
      </Button>

      <PageHeader
        title={bean.name}
        description={
          <>
            <Link
              to="/roasters/$roasterId"
              params={{ roasterId: String(bean.roaster.id) }}
              className="text-primary underline-offset-4 hover:underline"
            >
              {bean.roaster.name}
            </Link>
            {" · "}
            {bean.owner.username}
          </>
        }
      />

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Origin</CardTitle>
          </CardHeader>
          <CardContent className="grid grid-cols-2 gap-4">
            <Field label="Country" value={bean.origin_country} />
            <Field label="Region" value={bean.region} />
            <Field label="Producer" value={bean.producer} />
            <Field label="Variety" value={bean.variety} />
            <Field label="Process" value={humanize(bean.process)} />
            <Field
              label="Altitude"
              value={bean.altitude_masl ? `${bean.altitude_masl} masl` : null}
            />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Roast &amp; notes</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-4">
            <div className="grid grid-cols-2 gap-4">
              <Field label="Roast level" value={humanize(bean.roast_level)} />
              <Field label="Roast type" value={humanize(bean.roast_type)} />
              <Field label="Blend" value={humanize(bean.blend)} />
              <Field
                label="Rating"
                value={
                  (bean.rating ?? 0) > 0 ? (
                    <StarRating value={bean.rating ?? 0} readOnly size={16} />
                  ) : null
                }
              />
            </div>
            <Field label="Tasting notes (label)" value={bean.tasting_notes_label} />
            {bean.website ? (
              <Field
                label="Website"
                value={
                  <a
                    href={bean.website}
                    target="_blank"
                    rel="noreferrer"
                    className="text-primary underline-offset-4 hover:underline"
                  >
                    {bean.website}
                  </a>
                }
              />
            ) : null}
            {bean.notes ? <Field label="Your notes" value={bean.notes} /> : null}
          </CardContent>
        </Card>
      </div>

      <div className="mt-8 mb-4 flex items-center justify-between">
        <h2 className="text-lg font-semibold">
          Lots <span className="text-muted-foreground">({lots?.length ?? 0})</span>
        </h2>
        <Button
          variant="outline"
          onClick={() => {
            setEditingLot(null)
            setLotDialogOpen(true)
          }}
        >
          <Plus className="size-4" />
          Add lot
        </Button>
      </div>

      <DataTable
        columns={lotColumns}
        data={lots}
        emptyMessage="No lots yet. Add the bag you bought."
      />

      <div className="mt-8 mb-4 flex items-center justify-between">
        <h2 className="text-lg font-semibold">
          Brews <span className="text-muted-foreground">({brews.length})</span>
        </h2>
        <Button variant="outline" onClick={() => setBrewDialogOpen(true)}>
          <Plus className="size-4" />
          Log brew
        </Button>
      </div>

      <DataTable
        columns={brewColumns}
        data={brews}
        emptyMessage="No brews from this bean yet."
        onRowClick={(brew) =>
          navigate({ to: "/brews/$brewId", params: { brewId: String(brew.id) } })
        }
      />

      <LotDialog open={lotDialogOpen} onOpenChange={setLotDialogOpen} beanId={bean.id} lot={editingLot} />
      <BrewDialog
        open={brewDialogOpen}
        onOpenChange={setBrewDialogOpen}
        brew={null}
        defaultBeanId={bean.id}
      />
      <DeleteAlert
        open={deletingLot !== null}
        onOpenChange={(open) => !open && setDeletingLot(null)}
        description="Delete this lot? Brews attributed to it keep their history."
        isPending={removeLot.isPending}
        onConfirm={() => {
          if (deletingLot) removeLot.mutate({ path: { lot_id: deletingLot.id } })
          setDeletingLot(null)
        }}
      />
    </>
  )
}

function Field({ label, value }: { label: string; value: ReactNode }) {
  return (
    <div className="grid gap-1">
      <span className="text-xs text-muted-foreground">{label}</span>
      <span className="font-medium">{value || "—"}</span>
    </div>
  )
}
