import {
  brewMethodsListBrewMethodsOptions,
  equipmentListEquipmentOptions,
} from "@/client/@tanstack/react-query.gen"
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
import {
  MAX_BREW_TIME_SECONDS,
  MAX_BREWING_MASS_GRAMS,
  MAX_GRIND_SETTING_LENGTH,
  MAX_WATER_TEMP_CELSIUS,
  type PreparationFormValues,
} from "@/lib/brewing-validation"
import { useQuery } from "@tanstack/react-query"
import { useFormContext } from "react-hook-form"

interface PreparationFieldsProps {
  methodDisabled?: boolean
  methodDescription?: string
}

export function PreparationFields({
  methodDisabled = false,
  methodDescription,
}: PreparationFieldsProps) {
  const form = useFormContext<PreparationFormValues>()
  const { data: methods } = useQuery(brewMethodsListBrewMethodsOptions())
  const { data: equipment } = useQuery(equipmentListEquipmentOptions())
  const grinders = (equipment ?? []).filter((item) => item.type === "grinder")

  return (
    <>
      <FormField
        control={form.control}
        name="method_id"
        render={({ field }) => (
          <FormItem>
            <FormLabel>Method</FormLabel>
            <Select value={field.value} onValueChange={field.onChange} disabled={methodDisabled}>
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
            {methodDescription ? <FormDescription>{methodDescription}</FormDescription> : null}
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
              <Input
                type="number"
                min={0}
                max={MAX_BREWING_MASS_GRAMS}
                step="0.1"
                placeholder="18.0"
                {...field}
              />
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
              <Input
                type="number"
                min={0}
                max={MAX_BREWING_MASS_GRAMS}
                step="0.1"
                placeholder="36.0"
                {...field}
              />
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
              <Input
                type="number"
                min={0}
                max={MAX_BREWING_MASS_GRAMS}
                step="0.1"
                placeholder="300"
                {...field}
              />
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
            <Select
              value={field.value === "" ? "none" : field.value}
              onValueChange={(value) => field.onChange(value === "none" ? "" : value)}
            >
              <FormControl>
                <SelectTrigger className="w-full">
                  <SelectValue placeholder="Select a grinder" />
                </SelectTrigger>
              </FormControl>
              <SelectContent>
                <SelectItem value="none">No grinder</SelectItem>
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
              <Input maxLength={MAX_GRIND_SETTING_LENGTH} placeholder="2.5" {...field} />
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
              <Input
                type="number"
                min={0}
                max={MAX_WATER_TEMP_CELSIUS}
                step="0.1"
                placeholder="93.0"
                {...field}
              />
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
              <Input
                type="number"
                min={0}
                max={MAX_BREW_TIME_SECONDS}
                placeholder="28"
                {...field}
              />
            </FormControl>
            <FormMessage />
          </FormItem>
        )}
      />
    </>
  )
}
