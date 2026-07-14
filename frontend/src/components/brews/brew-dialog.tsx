import {
  beansListBeansOptions,
  brewMethodsListBrewMethodsOptions,
  brewsCreateBrewMutation,
  brewsUpdateBrewMutation,
  equipmentListEquipmentOptions,
} from "@/client/@tanstack/react-query.gen"
import type { BrewRead } from "@/client/types.gen"
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Textarea } from "@/components/ui/textarea"
import { beanLabel } from "@/lib/domain"
import { stripEmpty, toDateTimeLocal } from "@/lib/format"
import { submitAndClose, useCrudFeedback } from "@/lib/mutations"
import { zodResolver } from "@hookform/resolvers/zod"
import { useMutation, useQuery } from "@tanstack/react-query"
import { useEffect } from "react"
import { useForm } from "react-hook-form"
import { z } from "zod"

const schema = z.object({
  bean_id: z.string().min(1, "Pick a bean"),
  method_id: z.string().min(1, "Pick a method"),
  grinder_id: z.string(),
  dose_grams: z.string().min(1, "Dose is required"),
  yield_grams: z.string(),
  water_grams: z.string(),
  grind_setting: z.string(),
  water_temp_celsius: z.string(),
  brew_time_seconds: z.string(),
  tds_percent: z.string(),
  extraction_yield_percent: z.string(),
  brewed_at: z.string(),
  notes: z.string(),
})

type FormValues = z.infer<typeof schema>

const EMPTY: FormValues = {
  bean_id: "",
  method_id: "",
  grinder_id: "",
  dose_grams: "",
  yield_grams: "",
  water_grams: "",
  grind_setting: "",
  water_temp_celsius: "",
  brew_time_seconds: "",
  tds_percent: "",
  extraction_yield_percent: "",
  brewed_at: "",
  notes: "",
}

interface BrewDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  /** null = create. The bean and the method cannot be changed after the fact. */
  brew: BrewRead | null
  /** Preselect a bean when brewing straight from a bean row. */
  defaultBeanId?: number
}

