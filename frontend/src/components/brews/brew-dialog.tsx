import {
  beansListBeansOptions,
  brewMethodsListBrewMethodsOptions,
  brewsCreateBrewMutation,
  brewsUpdateBrewMutation,
  equipmentListEquipmentOptions,
  lotsListLotsOptions,
} from "@/client/@tanstack/react-query.gen"
import type { BeanLotRead, BrewRead } from "@/client/types.gen"
import { Combobox } from "@/components/data/combobox"
import { ResourceDialog } from "@/components/data/resource-dialog"
import { Checkbox } from "@/components/ui/checkbox"
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
import { patchBody, stripEmpty, toDateTimeLocal } from "@/lib/format"
import { submitAndClose, useCrudFeedback } from "@/lib/mutations"
import { zodResolver } from "@hookform/resolvers/zod"
import { useMutation, useQuery } from "@tanstack/react-query"
import { useEffect, useRef, useState } from "react"
import { useForm } from "react-hook-form"
import { z } from "zod"

const schema = z.object({
  bean_id: z.string().min(1, "Pick a bean"),
  lot_id: z.string(),
  method_id: z.string().min(1, "Pick a method"),
  grinder_id: z.string(),
  dose_grams: z.string().min(1, "Dose is required"),
  yield_grams: z.string(),
  water_grams: z.string(),
  grind_setting: z.string(),
  water_temp_celsius: z.string(),
  brew_time_seconds: z.string(),
  tds_percent: z.string(),
  brewed_at: z.string(),
  notes: z.string(),
})

type FormValues = z.infer<typeof schema>

// Nullable columns: on edit, clearing one sends an explicit null (see patchBody). brewed_at is
// NOT NULL (server default now()), so it is omitted when blank, never nulled.
const CLEARABLE = [
  "lot_id",
  "grinder_id",
  "yield_grams",
  "water_grams",
  "grind_setting",
  "water_temp_celsius",
  "brew_time_seconds",
  "tds_percent",
  "notes",
] as const

const EMPTY: FormValues = {
  bean_id: "",
  lot_id: "",
  method_id: "",
  grinder_id: "",
  dose_grams: "",
  yield_grams: "",
  water_grams: "",
  grind_setting: "",
  water_temp_celsius: "",
  brew_time_seconds: "",
  tds_percent: "",
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
  /** Seed a create ("brew again") from an existing brew, minus brewed_at and TDS. */
  prefillFrom?: BrewRead
}

