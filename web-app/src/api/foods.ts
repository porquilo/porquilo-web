import { apiFetch } from './client'
import type { CreateFoodRequest, FoodOut, FoodResult } from '../types/api'

export interface FoodPage { items: FoodResult[]; total: number }

export interface FoodListParams {
  page:     number
  pageSize: number
  sortBy:   string
  sortDir:  'asc' | 'desc'
  source?:  string
}

export function searchFoods(q: string, params: FoodListParams): Promise<FoodPage> {
  const p = new URLSearchParams({ q })
  if (params.source !== undefined) p.set('source', params.source)
  p.set('limit', String(params.pageSize))
  p.set('offset', String((params.page - 1) * params.pageSize))
  p.set('sort_by', params.sortBy)
  p.set('sort_dir', params.sortDir)
  return apiFetch<FoodPage>(`/api/foods?${p.toString()}`)
}

export function listFoods(params: FoodListParams): Promise<FoodPage> {
  const p = new URLSearchParams()
  if (params.source !== undefined) p.set('source', params.source)
  p.set('limit', String(params.pageSize))
  p.set('offset', String((params.page - 1) * params.pageSize))
  p.set('sort_by', params.sortBy)
  p.set('sort_dir', params.sortDir)
  return apiFetch<FoodPage>(`/api/foods?${p.toString()}`)
}

export function createFood(body: CreateFoodRequest): Promise<FoodOut> {
  return apiFetch<FoodOut>('/api/foods', {
    method: 'POST',
    body: JSON.stringify(body),
  })
}
