import { apiFetch } from './client'
import type { AuthUser } from '../types/api'

export async function login(
  username: string,
  password: string,
): Promise<{ token: string; user: AuthUser }> {
  return apiFetch('/api/auth/token', {
    method: 'POST',
    body: JSON.stringify({ username, password }),
  })
}

export async function logout(): Promise<void> {
  await apiFetch<void>('/api/auth/logout', { method: 'POST' })
}

export async function changePassword(
  currentPassword: string,
  newPassword: string,
): Promise<void> {
  await apiFetch<void>('/api/auth/password', {
    method: 'PATCH',
    body: JSON.stringify({ current_password: currentPassword, new_password: newPassword }),
  })
}
