import { apiFetch } from './client'

export interface OffSyncStatus {
  status: 'queued' | 'running' | 'succeeded' | 'failed' | null
  last_synced_at: string | null
  error: string | null
  sync_progress: number | null
  sync_total: number | null
}

export function startOffSync(): Promise<{ status: string }> {
  return apiFetch('/api/sync/off', { method: 'POST' })
}

export function getOffSyncStatus(): Promise<OffSyncStatus> {
  return apiFetch('/api/sync/off/status')
}
