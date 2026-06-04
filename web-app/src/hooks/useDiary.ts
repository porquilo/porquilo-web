import { useQuery } from '@tanstack/react-query'
import { getDiary } from '../api/diary'

export function useDiary(date: string) {
  return useQuery({
    queryKey: ['diary', date],
    queryFn: () => getDiary(date),
  })
}
