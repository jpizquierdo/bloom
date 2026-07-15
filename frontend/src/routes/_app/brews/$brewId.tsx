import {
  beansGetBeanOptions,
  brewMethodsListBrewMethodsOptions,
  brewsGetBrewOptions,
  equipmentListEquipmentOptions,
  tastingsDeleteTastingMutation,
  tastingsListTastingsOptions,
} from "@/client/@tanstack/react-query.gen"
import type { TastingRead } from "@/client/types.gen"
import { BrewDialog } from "@/components/brews/brew-dialog"
import { BrewDiagnostics } from "@/components/brews/diagnostics"
import { TastingDialog } from "@/components/brews/tasting-dialog"
import { DeleteAlert } from "@/components/data/delete-alert"
import { PageHeader } from "@/components/data/page-header"
import { RowActions } from "@/components/data/row-actions"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardAction,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { canEdit, useCurrentUser } from "@/lib/auth"
import { TASTING_SCORES } from "@/lib/domain"
import { formatDateTime, formatNumber, formatSeconds, humanize } from "@/lib/format"
import { useCrudFeedback } from "@/lib/mutations"
import { useMutation, useQuery } from "@tanstack/react-query"
import { Link, createFileRoute } from "@tanstack/react-router"
import { ArrowLeft, Pencil, Plus } from "lucide-react"
import type { ReactNode } from "react"
import { useState } from "react"

export const Route = createFileRoute("/_app/brews/$brewId")({ component: BrewDetailPage })