export function BrewDialog({ open, onOpenChange, brew, defaultBeanId }: BrewDialogProps) {
  const feedback = useCrudFeedback()
  const { data: beans } = useQuery(beansListBeansOptions())
  const { data: methods } = useQuery(brewMethodsListBrewMethodsOptions())
  const { data: equipment } = useQuery(equipmentListEquipmentOptions())
  const grinders = (equipment ?? []).filter((item) => item.type === "grinder")

  const form = useForm<FormValues>({ resolver: zodResolver(schema), defaultValues: EMPTY })

  useEffect(() => {
    if (!open) return
    form.reset(
      brew
        ? {
            bean_id: String(brew.bean_id),
            method_id: String(brew.method_id),
            grinder_id: brew.grinder_id ? String(brew.grinder_id) : "",
            dose_grams: brew.dose_grams,
            yield_grams: brew.yield_grams ?? "",
            water_grams: brew.water_grams ?? "",
            grind_setting: brew.grind_setting ?? "",
            water_temp_celsius: brew.water_temp_celsius ?? "",
            brew_time_seconds: brew.brew_time_seconds?.toString() ?? "",
            tds_percent: brew.tds_percent ?? "",
            extraction_yield_percent: brew.extraction_yield_percent ?? "",
            brewed_at: toDateTimeLocal(brew.brewed_at),
            notes: brew.notes ?? "",
          }
        : { ...EMPTY, bean_id: defaultBeanId ? String(defaultBeanId) : "" },
    )
  }, [open, brew, defaultBeanId, form])

  const create = useMutation({
    ...brewsCreateBrewMutation(),
    onSuccess: feedback.onSuccess("Brew logged"),
    onError: feedback.onError,
  })
  const update = useMutation({
    ...brewsUpdateBrewMutation(),
    onSuccess: feedback.onSuccess("Brew updated"),
    onError: feedback.onError,
  })

  function onSubmit(values: FormValues) {
    const measures = stripEmpty({
      grinder_id: values.grinder_id === "" ? undefined : Number(values.grinder_id),
      yield_grams: values.yield_grams === "" ? undefined : Number(values.yield_grams),
      water_grams: values.water_grams === "" ? undefined : Number(values.water_grams),
      water_temp_celsius:
        values.water_temp_celsius === "" ? undefined : Number(values.water_temp_celsius),
      brew_time_seconds:
        values.brew_time_seconds === "" ? undefined : Number(values.brew_time_seconds),
      tds_percent: values.tds_percent === "" ? undefined : Number(values.tds_percent),
      extraction_yield_percent:
        values.extraction_yield_percent === ""
          ? undefined
          : Number(values.extraction_yield_percent),
      brewed_at: values.brewed_at === "" ? undefined : new Date(values.brewed_at).toISOString(),
      grind_setting: values.grind_setting,
      notes: values.notes,
    })

    const request = brew
      ? update.mutateAsync({
          path: { brew_id: brew.id },
          body: { ...measures, dose_grams: Number(values.dose_grams) },
        })
      : create.mutateAsync({
          body: {
            ...measures,
            bean_id: Number(values.bean_id),
            method_id: Number(values.method_id),
            dose_grams: Number(values.dose_grams),
          },
        })
    return submitAndClose(request, () => onOpenChange(false))
  }

  return (
    <ResourceDialog
      open={open}
      onOpenChange={onOpenChange}
      title={brew ? "Edit brew" : "Log a brew"}
      description="Dose is the only required measure; fill in what you actually recorded."
      form={form}
      onSubmit={onSubmit}
      isPending={create.isPending || update.isPending}
      submitLabel={brew ? "Save" : "Log brew"}
      wide
    >
      <FormField
        control={form.control}
        name="bean_id"
        render={({ field }) => (
          <FormItem>
            <FormLabel>Bean</FormLabel>
            <Select value={field.value} onValueChange={field.onChange} disabled={brew !== null}>
              <FormControl>
                <SelectTrigger className="w-full">
                  <SelectValue placeholder="Select a bean" />
                </SelectTrigger>
              </FormControl>
              <SelectContent>
                {(beans ?? []).map((bean) => (
                  <SelectItem key={bean.id} value={String(bean.id)}>
                    {beanLabel(bean)}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            {brew ? <FormDescription>The bean cannot be changed.</FormDescription> : null}
            <FormMessage />
          </FormItem>
        )}
      />
      <FormField
        control={form.control}
        name="method_id"
        render={({ field }) => (
          <FormItem>
            <FormLabel>Method</FormLabel>
            <Select value={field.value} onValueChange={field.onChange} disabled={brew !== null}>
              <FormControl>
                <SelectTrigger className="w-full">
                  <SelectValue placeholder="Select a method" />
                </SelectTrigger>
              </FormControl>
              <SelectContent>
                {(methods ?? []).map((method) => (
                  <SelectItem key={method.id} value={String(method.id)}>
                    {method.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            {brew ? <FormDescription>The method cannot be changed.</FormDescription> : null}
            <FormMessage />
          </FormItem>
        )}
      />
      <FormField
        control={form.control}
        name="dose_grams"
        render={({ field }) => (
          <FormItem>
            <FormLabel>Dose (g)</FormLabel>
            <FormControl>
              <Input type="number" min={0} step="0.1" placeholder="18.0" {...field} />
            </FormControl>
            <FormMessage />
          </FormItem>
        )}
      />
      <FormField
        control={form.control}
        name="yield_grams"
        render={({ field }) => (
          <FormItem>
            <FormLabel>Yield (g)</FormLabel>
            <FormControl>
              <Input type="number" min={0} step="0.1" placeholder="36.0" {...field} />
            </FormControl>
            <FormDescription>Beverage in the cup.</FormDescription>
            <FormMessage />
          </FormItem>
        )}
      />
      <FormField
        control={form.control}
        name="water_grams"
        render={({ field }) => (
          <FormItem>
            <FormLabel>Water (g)</FormLabel>
            <FormControl>
              <Input type="number" min={0} step="0.1" placeholder="300" {...field} />
            </FormControl>
            <FormDescription>Filter and immersion brews.</FormDescription>
            <FormMessage />
          </FormItem>
        )}
      />
      <FormField
        control={form.control}
        name="grinder_id"
        render={({ field }) => (
          <FormItem>
            <FormLabel>Grinder</FormLabel>
            <Select value={field.value} onValueChange={field.onChange}>
              <FormControl>
                <SelectTrigger className="w-full">
                  <SelectValue placeholder="Select a grinder" />
                </SelectTrigger>
              </FormControl>
              <SelectContent>
                {grinders.map((grinder) => (
                  <SelectItem key={grinder.id} value={String(grinder.id)}>
                    {grinder.name}
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
        name="grind_setting"
        render={({ field }) => (
          <FormItem>
            <FormLabel>Grind setting</FormLabel>
            <FormControl>
              <Input placeholder="2.5" {...field} />
            </FormControl>
            <FormMessage />
          </FormItem>
        )}
      />
      <FormField
        control={form.control}
        name="water_temp_celsius"
        render={({ field }) => (
          <FormItem>
            <FormLabel>Water temp (°C)</FormLabel>
            <FormControl>
              <Input type="number" step="0.1" placeholder="93.0" {...field} />
            </FormControl>
            <FormMessage />
          </FormItem>
        )}
      />
      <FormField
        control={form.control}
        name="brew_time_seconds"
        render={({ field }) => (
          <FormItem>
            <FormLabel>Brew time (s)</FormLabel>
            <FormControl>
              <Input type="number" min={0} placeholder="28" {...field} />
            </FormControl>
            <FormMessage />
          </FormItem>
        )}
      />
      <FormField
        control={form.control}
        name="tds_percent"
        render={({ field }) => (
          <FormItem>
            <FormLabel>TDS (%)</FormLabel>
            <FormControl>
              <Input type="number" step="0.01" placeholder="1.35" {...field} />
            </FormControl>
            <FormDescription>From the refractometer.</FormDescription>
            <FormMessage />
          </FormItem>
        )}
      />
      <FormField
        control={form.control}
        name="extraction_yield_percent"
        render={({ field }) => (
          <FormItem>
            <FormLabel>Extraction yield (%)</FormLabel>
            <FormControl>
              <Input type="number" step="0.01" placeholder="20.5" {...field} />
            </FormControl>
            <FormMessage />
          </FormItem>
        )}
      />
      <FormField
        control={form.control}
        name="brewed_at"
        render={({ field }) => (
          <FormItem>
            <FormLabel>Brewed at</FormLabel>
            <FormControl>
              <Input type="datetime-local" {...field} />
            </FormControl>
            <FormDescription>Defaults to now.</FormDescription>
            <FormMessage />
          </FormItem>
        )}
      />
      <FormField
        control={form.control}
        name="notes"
        render={({ field }) => (
          <FormItem className="sm:col-span-2">
            <FormLabel>Notes</FormLabel>
            <FormControl>
              <Textarea rows={3} placeholder="Bloomed 45 s, gentle pours." {...field} />
            </FormControl>
            <FormMessage />
          </FormItem>
        )}
      />
    </ResourceDialog>
  )
}
