import { useQuery } from '@tanstack/react-query'
import { searchFoods, listFoods } from '../api/foods'
import type { FoodListParams } from '../api/foods'

export type { FoodListParams } from '../api/foods'

export const FOODS_PAGE_SIZES = [25, 50, 100] as const
export type FoodPageSize = typeof FOODS_PAGE_SIZES[number]

export function useFoods(q: string, params: FoodListParams) {
  return useQuery({
    queryKey: ['foods', 'search', q, params],
    queryFn:  () => searchFoods(q, params),
    enabled:  q.trim().length >= 2,
  })
}

export function useAllFoods(params: FoodListParams) {
  return useQuery({
    queryKey: ['foods', 'all', params],
    queryFn:  () => listFoods(params),
  })
}
