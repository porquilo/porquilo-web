import { useQuery } from '@tanstack/react-query'
import { getMeals } from '../api/meals'

export function useMeals() {
  return useQuery({
    queryKey: ['meals'],
    queryFn: getMeals,
  })
}
