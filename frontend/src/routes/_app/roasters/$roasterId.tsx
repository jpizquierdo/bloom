import {
  beansListBeansOptions,
  roastersGetRoasterOptions,
} from "@/client/@tanstack/react-query.gen"
import type { BeanRead } from "@/client/types.gen"
import { DataTable } from "@/components/data/data-table"
import { PageHeader } from "@/components/data/page-header"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { humanize } from "@/lib/format"
import { useQuery } from "@tanstack/react-query"
import { Link, createFileRoute, useNavigate } from "@tanstack/react-router"
import type { ColumnDef } from "@tanstack/react-table"
import { ArrowLeft } from "lucide-react"

export const Route = createFileRoute("/_app/roasters/$roasterId")({ component: RoasterDetailPage })

function RoasterDetailPage() {
  const { roasterId } = Route.useParams()
  const id = Number(roasterId)
  const navigate = useNavigate()

  const { data: roaster, isLoading } = useQuery(
    roastersGetRoasterOptions({ path: { roaster_id: id } }),
  )
  const { data: allBeans } = useQuery(beansListBeansOptions())

  if (isLoading || !roaster) {
    return <Skeleton className="h-64 w-full" />
  }

  const beans = allBeans?.filter((bean) => bean.roaster.id === id) ?? []

  const columns: ColumnDef<BeanRead, unknown>[] = [
    { accessorKey: "name", header: "Bean" },
    {
      id: "origin",
      accessorFn: (bean) => bean.origin_country ?? "",
      header: "Origin",
      cell: ({ row }) => row.original.origin_country ?? "—",
    },
    {
      accessorKey: "roast_level",
      header: "Roast",
      cell: ({ row }) => humanize(row.original.roast_level) || "—",
    },
    {
      id: "owner",
      accessorFn: (bean) => bean.owner.username,
      header: "Owner",
      cell: ({ row }) => (
        <span className="text-muted-foreground">{row.original.owner.username}</span>
      ),
    },
  ]

  return (
    <>
      <Button asChild variant="ghost" size="sm" className="mb-2 -ml-2">
        <Link to="/roasters">
          <ArrowLeft className="size-4" />
          All roasters
        </Link>
      </Button>

      <PageHeader
        title={roaster.name}
        description={[roaster.city, roaster.country].filter(Boolean).join(" · ") || undefined}
        actions={
          roaster.website ? (
            <Button asChild variant="outline">
              <a href={roaster.website} target="_blank" rel="noreferrer">
                {roaster.website.replace(/^https?:\/\//, "")}
              </a>
            </Button>
          ) : null
        }
      />

      {roaster.notes ? (
        <p className="mb-6 whitespace-pre-wrap text-sm text-muted-foreground">{roaster.notes}</p>
      ) : null}

      <h2 className="mb-4 text-lg font-semibold">
        Beans <span className="text-muted-foreground">({beans.length})</span>
      </h2>

      <DataTable
        columns={columns}
        data={beans}
        searchPlaceholder="Search beans…"
        emptyMessage="No beans from this roaster yet."
        onRowClick={(bean) =>
          navigate({ to: "/beans/$beanId", params: { beanId: String(bean.id) } })
        }
      />
    </>
  )
}
