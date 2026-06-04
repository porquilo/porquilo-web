export type Confidence = 'measured' | 'estimated' | 'calculated'
export type NutrientMap = Record<string, number>

export interface NutrientValue {
  value: number
  coverage: string
}

// Meals

export interface Meal {
  id: string
  name: string
  sort_order: number
  is_default: boolean
}

// Foods — GET /api/foods response

export interface FoodVariant {
  id: string
  name: string | null
  amount: number | null
  unit: string
}

export interface FoodResult {
  id: string
  name: string
  brand: string | null
  source: string
  default_unit: string
  nutrients: NutrientMap
  variants: FoodVariant[]
}

// Foods — POST /api/foods request

export interface NutrientIn {
  nutrient_key: string
  value_per_100: number
}

export interface VariantIn {
  name: string
  amount: number
  unit: string
}

export interface CreateFoodRequest {
  name: string
  brand?: string
  barcode?: string
  source?: string
  source_id?: string
  default_unit?: string
  nutrients: NutrientIn[]
  variants?: VariantIn[]
}

// Foods — POST /api/foods response

export interface NutrientOut {
  nutrient_key: string
  value_per_100: number
}

export interface VariantOut {
  name: string | null
  amount: number | null
  unit: string
}

export interface FoodOut {
  id: string
  name: string
  brand: string | null
  source: string
  default_unit: string
  nutrients: NutrientOut[]
  variants: VariantOut[]
}

// Diary

export interface DiaryEntry {
  id: string
  food_name: string
  weight_g: number | null
  weight_confidence: Confidence
  input_method: string
  eaten_at: string
  nutrients: Record<string, NutrientValue>
}

export interface DiaryMeal {
  meal_id: string
  meal_name: string
  is_skipped: boolean
  entries: DiaryEntry[]
  meal_totals: NutrientMap
}

export interface DiaryDay {
  date: string
  meals: DiaryMeal[]
  day_totals: NutrientMap
  has_estimated_entries: boolean
}

// Entries

export interface CreateEntryRequest {
  food_id: string
  meal_id: string
  weight_g: number
  eaten_at: string
  weight_source: string
  input_method: string
}

export interface CreateEntryResponse {
  id: string
  nutrients: Record<string, NutrientValue>
}
