import { apiFetch } from './client'
import type { CreateFoodRequest, FoodOut, FoodResult } from '../types/api'

export function searchFoods(q: string, source?: string): Promise<FoodResult[]> {
  const params = new URLSearchParams({ q })
  if (source !== undefined) params.set('source', source)
  return apiFetch<FoodResult[]>(`/api/foods?${params.toString()}`)
}

export function createFood(body: CreateFoodRequest): Promise<FoodOut> {
  return apiFetch<FoodOut>('/api/foods', {
    method: 'POST',
    body: JSON.stringify(body),
  })
}
