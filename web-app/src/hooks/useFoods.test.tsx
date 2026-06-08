import { beforeEach, describe, expect, it, vi } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import type { ReactNode } from 'react'
import { useFoods } from './useFoods'
import type { FoodListParams } from './useFoods'
import { searchFoods } from '../api/foods'

vi.mock('../api/foods', () => ({
  searchFoods: vi.fn().mockResolvedValue({ items: [], total: 0 }),
}))

const DEFAULT_PARAMS: FoodListParams = { page: 1, pageSize: 25, sortBy: 'name', sortDir: 'asc' }

function makeWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
  function Wrapper({ children }: { children: ReactNode }) {
    return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  }
  return Wrapper
}

describe('useFoods', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('is idle when q is empty', () => {
    const { result } = renderHook(() => useFoods('', DEFAULT_PARAMS), { wrapper: makeWrapper() })
    expect(result.current.fetchStatus).toBe('idle')
  })

  it('is idle when q is a single character', () => {
    const { result } = renderHook(() => useFoods('a', DEFAULT_PARAMS), { wrapper: makeWrapper() })
    expect(result.current.fetchStatus).toBe('idle')
  })

  it('is idle when q is only whitespace', () => {
    const { result } = renderHook(() => useFoods('   ', DEFAULT_PARAMS), { wrapper: makeWrapper() })
    expect(result.current.fetchStatus).toBe('idle')
  })

  it('fires when q.trim() has 2+ characters', async () => {
    const { result } = renderHook(() => useFoods('ch', DEFAULT_PARAMS), { wrapper: makeWrapper() })
    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(vi.mocked(searchFoods)).toHaveBeenCalledWith(
      'ch',
      expect.objectContaining({ page: 1, pageSize: 25, sortBy: 'name', sortDir: 'asc' })
    )
  })

  it('does not fire when q has chars but trim is under 2', async () => {
    const { result } = renderHook(() => useFoods(' a', DEFAULT_PARAMS), { wrapper: makeWrapper() })
    expect(result.current.fetchStatus).toBe('idle')
    expect(vi.mocked(searchFoods)).not.toHaveBeenCalled()
  })

  it('returns data from searchFoods', async () => {
    const { result } = renderHook(() => useFoods('chicken', DEFAULT_PARAMS), { wrapper: makeWrapper() })
    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.data?.items).toEqual([])
    expect(result.current.data?.total).toBe(0)
  })
})
