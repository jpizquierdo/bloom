import {
  beansCreateBeanMutation,
  beansUpdateBeanMutation,
  roastersListRoastersOptions,
} from "@/client/@tanstack/react-query.gen"
import type { BeanRead } from "@/client/types.gen"
import { CreatableCombobox } from "@/components/data/creatable-combobox"
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
import { StarRating } from "@/components/ui/star-rating"
import { Textarea } from "@/components/ui/textarea"
import { BLENDS, PROCESSES, ROAST_LEVELS, ROAST_TYPES } from "@/lib/domain"
import { humanize, stripEmpty } from "@/lib/format"
import { submitAndClose, useCrudFeedback } from "@/lib/mutations"
import { zodResolver } from "@hookform/resolvers/zod"
import { useMutation, useQuery } from "@tanstack/react-query"
import { useEffect } from "react"
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

/** Text inputs give strings; altitude wants a number, and empty means "absent". */
function toPayload(values: FormValues) {
  const { altitude_masl, process, roast_level, roast_type, blend, rating, ...rest } = values
  return {
    ...stripEmpty(rest),
    ...stripEmpty({ altitude_masl: altitude_masl === "" ? undefined : Number(altitude_masl) }),
    ...(process === "" ? {} : { process }),
    ...(roast_level === "" ? {} : { roast_level }),
    roast_type,
    blend,
    // 0 stars means unrated: send an explicit null (not omit), so clearing an existing
    // rating on PATCH actually clears it. The API allows null on rating.
    rating: rating === 0 ? null : rating,
  }
}

interface BeanDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  bean: BeanRead | null
}

export function BeanDialog({ open, onOpenChange, bean }: BeanDialogProps) {
  const feedback = useCrudFeedback()
  const { data: roasters } = useQuery(roastersListRoastersOptions())
  const form = useForm<FormValues>({ resolver: zodResolver(schema), defaultValues: EMPTY })

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

  function onSubmit(values: FormValues) {
    const body = toPayload(values)
    const request = bean
      ? update.mutateAsync({ path: { bean_id: bean.id }, body })
      : create.mutateAsync({ body: { ...body, name: values.name, roaster: values.roaster } })
    return submitAndClose(request, () => onOpenChange(false))
  }

  return (
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
  )
}
