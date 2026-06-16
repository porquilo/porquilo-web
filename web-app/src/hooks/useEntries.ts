import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import type { ApiError } from '../api/client'
import { createEntry, deleteEntry, getEntry, updateEntry } from '../api/entries'
import { skipMeal, unskipMeal } from '../api/diary'
import type { CreateEntryRequest, EntryDetailOut, UpdateEntryRequest } from '../types/api'

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

export function useEntry(id: string | null) {
  return useQuery({
    queryKey: ['entry', id],
    queryFn: () => getEntry(id!),
    enabled: id !== null,
  })
}

export function useUpdateEntry() {
  const queryClient = useQueryClient()
  return useMutation<EntryDetailOut, ApiError, { id: string; patch: UpdateEntryRequest }>({
    mutationFn: ({ id, patch }) => updateEntry(id, patch),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['diary'] })
    },
  })
}

export function useDeleteEntry() {
  const queryClient = useQueryClient()
  return useMutation<void, ApiError, string>({
    mutationFn: (id) => deleteEntry(id),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['diary'] })
    },
  })
}
