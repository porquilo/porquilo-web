import { useMutation, useQueryClient } from '@tanstack/react-query'
import type { ApiError } from '../api/client'
import { createEntry } from '../api/entries'
import { skipMeal, unskipMeal } from '../api/diary'
import type { CreateEntryRequest } from '../types/api'

export function useCreateEntry() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (body: CreateEntryRequest) => createEntry(body),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['diary'] })
    },
  })
}

export function useSkipMeal() {
  const queryClient = useQueryClient()
  return useMutation<void, ApiError, { date: string; mealId: string }>({
    mutationFn: ({ date, mealId }) => skipMeal(date, mealId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['diary'] })
    },
  })
}

export function useUnskipMeal() {
  const queryClient = useQueryClient()
  return useMutation<void, ApiError, { date: string; mealId: string }>({
    mutationFn: ({ date, mealId }) => unskipMeal(date, mealId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['diary'] })
    },
  })
}
