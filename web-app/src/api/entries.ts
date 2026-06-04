import { apiFetch } from './client'
import type { CreateEntryRequest, CreateEntryResponse } from '../types/api'

export function createEntry(body: CreateEntryRequest): Promise<CreateEntryResponse> {
  return apiFetch<CreateEntryResponse>('/api/entries', {
    method: 'POST',
    body: JSON.stringify(body),
  })
}
