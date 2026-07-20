import {
  beansListBeansOptions,
  brewMethodsListBrewMethodsOptions,
  brewsDeleteBrewMutation,
  brewsListBrewsOptions,
  equipmentListEquipmentOptions,
  roastersListRoastersOptions,
} from "@/client/@tanstack/react-query.gen"
import type { BrewRead } from "@/client/types.gen"
import { BrewDialog } from "@/components/brews/brew-dialog"
import { BrewDiagnostics } from "@/components/brews/diagnostics"
import { Combobox } from "@/components/data/combobox"
import { DeleteAlert } from "@/components/data/delete-alert"
import { PageHeader } from "@/components/data/page-header"
import { RowActions } from "@/components/data/row-actions"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardAction,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Skeleton } from "@/components/ui/skeleton"
import { canEdit, useCurrentUser } from "@/lib/auth"
import { beanLabel } from "@/lib/domain"
import { formatDateTime, formatNumber, formatSeconds } from "@/lib/format"
import { useCrudFeedback } from "@/lib/mutations"
import { useMutation, useQuery } from "@tanstack/react-query"
import { Link, createFileRoute } from "@tanstack/react-router"
import { Plus, X } from "lucide-react"
import type { ReactNode } from "react"
import { useState } from "react"

export const Route = createFileRoute("/_app/brews/")({ component: BrewsPage })