export function BrewDialog({
  open,
  onOpenChange,
  brew,
  defaultBeanId,
  prefillFrom,
}: BrewDialogProps) {
  const feedback = useCrudFeedback()
  const { data: beans } = useQuery(beansListBeansOptions())
  const { data: methods } = useQuery(brewMethodsListBrewMethodsOptions())
  const { data: equipment } = useQuery(equipmentListEquipmentOptions())
  const grinders = (equipment ?? []).filter((item) => item.type === "grinder")

  const form = useForm<FormValues>({ resolver: zodResolver(schema), defaultValues: EMPTY })

  // The lot picker offers the selected bean's lots (a brew's lot must belong to its bean).
  const beanId = form.watch("bean_id")
  const { data: lots } = useQuery({
    ...lotsListLotsOptions({ path: { bean_id: Number(beanId) } }),
    enabled: beanId !== "",
  })
  const [showFinished, setShowFinished] = useState(false)
  // The bean we've already defaulted the lot for, so a manual choice is not overridden.
  const autoLotBeanRef = useRef<string | null>(null)

  useEffect(() => {
    if (!open) return
    // "Brew again": reuse an existing brew's recipe, but brewed_at and TDS start blank
    // (brewed_at defaults to now on create; TDS is always a fresh refractometer reading).
    const source = brew ?? prefillFrom
    form.reset(
      source
        ? {
            bean_id: String(source.bean_id),
            lot_id: source.lot_id ? String(source.lot_id) : "",
            method_id: String(source.method_id),
            grinder_id: source.grinder_id ? String(source.grinder_id) : "",
            dose_grams: source.dose_grams,
            yield_grams: source.yield_grams ?? "",
            water_grams: source.water_grams ?? "",
            grind_setting: source.grind_setting ?? "",
            water_temp_celsius: source.water_temp_celsius ?? "",
            brew_time_seconds: source.brew_time_seconds?.toString() ?? "",
            tds_percent: brew ? (source.tds_percent ?? "") : "",
            brewed_at: brew ? toDateTimeLocal(source.brewed_at) : "",
            notes: source.notes ?? "",
          }
        : { ...EMPTY, bean_id: defaultBeanId ? String(defaultBeanId) : "" },
    )
  }, [open, brew, prefillFrom, defaultBeanId, form])

  // Fresh dialog: hide finished lots. Allow auto-lot again on a blank create, but not when
  // prefilling — keep the copied lot for the source's bean (re-enabled if the bean changes).
  useEffect(() => {
    if (open) {
      setShowFinished(false)
      autoLotBeanRef.current = prefillFrom ? String(prefillFrom.bean_id) : null
    }
  }, [open, prefillFrom])

  // On create, default the lot to the bean's most recent OPEN lot (once per bean). This also
  // clears a stale lot when the bean changes; editing keeps the brew's own lot untouched.
  useEffect(() => {
    if (!open || brew || beanId === "" || !lots) return
    if (autoLotBeanRef.current === beanId) return
    autoLotBeanRef.current = beanId
    const mostRecentOpen = lots.find((lot) => !lot.is_finished)
    form.setValue("lot_id", mostRecentOpen ? String(mostRecentOpen.id) : "")
  }, [open, brew, beanId, lots, form])

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
    const measures = {
      lot_id: values.lot_id === "" ? undefined : Number(values.lot_id),
      grinder_id: values.grinder_id === "" ? undefined : Number(values.grinder_id),
      yield_grams: values.yield_grams === "" ? undefined : Number(values.yield_grams),
      water_grams: values.water_grams === "" ? undefined : Number(values.water_grams),
      water_temp_celsius:
        values.water_temp_celsius === "" ? undefined : Number(values.water_temp_celsius),
      brew_time_seconds:
        values.brew_time_seconds === "" ? undefined : Number(values.brew_time_seconds),
      tds_percent: values.tds_percent === "" ? undefined : Number(values.tds_percent),
      brewed_at: values.brewed_at === "" ? undefined : new Date(values.brewed_at).toISOString(),
      grind_setting: values.grind_setting,
      notes: values.notes,
    }

    const request = brew
      ? update.mutateAsync({
          path: { brew_id: brew.id },
          body: { ...patchBody(measures, CLEARABLE), dose_grams: Number(values.dose_grams) },
        })
      : create.mutateAsync({
          body: {
            ...stripEmpty(measures),
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
      title={brew ? "Edit brew" : prefillFrom ? "Brew again" : "Log a brew"}
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
            <FormControl>
              <Combobox
                value={field.value}
                onChange={field.onChange}
                options={(beans ?? []).map((bean) => ({
                  value: String(bean.id),
                  label: beanLabel(bean),
                }))}
                placeholder="Select a bean"
                searchPlaceholder="Search beans…"
                disabled={brew !== null}
              />
            </FormControl>
            {brew ? <FormDescription>The bean cannot be changed.</FormDescription> : null}
            <FormMessage />
          </FormItem>
        )}
      />
      {beanId !== "" && (lots?.length ?? 0) > 0 ? (
        <FormField
          control={form.control}
          name="lot_id"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Lot</FormLabel>
              <Select
                value={field.value === "" ? "none" : field.value}
                onValueChange={(value) => field.onChange(value === "none" ? "" : value)}
              >
                <FormControl>
                  <SelectTrigger className="w-full">
                    <SelectValue />
                  </SelectTrigger>
                </FormControl>
                <SelectContent>
                  <SelectItem value="none">No specific lot</SelectItem>
                  {(lots ?? [])
                    .filter(
                      (lot) =>
                        showFinished || !lot.is_finished || String(lot.id) === field.value,
                    )
                    .map((lot) => (
                      <SelectItem key={lot.id} value={String(lot.id)}>
                        {lotLabel(lot)}
                        {lot.is_finished ? " · finished" : ""}
                      </SelectItem>
                    ))}
                </SelectContent>
              </Select>
              {(lots ?? []).some((lot) => lot.is_finished) ? (
                <label className="flex items-center gap-2 text-sm text-muted-foreground">
                  <Checkbox
                    checked={showFinished}
                    onCheckedChange={(checked) => setShowFinished(checked === true)}
                  />
                  Show finished
                </label>
              ) : null}
              <FormDescription>Which bag this brew came from (optional).</FormDescription>
              <FormMessage />
            </FormItem>
          )}
        />
      ) : null}
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

function lotLabel(lot: BeanLotRead): string {
  const parts = [
    lot.purchase_date ? `Bought ${lot.purchase_date}` : null,
    lot.roast_date ? `roasted ${lot.roast_date}` : null,
    lot.weight_grams ? `${lot.weight_grams} g` : null,
  ].filter(Boolean)
  return parts.length > 0 ? parts.join(" · ") : `Lot #${lot.id}`
}
