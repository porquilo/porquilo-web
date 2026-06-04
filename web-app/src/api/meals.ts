import { apiFetch } from './client'
import type { Meal } from '../types/api'

export function getMeals(): Promise<Meal[]> {
  return apiFetch<Meal[]>('/api/meals')
}
