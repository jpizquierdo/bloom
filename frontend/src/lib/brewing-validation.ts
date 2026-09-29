import { z } from "zod"

// Keep these aligned with bloom/schemas/common.py so the form fails before the API call.
export const MAX_BREWING_MASS_GRAMS = 9999.99
export const MAX_WATER_TEMP_CELSIUS = 999.9
export const MAX_TDS_PERCENT = 99.99
export const MAX_BREW_TIME_SECONDS = 2_147_483_647
export const MAX_RECIPE_NAME_LENGTH = 200
export const MAX_GRIND_SETTING_LENGTH = 100
export const MAX_BREWING_NOTES_LENGTH = 10_000

function optionalNumber(isValid: (number: number) => boolean, message: string) {
  return z.string().refine((value) => value === "" || isValid(Number(value)), message)
}

const between = (label: string, minimum: number, maximum: number) =>
  optionalNumber(
    (n) => n >= minimum && n <= maximum,
    `${label} must be between ${minimum} and ${maximum}`,
  )

const positiveUpTo = (label: string, maximum: number) =>
  optionalNumber(
    (n) => n > 0 && n <= maximum,
    `${label} must be greater than 0 and at most ${maximum}`,
  )

export const preparationFieldSchema = {
  method_id: z.string().min(1, "Pick a method"),
  grinder_id: z.string(),
  dose_grams: positiveUpTo("Dose", MAX_BREWING_MASS_GRAMS).refine(
    (value) => value !== "",
    "Dose is required",
  ),
  yield_grams: positiveUpTo("Yield", MAX_BREWING_MASS_GRAMS),
  water_grams: positiveUpTo("Water", MAX_BREWING_MASS_GRAMS),
  grind_setting: z.string().max(MAX_GRIND_SETTING_LENGTH, "Grind setting is too long"),
  water_temp_celsius: between("Water temperature", 0, MAX_WATER_TEMP_CELSIUS),
  brew_time_seconds: optionalNumber(
    (n) => Number.isInteger(n) && n > 0 && n <= MAX_BREW_TIME_SECONDS,
    `Brew time must be a whole number between 1 and ${MAX_BREW_TIME_SECONDS}`,
  ),
}

export const tdsSchema = between("TDS", 0, MAX_TDS_PERCENT)
export const brewingNotesSchema = z
  .string()
  .max(MAX_BREWING_NOTES_LENGTH, "Notes are too long")
export const recipeNameSchema = z
  .string()
  .trim()
  .min(1, "Name is required")
  .max(MAX_RECIPE_NAME_LENGTH, "Name is too long")

export type PreparationFormValues = z.infer<z.ZodObject<typeof preparationFieldSchema>>
