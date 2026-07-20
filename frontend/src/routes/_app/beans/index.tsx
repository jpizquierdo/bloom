import {
  beansDeleteBeanMutation,
  beansListBeansOptions,
  roastersListRoastersOptions,
} from "@/client/@tanstack/react-query.gen"
import type { BeanRead } from "@/client/types.gen"
import { BeanDialog } from "@/components/beans/bean-dialog"
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
import { Input } from "@/components/ui/input"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Skeleton } from "@/components/ui/skeleton"
import { StarRating } from "@/components/ui/star-rating"
import { canEdit, useCurrentUser } from "@/lib/auth"
import { humanize } from "@/lib/format"
import { useCrudFeedback } from "@/lib/mutations"
import { useMutation, useQuery } from "@tanstack/react-query"
import { Link, createFileRoute } from "@tanstack/react-router"
import { Plus, X } from "lucide-react"
import { useState } from "react"

export const Route = createFileRoute("/_app/beans/")({ component: BeansPage })

function BeansPage() {
  const { user } = useCurrentUser()
  const feedback = useCrudFeedback()
  const { data, isLoading } = useQuery(beansListBeansOptions())
  const { data: roasters } = useQuery(roastersListRoastersOptions())

  const [editing, setEditing] = useState<BeanRead | null>(null)
  const [dialogOpen, setDialogOpen] = useState(false)
  const [deleting, setDeleting] = useState<BeanRead | null>(null)
  const [roasterFilter, setRoasterFilter] = useState("all")
  const [search, setSearch] = useState("")

  const query = search.trim().toLowerCase()
  const filtered = (data ?? [])
    .filter((bean) => roasterFilter === "all" || String(bean.roaster.id) === roasterFilter)
    .filter(
      (bean) =>
        query === "" ||
        bean.name.toLowerCase().includes(query) ||
        bean.roaster.name.toLowerCase().includes(query),
    )
    .sort((a, b) => a.name.localeCompare(b.name))

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

      <div className="flex flex-wrap items-center gap-2">
        <Input
          placeholder="Search beans…"
          value={search}
          onChange={(event) => setSearch(event.target.value)}
          className="w-full sm:w-64"
        />
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
      </div>

      {isLoading ? (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 3 }, (_, i) => (
            <Skeleton key={i} className="h-40 w-full" />
          ))}
        </div>
      ) : filtered.length === 0 ? (
        <div className="rounded-lg border border-dashed p-8 text-center text-sm text-muted-foreground">
          No beans yet. Add the coffee you are drinking.
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {filtered.map((bean) => (
            <Card key={bean.id}>
              <CardHeader>
                <CardTitle className="text-base">
                  <Link
                    to="/beans/$beanId"
                    params={{ beanId: String(bean.id) }}
                    className="hover:underline"
                  >
                    {bean.name}
                  </Link>
                </CardTitle>
                <CardDescription>
                  {bean.roaster.name} · {bean.owner.username}
                </CardDescription>
                <CardAction>
                  <RowActions
                    canEdit={canEdit(bean, user)}
                    onEdit={() => openEdit(bean)}
                    onDelete={() => setDeleting(bean)}
                  />
                </CardAction>
              </CardHeader>
              <CardContent className="grid gap-2">
                <div className="flex items-center justify-between gap-2 text-sm text-muted-foreground">
                  <span>{bean.origin_country ?? "—"}</span>
                  {bean.roast_type !== "unknown" ? (
                    <Badge variant="secondary">{humanize(bean.roast_type)}</Badge>
                  ) : null}
                </div>
                {(bean.rating ?? 0) > 0 ? (
                  <StarRating value={bean.rating ?? 0} readOnly size={16} />
                ) : null}
              </CardContent>
            </Card>
          ))}
        </div>
      )}

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