function BrewDetailPage() {
  const { brewId } = Route.useParams()
  const id = Number(brewId)
  const { user } = useCurrentUser()
  const feedback = useCrudFeedback()

  const { data: brew, isLoading } = useQuery(brewsGetBrewOptions({ path: { brew_id: id } }))
  const { data: tastings } = useQuery(tastingsListTastingsOptions({ path: { brew_id: id } }))
  const { data: methods } = useQuery(brewMethodsListBrewMethodsOptions())
  const { data: equipment } = useQuery(equipmentListEquipmentOptions())
  const { data: bean } = useQuery({
    ...beansGetBeanOptions({ path: { bean_id: brew?.bean_id ?? 0 } }),
    enabled: brew !== undefined,
  })

  const [brewDialogOpen, setBrewDialogOpen] = useState(false)
  const [tastingDialogOpen, setTastingDialogOpen] = useState(false)
  const [editingTasting, setEditingTasting] = useState<TastingRead | null>(null)
  const [deletingTasting, setDeletingTasting] = useState<TastingRead | null>(null)

  const removeTasting = useMutation({
    ...tastingsDeleteTastingMutation(),
    onSuccess: feedback.onSuccess("Tasting deleted"),
    onError: feedback.onError,
  })

  if (isLoading || !brew) {
    return <Skeleton className="h-64 w-full" />
  }

  const method = methods?.find((item) => item.id === brew.method_id)
  const grinder = equipment?.find((item) => item.id === brew.grinder_id)

  return (
    <>
      <Button asChild variant="ghost" size="sm" className="mb-2 -ml-2">
        <Link to="/brews">
          <ArrowLeft className="size-4" />
          All brews
        </Link>
      </Button>

      <PageHeader
        title={bean ? bean.name : "Brew"}
        description={[
          bean?.roaster.name,
          method?.name,
          formatDateTime(brew.brewed_at),
          `by ${brew.author.username}`,
        ]
          .filter(Boolean)
          .join(" · ")}
        actions={
          canEdit(brew, user) ? (
            <Button variant="outline" onClick={() => setBrewDialogOpen(true)}>
              <Pencil className="size-4" />
              Edit brew
            </Button>
          ) : null
        }
      />

      <div className="grid gap-6 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Recipe</CardTitle>
          </CardHeader>
          <CardContent className="grid grid-cols-2 gap-4 sm:grid-cols-4">
            <Metric label="Dose" value={`${formatNumber(brew.dose_grams)} g`} />
            <Metric
              label="Yield"
              value={brew.yield_grams ? `${formatNumber(brew.yield_grams)} g` : "—"}
            />
            <Metric
              label="Water"
              value={brew.water_grams ? `${formatNumber(brew.water_grams)} g` : "—"}
            />
            <Metric
              label="Ratio"
              value={brew.ratio ? `1:${formatNumber(brew.ratio, 2)}` : "—"}
            />
            <Metric label="Time" value={formatSeconds(brew.brew_time_seconds)} />
            <Metric
              label="Temp"
              value={
                brew.water_temp_celsius ? `${formatNumber(brew.water_temp_celsius)} °C` : "—"
              }
            />
            <Metric label="Grinder" value={grinder?.name ?? "—"} />
            <Metric label="Setting" value={brew.grind_setting ?? "—"} />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Extraction</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-4">
            <div className="grid grid-cols-2 gap-4">
              <Metric label="TDS" value={formatNumber(brew.tds_percent, 2)} />
              <Metric
                label="Yield %"
                value={formatNumber(brew.extraction_yield_percent, 2)}
              />
            </div>
            <BrewDiagnostics brew={brew} />
          </CardContent>
        </Card>
      </div>

      {brew.notes ? (
        <Card className="mt-6">
          <CardHeader>
            <CardTitle>Notes</CardTitle>
          </CardHeader>
          <CardContent className="whitespace-pre-wrap text-sm">{brew.notes}</CardContent>
        </Card>
      ) : null}

      <div className="mt-8 mb-4 flex items-center justify-between">
        <h2 className="text-lg font-semibold">Tastings</h2>
        <Button
          variant="outline"
          onClick={() => {
            setEditingTasting(null)
            setTastingDialogOpen(true)
          }}
        >
          <Plus className="size-4" />
          Add tasting
        </Button>
      </div>

      {tastings && tastings.length > 0 ? (
        <div className="grid gap-4 md:grid-cols-2">
          {tastings.map((tasting) => (
            <Card key={tasting.id}>
              <CardHeader>
                <CardTitle className="text-base">
                  {tasting.overall ? `${tasting.overall}/10 overall` : "Tasting"}
                </CardTitle>
                <CardDescription>
                  {tasting.author.username} · {formatDateTime(tasting.tasted_at)}
                </CardDescription>
                <CardAction>
                  <RowActions
                    canEdit={canEdit(tasting, user)}
                    onEdit={() => {
                      setEditingTasting(tasting)
                      setTastingDialogOpen(true)
                    }}
                    onDelete={() => setDeletingTasting(tasting)}
                  />
                </CardAction>
              </CardHeader>
              <CardContent className="grid gap-3">
                <div className="grid gap-1.5">
                  {TASTING_SCORES.filter((score) => tasting[score] !== null).map((score) => (
                    <div key={score} className="flex items-center gap-2 text-sm">
                      <span className="w-24 shrink-0 text-muted-foreground">
                        {humanize(score)}
                      </span>
                      <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-muted">
                        <div
                          className="h-full rounded-full bg-primary"
                          style={{ width: `${(tasting[score] ?? 0) * 10}%` }}
                        />
                      </div>
                      <span className="w-6 text-right tabular-nums">{tasting[score]}</span>
                    </div>
                  ))}
                </div>

                {tasting.descriptors && tasting.descriptors.length > 0 ? (
                  <div className="flex flex-wrap gap-1">
                    {tasting.descriptors.map((descriptor) => (
                      <Badge key={descriptor} variant="secondary">
                        {descriptor}
                      </Badge>
                    ))}
                  </div>
                ) : null}

                {tasting.notes ? (
                  <p className="whitespace-pre-wrap text-sm text-muted-foreground">
                    {tasting.notes}
                  </p>
                ) : null}
              </CardContent>
            </Card>
          ))}
        </div>
      ) : (
        <div className="rounded-lg border border-dashed p-8 text-center text-sm text-muted-foreground">
          Nobody has tasted this brew yet.
        </div>
      )}

      <BrewDialog open={brewDialogOpen} onOpenChange={setBrewDialogOpen} brew={brew} />
      <TastingDialog
        open={tastingDialogOpen}
        onOpenChange={setTastingDialogOpen}
        brewId={id}
        tasting={editingTasting}
      />
      <DeleteAlert
        open={deletingTasting !== null}
        onOpenChange={(open) => !open && setDeletingTasting(null)}
        description="Delete this tasting?"
        isPending={removeTasting.isPending}
        onConfirm={() => {
          if (deletingTasting) {
            removeTasting.mutate({ path: { tasting_id: deletingTasting.id } })
          }
          setDeletingTasting(null)
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
