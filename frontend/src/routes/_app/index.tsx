import {
  beansListBeansOptions,
  brewMethodsListBrewMethodsOptions,
  brewsListBrewsOptions,
  tastingsListAllTastingsOptions,
} from "@/client/@tanstack/react-query.gen"
import { BrewDiagnostics } from "@/components/brews/diagnostics"
import { PageHeader } from "@/components/data/page-header"
import { Button } from "@/components/ui/button"
import { Card, CardAction, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { useCurrentUser } from "@/lib/auth"
import { formatDateTime, formatNumber } from "@/lib/format"
import { useQuery } from "@tanstack/react-query"
import { Link, createFileRoute } from "@tanstack/react-router"
import type { LucideIcon } from "lucide-react"
import { Bean, Coffee, NotebookPen } from "lucide-react"

export const Route = createFileRoute("/_app/")({ component: DashboardPage })

function DashboardPage() {
  const { user } = useCurrentUser()
  const { data: beans } = useQuery(beansListBeansOptions())
  const { data: brews } = useQuery(brewsListBrewsOptions())
  const { data: tastings } = useQuery(tastingsListAllTastingsOptions())
  const { data: methods } = useQuery(brewMethodsListBrewMethodsOptions())

  const recentBrews = [...(brews ?? [])]
    .sort((a, b) => (b.brewed_at ?? "").localeCompare(a.brewed_at ?? ""))
    .slice(0, 5)

  const beanName = (id: number) => beans?.find((bean) => bean.id === id)?.name ?? `#${id}`
  const methodName = (id: number) =>
    methods?.find((method) => method.id === id)?.name ?? `#${id}`

  return (
    <>
      <PageHeader
        title={`Welcome back${user ? `, ${user.username}` : ""}`}
        description="What the whole log has been drinking."
      />

      <div className="grid gap-4 sm:grid-cols-3">
        <Stat label="Coffees" value={beans?.length ?? 0} icon={Bean} />
        <Stat label="Brews" value={brews?.length ?? 0} icon={Coffee} />
        <Stat label="Tastings" value={tastings?.length ?? 0} icon={NotebookPen} />
      </div>

      <Card className="mt-6">
        <CardHeader>
          <CardTitle>Recent brews</CardTitle>
          <CardAction>
            <Button asChild variant="ghost" size="sm">
              <Link to="/brews">View all</Link>
            </Button>
          </CardAction>
        </CardHeader>
        <CardContent className="grid gap-1">
          {recentBrews.length === 0 ? (
            <p className="py-6 text-center text-sm text-muted-foreground">
              No brews yet. Log the last coffee you made.
            </p>
          ) : (
            recentBrews.map((brew) => (
              <Link
                key={brew.id}
                to="/brews/$brewId"
                params={{ brewId: String(brew.id) }}
                className="flex flex-wrap items-center gap-3 rounded-md px-2 py-2.5 hover:bg-muted/60"
              >
                <div className="grid min-w-40 flex-1">
                  <span className="font-medium">{beanName(brew.bean_id)}</span>
                  <span className="text-xs text-muted-foreground">
                    {methodName(brew.method_id)} · {formatDateTime(brew.brewed_at)}
                  </span>
                </div>
                <span className="text-sm tabular-nums text-muted-foreground">
                  {formatNumber(brew.dose_grams)} g
                  {brew.ratio ? ` · 1:${formatNumber(brew.ratio, 2)}` : ""}
                </span>
                <BrewDiagnostics brew={brew} />
              </Link>
            ))
          )}
        </CardContent>
      </Card>
    </>
  )
}

function Stat({
  label,
  value,
  hint,
  icon: Icon,
}: {
  label: string
  value: number
  hint?: string
  icon: LucideIcon
}) {
  return (
    <Card>
      <CardContent className="flex items-center gap-4">
        <span className="flex size-10 items-center justify-center rounded-lg bg-accent text-accent-foreground">
          <Icon className="size-5" />
        </span>
        <div className="grid">
          <span className="text-2xl font-semibold tabular-nums">{value}</span>
          <span className="text-sm text-muted-foreground">
            {label}
            {hint ? ` · ${hint}` : ""}
          </span>
        </div>
      </CardContent>
    </Card>
  )
}
