import { apiFetch } from './client'

export interface SettingRead {
  key: string
  value: string | null
  is_set: boolean
}

export const getSettings = () => apiFetch<SettingRead[]>('/api/settings')

export const putSetting = (key: string, value: string | null) =>
  apiFetch<SettingRead>(`/api/settings/${key}`, {
    method: 'PUT',
    body: JSON.stringify({ value }),
  })
