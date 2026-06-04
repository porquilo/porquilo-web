import { apiFetch } from './client'
import type { DiaryDay } from '../types/api'

export function getDiary(date: string): Promise<DiaryDay> {
  return apiFetch<DiaryDay>(`/api/diary/${date}`)
}

export function skipMeal(date: string, mealId: string): Promise<void> {
  return apiFetch<void>(`/api/diary/${date}/meals/${mealId}/skip`, {
    method: 'POST',
  })
}

export function unskipMeal(date: string, mealId: string): Promise<void> {
  return apiFetch<void>(`/api/diary/${date}/meals/${mealId}/skip`, {
    method: 'DELETE',
  })
}
