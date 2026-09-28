import { z } from "zod"

// Keep these aligned with bloom/schemas/common.py so the form fails before the API call.
export const MAX_BREWING_MASS_GRAMS = 9999.99
export const MAX_WATER_TEMP_CELSIUS = 999.9
export const MAX_TDS_PERCENT = 99.99
export const MAX_BREW_TIME_SECONDS = 2_147_483_647
export const MAX_RECIPE_NAME_LENGTH = 200
export const MAX_GRIND_SETTING_LENGTH = 100
export const MAX_BREWING_NOTES_LENGTH = 10_000

function optionalNumber(label: string, minimum: number, maximum: number) {
  return z.string().refine((value) => {
    if (value === "") return true
    const number = Number(value)
    return Number.isFinite(number) && number >= minimum && number <= maximum
  }, `${label} must be between ${minimum} and ${maximum}`)
}

function optionalPositiveNumber(label: string, maximum: number) {
  return z.string().refine((value) => {
    if (value === "") return true
    const number = Number(value)
    return Number.isFinite(number) && number > 0 && number <= maximum
  }, `${label} must be greater than 0 and at most ${maximum}`)
}

export const preparationFieldSchema = {
  method_id: z.string().min(1, "Pick a method"),
  grinder_id: z.string(),
  dose_grams: optionalPositiveNumber("Dose", MAX_BREWING_MASS_GRAMS).refine(
    (value) => value !== "",
    "Dose is required",
  ),
  yield_grams: optionalPositiveNumber("Yield", MAX_BREWING_MASS_GRAMS),
  water_grams: optionalPositiveNumber("Water", MAX_BREWING_MASS_GRAMS),
  grind_setting: z.string().max(MAX_GRIND_SETTING_LENGTH, "Grind setting is too long"),
  water_temp_celsius: optionalNumber("Water temperature", 0, MAX_WATER_TEMP_CELSIUS),
  brew_time_seconds: z.string().refine((value) => {
    if (value === "") return true
    const number = Number(value)
    return Number.isInteger(number) && number > 0 && number <= MAX_BREW_TIME_SECONDS
  }, `Brew time must be a whole number between 1 and ${MAX_BREW_TIME_SECONDS}`),
}

export const tdsSchema = optionalNumber("TDS", 0, MAX_TDS_PERCENT)
export const brewingNotesSchema = z
  .string()
  .max(MAX_BREWING_NOTES_LENGTH, "Notes are too long")
export const recipeNameSchema = z
  .string()
  .trim()
  .min(1, "Name is required")
  .max(MAX_RECIPE_NAME_LENGTH, "Name is too long")

export type PreparationFormValues = z.infer<z.ZodObject<typeof preparationFieldSchema>>
