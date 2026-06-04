import { useQuery } from '@tanstack/react-query'
import { searchFoods, listFoods } from '../api/foods'

export function useFoods(q: string) {
  return useQuery({
    queryKey: ['foods', q],
    queryFn: () => searchFoods(q),
    enabled: q.trim().length >= 2,
  })
}

export function useAllFoods() {
  return useQuery({
    queryKey: ['foods', 'all'],
    queryFn: listFoods,
  })
}
