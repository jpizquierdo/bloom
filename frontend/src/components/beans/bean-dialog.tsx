import {
  beansCreateBeanMutation,
  beansListBeansOptions,
  beansUpdateBeanMutation,
  roastersListRoastersOptions,
} from "@/client/@tanstack/react-query.gen"
import type { BeanRead } from "@/client/types.gen"
import { CreatableCombobox } from "@/components/data/creatable-combobox"
import { ResourceDialog } from "@/components/data/resource-dialog"
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog"
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
import { StarRating } from "@/components/ui/star-rating"
import { Textarea } from "@/components/ui/textarea"
import {
  BLENDS,
  PROCESSES,
  ROAST_LEVELS,
  ROAST_TYPES,
  beanLabel,
  findDuplicateBean,
} from "@/lib/domain"
import { humanize, patchBody, stripEmpty } from "@/lib/format"
import { submitAndClose, useCrudFeedback } from "@/lib/mutations"
import { zodResolver } from "@hookform/resolvers/zod"
import { useMutation, useQuery } from "@tanstack/react-query"
import { useNavigate } from "@tanstack/react-router"
import { useEffect, useState } from "react"
import { useForm } from "react-hook-form"
import { z } from "zod"

// A bean is the coffee concept; per-purchase data (roast/purchase date, price,
// weight, finished) lives on its lots — see the bean detail page.
const schema = z.object({
  name: z.string().min(1, "Name is required"),
  roaster: z.string().min(1, "Roaster is required"),
  origin_country: z.string(),
  region: z.string(),
  producer: z.string(),
  variety: z.string(),
  process: z.enum(PROCESSES).or(z.literal("")),
  roast_level: z.enum(ROAST_LEVELS).or(z.literal("")),
  roast_type: z.enum(ROAST_TYPES),
  blend: z.enum(BLENDS),
  altitude_masl: z.string(),
  tasting_notes_label: z.string(),
  rating: z.number().int().min(0).max(5),
  website: z.string(),
  notes: z.string(),
})

type FormValues = z.infer<typeof schema>

const EMPTY: FormValues = {
  name: "",
  roaster: "",
  origin_country: "",
  region: "",
  producer: "",
  variety: "",
  process: "",
  roast_level: "",
  roast_type: "unknown",
  blend: "single_origin",
  altitude_masl: "",
  tasting_notes_label: "",
  rating: 0,
  website: "",
  notes: "",
}

// Nullable columns: on edit, clearing one sends an explicit null (see patchBody).
const CLEARABLE = [
  "origin_country",
  "region",
  "producer",
  "variety",
  "process",
  "roast_level",
  "altitude_masl",
  "tasting_notes_label",
  "rating",
  "website",
  "notes",
] as const

/** Normalize form strings to API values; "unset" is `undefined` for typed fields, "" for text. */
function normalize(values: FormValues) {
  return {
    name: values.name,
    roaster: values.roaster,
    origin_country: values.origin_country,
    region: values.region,
    producer: values.producer,
    variety: values.variety,
    process: values.process === "" ? undefined : values.process,
    roast_level: values.roast_level === "" ? undefined : values.roast_level,
    roast_type: values.roast_type,
    blend: values.blend,
    altitude_masl: values.altitude_masl === "" ? undefined : Number(values.altitude_masl),
    tasting_notes_label: values.tasting_notes_label,
    rating: values.rating === 0 ? undefined : values.rating, // 0 stars = unrated
    website: values.website,
    notes: values.notes,
  }
}

interface BeanDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  bean: BeanRead | null
}

