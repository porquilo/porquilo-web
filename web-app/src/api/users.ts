import { apiFetch } from './client'
import type { AdminUser } from '../types/api'

export async function listUsers(): Promise<AdminUser[]> {
  return apiFetch('/api/users')
}

export async function createUser(body: {
  username: string
  password: string
  role?: string
  name?: string
}): Promise<AdminUser> {
  return apiFetch('/api/users', {
    method: 'POST',
    body: JSON.stringify(body),
  })
}

export async function setUserActive(userId: string, isActive: boolean): Promise<AdminUser> {
  return apiFetch(`/api/users/${userId}`, {
    method: 'PATCH',
    body: JSON.stringify({ is_active: isActive }),
  })
}

export async function resetUserPassword(userId: string, newPassword: string): Promise<void> {
  await apiFetch<void>(`/api/users/${userId}/reset-password`, {
    method: 'POST',
    body: JSON.stringify({ new_password: newPassword }),
  })
}

export async function generatePairingCode(userId: string): Promise<{ code: string; expires_at: string }> {
  return apiFetch(`/api/users/${userId}/pairing-code`, {
    method: 'POST',
  })
}
