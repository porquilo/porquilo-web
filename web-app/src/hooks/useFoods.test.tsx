import { beforeEach, describe, expect, it, vi } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import type { ReactNode } from 'react'
import { useFoods } from './useFoods'
import { searchFoods } from '../api/foods'

vi.mock('../api/foods', () => ({
  searchFoods: vi.fn().mockResolvedValue([]),
}))

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
    const { result } = renderHook(() => useFoods(''), { wrapper: makeWrapper() })
    expect(result.current.fetchStatus).toBe('idle')
  })

  it('is idle when q is a single character', () => {
    const { result } = renderHook(() => useFoods('a'), { wrapper: makeWrapper() })
    expect(result.current.fetchStatus).toBe('idle')
  })

  it('is idle when q is only whitespace', () => {
    const { result } = renderHook(() => useFoods('   '), { wrapper: makeWrapper() })
    expect(result.current.fetchStatus).toBe('idle')
  })

  it('fires when q.trim() has 2+ characters', async () => {
    const { result } = renderHook(() => useFoods('ch'), { wrapper: makeWrapper() })
    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(vi.mocked(searchFoods)).toHaveBeenCalledWith('ch')
  })

  it('does not fire when q has chars but trim is under 2', async () => {
    const { result } = renderHook(() => useFoods(' a'), { wrapper: makeWrapper() })
    expect(result.current.fetchStatus).toBe('idle')
    expect(vi.mocked(searchFoods)).not.toHaveBeenCalled()
  })

  it('returns data from searchFoods', async () => {
    const { result } = renderHook(() => useFoods('chicken'), { wrapper: makeWrapper() })
    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.data).toEqual([])
  })
})