export function BeanDialog({ open, onOpenChange, bean }: BeanDialogProps) {
  const feedback = useCrudFeedback()
  const navigate = useNavigate()
  const { data: roasters } = useQuery(roastersListRoastersOptions())
  const { data: beans } = useQuery(beansListBeansOptions())
  const form = useForm<FormValues>({ resolver: zodResolver(schema), defaultValues: EMPTY })
  // Values held back while the duplicate warning is up, so confirming re-submits them.
  const [pending, setPending] = useState<FormValues | null>(null)

  const [watchedName, watchedRoaster] = form.watch(["name", "roaster"])
  const duplicate = findDuplicateBean(beans ?? [], {
    name: watchedName,
    roaster: watchedRoaster,
    excludeId: bean?.id,
  })

  useEffect(() => {
    if (!open) return
    form.reset(
      bean
        ? {
            name: bean.name,
            roaster: bean.roaster.name,
            origin_country: bean.origin_country ?? "",
            region: bean.region ?? "",
            producer: bean.producer ?? "",
            variety: bean.variety ?? "",
            process: bean.process ?? "",
            roast_level: bean.roast_level ?? "",
            roast_type: bean.roast_type ?? "unknown",
            blend: bean.blend ?? "single_origin",
            altitude_masl: bean.altitude_masl?.toString() ?? "",
            tasting_notes_label: bean.tasting_notes_label ?? "",
            rating: bean.rating ?? 0,
            website: bean.website ?? "",
            notes: bean.notes ?? "",
          }
        : EMPTY,
    )
  }, [open, bean, form])

  const create = useMutation({
    ...beansCreateBeanMutation(),
    onSuccess: feedback.onSuccess("Bean added"),
    onError: feedback.onError,
  })
  const update = useMutation({
    ...beansUpdateBeanMutation(),
    onSuccess: feedback.onSuccess("Bean updated"),
    onError: feedback.onError,
  })

  function save(values: FormValues, allowDuplicate: boolean) {
    const normalized = normalize(values)
    const query = allowDuplicate ? { allow_duplicate: true } : undefined
    const request = bean
      ? update.mutateAsync({
          path: { bean_id: bean.id },
          query,
          body: patchBody(normalized, CLEARABLE),
        })
      : create.mutateAsync({
          query,
          body: { ...stripEmpty(normalized), name: values.name, roaster: values.roaster },
        })
    return submitAndClose(request, () => onOpenChange(false))
  }

  function onSubmit(values: FormValues) {
    // The API would refuse this with a 409 anyway; asking first turns that into a choice.
    if (duplicate) {
      setPending(values)
      return
    }
    return save(values, false)
  }

  function openDuplicate() {
    if (!duplicate) return
    setPending(null)
    onOpenChange(false)
    navigate({ to: "/beans/$beanId", params: { beanId: String(duplicate.id) } })
  }

  return (
    <>
      <ResourceDialog
        open={open}
        onOpenChange={onOpenChange}
        title={bean ? "Edit bean" : "New bean"}
        description="Only the name and the roaster are required. Add lots (bags) from the bean's page."
        form={form}
        onSubmit={onSubmit}
        isPending={create.isPending || update.isPending}
        wide
      >
        <FormField
          control={form.control}
          name="name"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Name</FormLabel>
              <FormControl>
                <Input placeholder="Kirinyaga AA" {...field} />
              </FormControl>
              {duplicate ? (
                <FormDescription className="text-amber-600 dark:text-amber-500">
                  {beanLabel(duplicate)} is already logged.{" "}
                  <button type="button" onClick={openDuplicate} className="underline">
                    Open it
                  </button>{" "}
                  instead of adding it twice.
                </FormDescription>
              ) : null}
              <FormMessage />
            </FormItem>
          )}
        />
        <FormField
          control={form.control}
          name="roaster"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Roaster</FormLabel>
              <FormControl>
                <CreatableCombobox
                  value={field.value}
                  onChange={field.onChange}
                  options={(roasters ?? []).map((roaster) => roaster.name)}
                  placeholder="Select or type a roaster"
                />
              </FormControl>
              <FormDescription>A roaster you type is created automatically.</FormDescription>
              <FormMessage />
            </FormItem>
          )}
        />
        <FormField
          control={form.control}
          name="origin_country"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Origin country</FormLabel>
              <FormControl>
                <Input placeholder="Kenya" {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        <FormField
          control={form.control}
          name="region"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Region</FormLabel>
              <FormControl>
                <Input placeholder="Kirinyaga" {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        <FormField
          control={form.control}
          name="producer"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Producer</FormLabel>
              <FormControl>
                <Input placeholder="Kiangoi Factory" {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        <FormField
          control={form.control}
          name="variety"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Variety</FormLabel>
              <FormControl>
                <Input placeholder="SL28, SL34" {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        <FormField
          control={form.control}
          name="process"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Process</FormLabel>
              <Select value={field.value} onValueChange={field.onChange}>
                <FormControl>
                  <SelectTrigger className="w-full">
                    <SelectValue placeholder="Select a process" />
                  </SelectTrigger>
                </FormControl>
                <SelectContent>
                  {PROCESSES.map((process) => (
                    <SelectItem key={process} value={process}>
                      {humanize(process)}
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
          name="roast_level"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Roast level</FormLabel>
              <Select value={field.value} onValueChange={field.onChange}>
                <FormControl>
                  <SelectTrigger className="w-full">
                    <SelectValue placeholder="Select a roast level" />
                  </SelectTrigger>
                </FormControl>
                <SelectContent>
                  {ROAST_LEVELS.map((level) => (
                    <SelectItem key={level} value={level}>
                      {humanize(level)}
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
          name="roast_type"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Roast type</FormLabel>
              <Select value={field.value} onValueChange={field.onChange}>
                <FormControl>
                  <SelectTrigger className="w-full">
                    <SelectValue placeholder="Select a roast type" />
                  </SelectTrigger>
                </FormControl>
                <SelectContent>
                  {ROAST_TYPES.map((type) => (
                    <SelectItem key={type} value={type}>
                      {humanize(type)}
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
          name="blend"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Blend</FormLabel>
              <Select value={field.value} onValueChange={field.onChange}>
                <FormControl>
                  <SelectTrigger className="w-full">
                    <SelectValue placeholder="Single origin or blend" />
                  </SelectTrigger>
                </FormControl>
                <SelectContent>
                  {BLENDS.map((blend) => (
                    <SelectItem key={blend} value={blend}>
                      {humanize(blend)}
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
          name="altitude_masl"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Altitude (masl)</FormLabel>
              <FormControl>
                <Input type="number" min={0} placeholder="1750" {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        <FormField
          control={form.control}
          name="tasting_notes_label"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Notes on the label</FormLabel>
              <FormControl>
                <Input placeholder="Blackcurrant, grapefruit" {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        <FormField
          control={form.control}
          name="website"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Website</FormLabel>
              <FormControl>
                <Input type="url" placeholder="https://roaster.example/coffee" {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        <FormField
          control={form.control}
          name="rating"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Rating</FormLabel>
              <FormControl>
                <StarRating value={field.value} onChange={field.onChange} aria-label="Bean rating" />
              </FormControl>
              <FormDescription>Leave empty if unrated.</FormDescription>
              <FormMessage />
            </FormItem>
          )}
        />
        <FormField
          control={form.control}
          name="notes"
          render={({ field }) => (
            <FormItem className="sm:col-span-2">
              <FormLabel>Your notes</FormLabel>
              <FormControl>
                <Textarea rows={3} {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
      </ResourceDialog>

      <AlertDialog open={pending !== null} onOpenChange={(next) => !next && setPending(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>This coffee is already logged</AlertDialogTitle>
            <AlertDialogDescription>
              {duplicate ? beanLabel(duplicate) : ""} already exists. Keeping one entry per
              coffee keeps its brews and lots together — add a second one only if it really is
              a different coffee.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Back</AlertDialogCancel>
            <Button type="button" variant="outline" onClick={openDuplicate}>
              Open the existing one
            </Button>
            <AlertDialogAction
              onClick={() => {
                const values = pending
                setPending(null)
                if (values) save(values, true)
              }}
            >
              {bean ? "Save anyway" : "Create anyway"}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  )
}
