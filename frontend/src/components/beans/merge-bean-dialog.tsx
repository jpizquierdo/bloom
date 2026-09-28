import {
  beansListBeansOptions,
  beansMergeBeanMutation,
} from "@/client/@tanstack/react-query.gen"
import type { BeanRead } from "@/client/types.gen"
import { Combobox } from "@/components/data/combobox"
import { ResourceDialog } from "@/components/data/resource-dialog"
import {
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form"
import { canEdit, useCurrentUser } from "@/lib/auth"
import { beanLabel } from "@/lib/domain"
import { submitAndClose, useCrudFeedback } from "@/lib/mutations"
import { zodResolver } from "@hookform/resolvers/zod"
import { useMutation, useQuery } from "@tanstack/react-query"
import { useEffect } from "react"
import { useForm } from "react-hook-form"
import { z } from "zod"

const schema = z.object({
  source_id: z.string().min(1, "Pick the duplicate to merge"),
})

type FormValues = z.infer<typeof schema>

interface MergeBeanDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  /** The bean that stays: the duplicate is folded into it. */
  bean: BeanRead
}

export function MergeBeanDialog({ open, onOpenChange, bean }: MergeBeanDialogProps) {
  const feedback = useCrudFeedback()
  const { user } = useCurrentUser()
  const { data: beans } = useQuery(beansListBeansOptions())
  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { source_id: "" },
  })

  useEffect(() => {
    if (open) form.reset({ source_id: "" })
  }, [open, form])

  const merge = useMutation({
    ...beansMergeBeanMutation(),
    onSuccess: feedback.onSuccess("Beans merged"),
    onError: feedback.onError,
  })

  // Merging deletes the duplicate, so the API only accepts beans the user may edit.
  const candidates = (beans ?? []).filter((row) => row.id !== bean.id && canEdit(row, user))

  function onSubmit(values: FormValues) {
    const request = merge.mutateAsync({
      path: { bean_id: bean.id },
      body: { source_id: Number(values.source_id) },
    })
    return submitAndClose(request, () => onOpenChange(false))
  }

  return (
    <ResourceDialog
      open={open}
      onOpenChange={onOpenChange}
      title="Merge a duplicate"
      description={`Pick the duplicate of "${bean.name}". All of its lots, recipes and brews move here, including entries from other users, then it is deleted.`}
      form={form}
      onSubmit={onSubmit}
      isPending={merge.isPending}
      submitLabel="Merge"
    >
      <FormField
        control={form.control}
        name="source_id"
        render={({ field }) => (
          <FormItem>
            <FormLabel>Duplicate to merge away</FormLabel>
            <FormControl>
              <Combobox
                value={field.value}
                onChange={field.onChange}
                options={candidates.map((candidate) => ({
                  value: String(candidate.id),
                  label: beanLabel(candidate),
                }))}
                placeholder="Select a bean"
                searchPlaceholder="Search beans…"
                emptyMessage="No bean you can edit."
              />
            </FormControl>
            <FormDescription>
              This bean keeps its own details and adopts the duplicate's for anything it left
              empty. Only beans you can edit are listed.
            </FormDescription>
            <FormMessage />
          </FormItem>
        )}
      />
    </ResourceDialog>
  )
}
