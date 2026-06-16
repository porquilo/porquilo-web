import { apiFetch } from './client'
import type { CreateEntryRequest, CreateEntryResponse, EntryDetailOut, UpdateEntryRequest } from '../types/api'

export function createEntry(body: CreateEntryRequest): Promise<CreateEntryResponse> {
  return apiFetch<CreateEntryResponse>('/api/entries', {
    method: 'POST',
    body: JSON.stringify(body),
  })
}

export function getEntry(id: string): Promise<EntryDetailOut> {
  return apiFetch<EntryDetailOut>(`/api/entries/${id}`)
}

export function updateEntry(id: string, patch: UpdateEntryRequest): Promise<EntryDetailOut> {
  return apiFetch<EntryDetailOut>(`/api/entries/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(patch),
  })
}

export function deleteEntry(id: string): Promise<void> {
  return apiFetch<void>(`/api/entries/${id}`, { method: 'DELETE' })
}
