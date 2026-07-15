import {
  brewMethodsCreateBrewMethodMutation,
  brewMethodsListBrewMethodsOptions,
} from "@/client/@tanstack/react-query.gen"
import type { BrewMethodRead } from "@/client/types.gen"
import { DataTable } from "@/components/data/data-table"
import { PageHeader } from "@/components/data/page-header"
import { ResourceDialog } from "@/components/data/resource-dialog"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form"
import { Input } from "@/components/ui/input"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { isAdmin, useCurrentUser } from "@/lib/auth"
import { BREW_CATEGORIES } from "@/lib/domain"
import { formatNumber, humanize, stripEmpty } from "@/lib/format"
import { submitAndClose, useCrudFeedback } from "@/lib/mutations"
import { zodResolver } from "@hookform/resolvers/zod"
import { useMutation, useQuery } from "@tanstack/react-query"
import { createFileRoute } from "@tanstack/react-router"
import type { ColumnDef } from "@tanstack/react-table"
import { Plus } from "lucide-react"
import { useState } from "react"
import { useForm } from "react-hook-form"
import { z } from "zod"

export const Route = createFileRoute("/_app/brew-methods")({ component: BrewMethodsPage })

const schema = z.object({
  name: z.string().min(1, "Name is required"),
  category: z.enum(BREW_CATEGORIES, "Pick a category"),
  default_ratio: z.string(),
})

type FormValues = z.infer<typeof schema>

function BrewMethodsPage() {
  const { user } = useCurrentUser()
  const feedback = useCrudFeedback()
  const { data, isLoading } = useQuery(brewMethodsListBrewMethodsOptions())
  const [dialogOpen, setDialogOpen] = useState(false)

  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { name: "", category: "filter", default_ratio: "" },
  })

  const create = useMutation({
    ...brewMethodsCreateBrewMethodMutation(),
    onSuccess: feedback.onSuccess("Brew method created"),
    onError: feedback.onError,
  })

  function onSubmit(values: FormValues) {
    const request = create.mutateAsync({
      body: {
        name: values.name,
        category: values.category,
        ...stripEmpty({
          default_ratio:
            values.default_ratio === "" ? undefined : Number(values.default_ratio),
        }),
      },
    })
    return submitAndClose(request, () => setDialogOpen(false))
  }

  const columns: ColumnDef<BrewMethodRead, unknown>[] = [
    { accessorKey: "name", header: "Name" },
    {
      accessorKey: "category",
      header: "Category",
      cell: ({ row }) => <Badge variant="secondary">{humanize(row.original.category)}</Badge>,
    },
    {
      accessorKey: "default_ratio",
      header: "Default ratio",
      cell: ({ row }) =>
        row.original.default_ratio ? `1:${formatNumber(row.original.default_ratio, 1)}` : "—",
    },
  ]

  return (
    <>
      <PageHeader
        title="Brew methods"
        description="The shared catalogue of methods. Admins keep it tidy."
        actions={
          isAdmin(user) ? (
            <Button
              onClick={() => {
                form.reset({ name: "", category: "filter", default_ratio: "" })
                setDialogOpen(true)
              }}
            >
              <Plus className="size-4" />
              New method
            </Button>
          ) : null
        }
      />

      <DataTable
        columns={columns}
        data={data}
        isLoading={isLoading}
        searchPlaceholder="Search methods…"
        emptyMessage="No methods yet. An admin can add V60, Espresso, AeroPress…"
      />

      <ResourceDialog
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        title="New brew method"
        form={form}
        onSubmit={onSubmit}
        isPending={create.isPending}
      >
        <FormField
          control={form.control}
          name="name"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Name</FormLabel>
              <FormControl>
                <Input placeholder="V60" {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        <FormField
          control={form.control}
          name="category"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Category</FormLabel>
              <Select value={field.value} onValueChange={field.onChange}>
                <FormControl>
                  <SelectTrigger className="w-full">
                    <SelectValue />
                  </SelectTrigger>
                </FormControl>
                <SelectContent>
                  {BREW_CATEGORIES.map((category) => (
                    <SelectItem key={category} value={category}>
                      {humanize(category)}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <FormMessage />
            </FormItem>
          )}
        />
        <FormField
          control={form.control}
          name="default_ratio"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Default ratio</FormLabel>
              <FormControl>
                <Input type="number" step="0.01" min={0} placeholder="16.00" {...field} />
              </FormControl>
              <FormDescription>Water per gram of coffee, e.g. 16 for 1:16.</FormDescription>
              <FormMessage />
            </FormItem>
          )}
        />
      </ResourceDialog>
    </>
  )
}
