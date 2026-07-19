import {
  lotsCreateLotMutation,
  lotsUpdateLotMutation,
} from "@/client/@tanstack/react-query.gen"
import type { BeanLotRead } from "@/client/types.gen"
import { ResourceDialog } from "@/components/data/resource-dialog"
import {
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form"
import { Input } from "@/components/ui/input"
import { Switch } from "@/components/ui/switch"
import { patchBody, stripEmpty, toDateInput } from "@/lib/format"
import { submitAndClose, useCrudFeedback } from "@/lib/mutations"
import { useMutation } from "@tanstack/react-query"
import { useEffect } from "react"
import { useForm } from "react-hook-form"

type FormValues = {
  roast_date: string
  purchase_date: string
  weight_grams: string
  price: string
  is_finished: boolean
}

const EMPTY: FormValues = {
  roast_date: "",
  purchase_date: "",
  weight_grams: "",
  price: "",
  is_finished: false,
}

// Nullable columns: on edit, clearing one sends an explicit null (see patchBody).
const CLEARABLE = ["roast_date", "purchase_date", "weight_grams", "price"] as const

interface LotDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  beanId: number
  lot: BeanLotRead | null
}

export function LotDialog({ open, onOpenChange, beanId, lot }: LotDialogProps) {
  const feedback = useCrudFeedback()
  const form = useForm<FormValues>({ defaultValues: EMPTY })

  useEffect(() => {
    if (!open) return
    form.reset(
      lot
        ? {
            roast_date: toDateInput(lot.roast_date),
            purchase_date: toDateInput(lot.purchase_date),
            weight_grams: lot.weight_grams?.toString() ?? "",
            price: lot.price ?? "",
            is_finished: lot.is_finished,
          }
        : EMPTY,
    )
  }, [open, lot, form])

  const create = useMutation({
    ...lotsCreateLotMutation(),
    onSuccess: feedback.onSuccess("Lot added"),
    onError: feedback.onError,
  })
  const update = useMutation({
    ...lotsUpdateLotMutation(),
    onSuccess: feedback.onSuccess("Lot updated"),
    onError: feedback.onError,
  })

  function onSubmit(values: FormValues) {
    const normalized = {
      roast_date: values.roast_date === "" ? undefined : values.roast_date,
      purchase_date: values.purchase_date === "" ? undefined : values.purchase_date,
      weight_grams: values.weight_grams === "" ? undefined : Number(values.weight_grams),
      price: values.price === "" ? undefined : Number(values.price),
      is_finished: values.is_finished,
    }
    const request = lot
      ? update.mutateAsync({ path: { lot_id: lot.id }, body: patchBody(normalized, CLEARABLE) })
      : create.mutateAsync({ path: { bean_id: beanId }, body: stripEmpty(normalized) })
    return submitAndClose(request, () => onOpenChange(false))
  }

  return (
    <ResourceDialog
      open={open}
      onOpenChange={onOpenChange}
      title={lot ? "Edit lot" : "Add a lot"}
      description="A lot is one bag you bought — its roast/purchase dates, weight and price."
      form={form}
      onSubmit={onSubmit}
      isPending={create.isPending || update.isPending}
    >
      <FormField
        control={form.control}
        name="roast_date"
        render={({ field }) => (
          <FormItem>
            <FormLabel>Roast date</FormLabel>
            <FormControl>
              <Input type="date" {...field} />
            </FormControl>
            <FormMessage />
          </FormItem>
        )}
      />
      <FormField
        control={form.control}
        name="purchase_date"
        render={({ field }) => (
          <FormItem>
            <FormLabel>Purchase date</FormLabel>
            <FormControl>
              <Input type="date" {...field} />
            </FormControl>
            <FormMessage />
          </FormItem>
        )}
      />
      <FormField
        control={form.control}
        name="weight_grams"
        render={({ field }) => (
          <FormItem>
            <FormLabel>Weight (g)</FormLabel>
            <FormControl>
              <Input type="number" min={0} placeholder="250" {...field} />
            </FormControl>
            <FormMessage />
          </FormItem>
        )}
      />
      <FormField
        control={form.control}
        name="price"
        render={({ field }) => (
          <FormItem>
            <FormLabel>Price</FormLabel>
            <FormControl>
              <Input type="number" min={0} step="0.01" placeholder="18.50" {...field} />
            </FormControl>
            <FormMessage />
          </FormItem>
        )}
      />
      <FormField
        control={form.control}
        name="is_finished"
        render={({ field }) => (
          <FormItem className="flex items-center justify-between rounded-lg border p-3">
            <div className="grid gap-0.5">
              <FormLabel>Finished</FormLabel>
              <FormDescription>The bag is empty.</FormDescription>
            </div>
            <FormControl>
              <Switch checked={field.value} onCheckedChange={field.onChange} />
            </FormControl>
          </FormItem>
        )}
      />
    </ResourceDialog>
  )
}
