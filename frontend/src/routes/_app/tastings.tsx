import {
  beansListBeansOptions,
  brewMethodsListBrewMethodsOptions,
  brewsListBrewsOptions,
  tastingsDeleteTastingMutation,
  tastingsListAllTastingsOptions,
} from "@/client/@tanstack/react-query.gen"
import type { TastingRead } from "@/client/types.gen"
import { TastingDialog } from "@/components/brews/tasting-dialog"
import { DeleteAlert } from "@/components/data/delete-alert"
import { PageHeader } from "@/components/data/page-header"
import { RowActions } from "@/components/data/row-actions"
import { Badge } from "@/components/ui/badge"
import {
  Card,
  CardAction,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Checkbox } from "@/components/ui/checkbox"
import { Skeleton } from "@/components/ui/skeleton"
import { StarRating } from "@/components/ui/star-rating"
import { canEdit, useCurrentUser } from "@/lib/auth"
import { TASTING_SCORES } from "@/lib/domain"
import { formatDateTime, humanize } from "@/lib/format"
import { useCrudFeedback } from "@/lib/mutations"
import { useMutation, useQuery } from "@tanstack/react-query"
import { Link, createFileRoute } from "@tanstack/react-router"
import { useState } from "react"

export const Route = createFileRoute("/_app/tastings")({ component: TastingsPage })

function TastingsPage() {
  const { user } = useCurrentUser()
  const feedback = useCrudFeedback()

  const [showEveryone, setShowEveryone] = useState(false)
  const [editing, setEditing] = useState<TastingRead | null>(null)
  const [dialogOpen, setDialogOpen] = useState(false)
  const [deleting, setDeleting] = useState<TastingRead | null>(null)

  // mine=true returns only my tastings; without it the whole shared log comes back.
  const { data: tastings, isLoading } = useQuery(
    tastingsListAllTastingsOptions({ query: { mine: !showEveryone } }),
  )
  // A tasting only carries its brew_id, so join client-side (like the dashboard does) to
  // name the coffee and method behind each one.
  const { data: brews } = useQuery(brewsListBrewsOptions())
  const { data: beans } = useQuery(beansListBeansOptions())
  const { data: methods } = useQuery(brewMethodsListBrewMethodsOptions())

  const remove = useMutation({
    ...tastingsDeleteTastingMutation(),
    onSuccess: feedback.onSuccess("Tasting deleted"),
    onError: feedback.onError,
  })

  const sorted = [...(tastings ?? [])].sort((a, b) =>
    (b.tasted_at ?? "").localeCompare(a.tasted_at ?? ""),
  )

  const brewOf = (id: number) => brews?.find((brew) => brew.id === id)
  const beanName = (beanId: number) => beans?.find((bean) => bean.id === beanId)?.name
  const roasterName = (beanId: number) => beans?.find((bean) => bean.id === beanId)?.roaster.name
  const methodName = (methodId: number) => methods?.find((method) => method.id === methodId)?.name

  return (
    <>
      <PageHeader
        title="Tastings"
        description={
          showEveryone ? "Every tasting in the shared log." : "The cups you have scored."
        }
        actions={
          <label className="flex cursor-pointer items-center gap-2 text-sm select-none">
            <Checkbox
              checked={showEveryone}
              onCheckedChange={(checked) => setShowEveryone(checked === true)}
            />
            Show everyone's
          </label>
        }
      />

      {isLoading ? (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 3 }, (_, i) => (
            <Skeleton key={i} className="h-56 w-full" />
          ))}
        </div>
      ) : sorted.length === 0 ? (
        <div className="rounded-lg border border-dashed p-8 text-center text-sm text-muted-foreground">
          {showEveryone
            ? "No tastings yet. Score a brew from its page."
            : "You haven't scored any brews yet. Open a brew and add a tasting."}
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {sorted.map((tasting) => {
            const brew = brewOf(tasting.brew_id)
            const scored = TASTING_SCORES.filter((score) => tasting[score] !== null)
            return (
              <Card key={tasting.id}>
                <CardHeader>
                  <CardTitle className="text-base">
                    {brew ? (
                      <Link
                        to="/brews/$brewId"
                        params={{ brewId: String(brew.id) }}
                        className="hover:underline"
                      >
                        {beanName(brew.bean_id) ?? "Coffee"}
                      </Link>
                    ) : (
                      (beanName(tasting.brew_id) ?? "Tasting")
                    )}
                  </CardTitle>
                  <CardDescription>
                    {brew ? (
                      <>
                        {roasterName(brew.bean_id) ? `${roasterName(brew.bean_id)} · ` : ""}
                        {methodName(brew.method_id) ?? "—"} ·{" "}
                      </>
                    ) : null}
                    {formatDateTime(tasting.tasted_at)} · {tasting.author.username}
                  </CardDescription>
                  <CardAction>
                    <RowActions
                      canEdit={canEdit(tasting, user)}
                      onEdit={() => {
                        setEditing(tasting)
                        setDialogOpen(true)
                      }}
                      onDelete={() => setDeleting(tasting)}
                    />
                  </CardAction>
                </CardHeader>
                <CardContent className="grid gap-3">
                  {scored.length > 0 ? (
                    <div className="grid gap-1.5">
                      {scored.map((score) => (
                        <div key={score} className="flex items-center gap-2 text-sm">
                          <span className="w-24 shrink-0 text-muted-foreground">
                            {humanize(score)}
                          </span>
                          <StarRating value={tasting[score] ?? 0} readOnly size={16} />
                        </div>
                      ))}
                    </div>
                  ) : null}

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
            )
          })}
        </div>
      )}

      {editing ? (
        <TastingDialog
          open={dialogOpen}
          onOpenChange={setDialogOpen}
          brewId={editing.brew_id}
          tasting={editing}
        />
      ) : null}
      <DeleteAlert
        open={deleting !== null}
        onOpenChange={(open) => !open && setDeleting(null)}
        description="Delete this tasting? This cannot be undone."
        isPending={remove.isPending}
        onConfirm={() => {
          if (deleting) remove.mutate({ path: { tasting_id: deleting.id } })
          setDeleting(null)
        }}
      />
    </>
  )
}