function BrewsPage() {
  const { user } = useCurrentUser()
  const feedback = useCrudFeedback()

  const { data, isLoading } = useQuery(brewsListBrewsOptions())
  const { data: beans } = useQuery(beansListBeansOptions())
  const { data: methods } = useQuery(brewMethodsListBrewMethodsOptions())
  const { data: equipment } = useQuery(equipmentListEquipmentOptions())
  const { data: roasters } = useQuery(roastersListRoastersOptions())

  const [editing, setEditing] = useState<BrewRead | null>(null)
  const [dialogOpen, setDialogOpen] = useState(false)
  const [deleting, setDeleting] = useState<BrewRead | null>(null)
  const [roasterFilter, setRoasterFilter] = useState("all")
  const [beanFilter, setBeanFilter] = useState("all")
  const [search, setSearch] = useState("")

  const remove = useMutation({
    ...brewsDeleteBrewMutation(),
    onSuccess: feedback.onSuccess("Brew deleted"),
    onError: feedback.onError,
  })

  const beanOf = (id: number) => beans?.find((bean) => bean.id === id)
  const beanName = (id: number) => beanOf(id)?.name ?? `#${id}`
  const roasterName = (id: number) => beanOf(id)?.roaster.name
  const methodOf = (id: number) => methods?.find((method) => method.id === id)
  const methodName = (id: number) => methodOf(id)?.name ?? `#${id}`
  const grinderName = (id: number | null | undefined) =>
    equipment?.find((item) => item.id === id)?.name ?? "—"
  const roasterIdForBean = (beanId: number) => beanOf(beanId)?.roaster.id

  // When a roaster is picked, the bean dropdown only offers that roaster's beans.
  const beanOptions = (beans ?? []).filter(
    (bean) => roasterFilter === "all" || String(bean.roaster.id) === roasterFilter,
  )

  const query = search.trim().toLowerCase()
  const filtered = (data ?? [])
    .filter((brew) => {
      if (roasterFilter !== "all" && String(roasterIdForBean(brew.bean_id)) !== roasterFilter) {
        return false
      }
      if (beanFilter !== "all" && String(brew.bean_id) !== beanFilter) return false
      if (query !== "") {
        const haystack = [
          beanName(brew.bean_id),
          roasterName(brew.bean_id),
          methodName(brew.method_id),
          brew.author.username,
        ]
          .filter(Boolean)
          .join(" ")
          .toLowerCase()
        if (!haystack.includes(query)) return false
      }
      return true
    })
    .sort((a, b) => (b.brewed_at ?? "").localeCompare(a.brewed_at ?? ""))

  const hasFilters = roasterFilter !== "all" || beanFilter !== "all"

  function pickRoaster(value: string) {
    setRoasterFilter(value)
    setBeanFilter("all") // the previously chosen bean may not belong to the new roaster
  }

  function clearFilters() {
    setRoasterFilter("all")
    setBeanFilter("all")
  }

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

      <div className="flex flex-wrap items-center gap-2">
        <Input
          placeholder="Search brews…"
          value={search}
          onChange={(event) => setSearch(event.target.value)}
          className="w-full sm:w-56"
        />
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
      </div>

      {isLoading ? (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 3 }, (_, i) => (
            <Skeleton key={i} className="h-56 w-full" />
          ))}
        </div>
      ) : filtered.length === 0 ? (
        <div className="rounded-lg border border-dashed p-8 text-center text-sm text-muted-foreground">
          No brews yet. Log the last coffee you made.
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {filtered.map((brew) => {
            const method = methodOf(brew.method_id)
            const roaster = roasterName(brew.bean_id)
            // Espresso's meaningful "out" is the beverage yield; for filter/immersion the
            // recipe is defined by the water you pour, so show that instead.
            const out =
              method?.category === "espresso" ? brew.yield_grams : brew.water_grams
            const inOut = `${formatNumber(brew.dose_grams)} g${out ? ` → ${formatNumber(out)} g` : ""}`

            const hasDiagnostics = Boolean(
              brew.diagnostics?.strength || brew.diagnostics?.extraction,
            )
            const hasNumbers = Boolean(brew.tds_percent || brew.extraction_yield_percent)

            return (
              <Card key={brew.id}>
                <CardHeader>
                  <CardDescription>
                    {formatDateTime(brew.brewed_at)} · {brew.author.username}
                  </CardDescription>
                  <CardTitle className="text-base">
                    <Link
                      to="/brews/$brewId"
                      params={{ brewId: String(brew.id) }}
                      className="hover:underline"
                    >
                      {beanName(brew.bean_id)}
                    </Link>
                    {roaster ? (
                      <span className="ml-1 font-normal text-muted-foreground">({roaster})</span>
                    ) : null}
                  </CardTitle>
                  <CardAction>
                    <RowActions
                      canEdit={canEdit(brew, user)}
                      onEdit={() => {
                        setEditing(brew)
                        setDialogOpen(true)
                      }}
                      onDelete={() => setDeleting(brew)}
                    />
                  </CardAction>
                </CardHeader>
                <CardContent className="grid gap-3">
                  <div className="grid grid-cols-2 gap-x-4 gap-y-3">
                    <Metric label="Method" value={methodName(brew.method_id)} />
                    <Metric label="Grinder" value={grinderName(brew.grinder_id)} />
                    <Metric label="In → Out" value={inOut} />
                    <Metric label="Time" value={formatSeconds(brew.brew_time_seconds)} />
                    <Metric label="Grind setting" value={brew.grind_setting ?? "—"} />
                    <Metric
                      label="Temp"
                      value={
                        brew.water_temp_celsius
                          ? `${formatNumber(brew.water_temp_celsius)} °C`
                          : "—"
                      }
                    />
                  </div>

                  {hasDiagnostics || hasNumbers ? (
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      {hasDiagnostics ? <BrewDiagnostics brew={brew} /> : <span />}
                      {hasNumbers ? (
                        <div className="flex gap-3 text-sm tabular-nums text-muted-foreground">
                          {brew.tds_percent ? (
                            <span>TDS {formatNumber(brew.tds_percent, 2)}%</span>
                          ) : null}
                          {brew.extraction_yield_percent ? (
                            <span>EY {formatNumber(brew.extraction_yield_percent, 2)}%</span>
                          ) : null}
                        </div>
                      ) : null}
                    </div>
                  ) : null}
                </CardContent>
              </Card>
            )
          })}
        </div>
      )}

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

function Metric({ label, value }: { label: string; value: ReactNode }) {
  return (
    <div className="grid gap-1">
      <span className="text-xs text-muted-foreground">{label}</span>
      <span className="font-medium tabular-nums">{value}</span>
    </div>
  )
}
