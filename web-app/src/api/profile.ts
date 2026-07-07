import { apiFetch } from './client'

export interface ProfileRead {
  name: string | null
  units_preference: string | null
  timezone: string | null
}

export interface ProfileUpdate {
  name?: string | null
  units_preference?: string | null
  timezone?: string | null
}

export const getProfile = () => apiFetch<ProfileRead>('/api/profile')

export const updateProfile = (body: ProfileUpdate) =>
  apiFetch<ProfileRead>('/api/profile', {
    method: 'PATCH',
    body: JSON.stringify(body),
  })
