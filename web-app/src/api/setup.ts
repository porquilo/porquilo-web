import { apiFetch } from './client'
import type { AuthUser } from '../types/api'

export async function getSetupStatus(): Promise<{ initialized: boolean }> {
  return apiFetch('/api/setup/status')
}

export async function initSetup(
  username: string,
  password: string,
  name?: string,
): Promise<{ token: string; user: AuthUser }> {
  return apiFetch('/api/setup/init', {
    method: 'POST',
    body: JSON.stringify({ username, password, name }),
  })
}
