import { apiFetch } from './client'
import type { Meal } from '../types/api'

export function getMeals(): Promise<Meal[]> {
  return apiFetch<Meal[]>('/api/meals')
}

export function createMeal(name: string): Promise<Meal> {
  return apiFetch<Meal>('/api/meals', { method: 'POST', body: JSON.stringify({ name }) })
}

export function patchMeal(id: string, patch: { name?: string; sort_order?: number }): Promise<Meal> {
  return apiFetch<Meal>(`/api/meals/${id}`, { method: 'PATCH', body: JSON.stringify(patch) })
}

export function deleteMeal(id: string): Promise<void> {
  return apiFetch<void>(`/api/meals/${id}`, { method: 'DELETE' })
}
