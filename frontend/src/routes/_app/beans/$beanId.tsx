import {
  beansGetBeanOptions,
  brewMethodsListBrewMethodsOptions,
  brewsListBrewsOptions,
} from "@/client/@tanstack/react-query.gen"
import type { BrewRead } from "@/client/types.gen"
import { DataTable } from "@/components/data/data-table"
import { PageHeader } from "@/components/data/page-header"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { formatDate, formatDateTime, formatNumber, humanize } from "@/lib/format"
import { useQuery } from "@tanstack/react-query"
import { Link, createFileRoute, useNavigate } from "@tanstack/react-router"
import type { ColumnDef } from "@tanstack/react-table"
import { ArrowLeft } from "lucide-react"
import type { ReactNode } from "react"

export const Route = createFileRoute("/_app/beans/$beanId")({ component: BeanDetailPage })

function BeanDetailPage() {
  const { beanId } = Route.useParams()
  const id = Number(beanId)
  const navigate = useNavigate()

  const { data: bean, isLoading } = useQuery(beansGetBeanOptions({ path: { bean_id: id } }))
  const { data: allBrews } = useQuery(brewsListBrewsOptions())
  const { data: methods } = useQuery(brewMethodsListBrewMethodsOptions())

  if (isLoading || !bean) {
    return <Skeleton className="h-64 w-full" />
  }

  const brews = allBrews?.filter((brew) => brew.bean_id === id) ?? []
  const methodName = (methodId: number) =>
    methods?.find((method) => method.id === methodId)?.name ?? `#${methodId}`

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
        actions={
          bean.is_finished ? (
            <Badge variant="outline">Finished</Badge>
          ) : (
            <Badge variant="secondary">Open</Badge>
          )
        }
      />

      <div className="grid gap-6 lg:grid-cols-3">
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
            <CardTitle>Roast</CardTitle>
          </CardHeader>
          <CardContent className="grid grid-cols-2 gap-4">
            <Field label="Level" value={humanize(bean.roast_level)} />
            <Field label="Roasted" value={formatDate(bean.roast_date)} />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Purchase</CardTitle>
          </CardHeader>
          <CardContent className="grid grid-cols-2 gap-4">
            <Field label="Bought" value={formatDate(bean.purchase_date)} />
            <Field label="Price" value={bean.price ? formatNumber(bean.price, 2) : null} />
            <Field
              label="Weight"
              value={bean.weight_grams ? `${formatNumber(bean.weight_grams, 0)} g` : null}
            />
          </CardContent>
        </Card>
      </div>

      {bean.tasting_notes_label ? (
        <Card className="mt-6">
          <CardHeader>
            <CardTitle>Tasting notes (label)</CardTitle>
          </CardHeader>
          <CardContent className="whitespace-pre-wrap text-sm">
            {bean.tasting_notes_label}
          </CardContent>
        </Card>
      ) : null}

      {bean.notes ? (
        <Card className="mt-6">
          <CardHeader>
            <CardTitle>Notes</CardTitle>
          </CardHeader>
          <CardContent className="whitespace-pre-wrap text-sm">{bean.notes}</CardContent>
        </Card>
      ) : null}

      <h2 className="mt-8 mb-4 text-lg font-semibold">
        Brews <span className="text-muted-foreground">({brews.length})</span>
      </h2>

      <DataTable
        columns={brewColumns}
        data={brews}
        emptyMessage="No brews from this bean yet."
        onRowClick={(brew) =>
          navigate({ to: "/brews/$brewId", params: { brewId: String(brew.id) } })
        }
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
