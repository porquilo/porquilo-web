const BASE_URL: string = import.meta.env.VITE_API_BASE_URL ?? ''

export class ApiError extends Error {
  status: number

  constructor(status: number, message: string) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const headers = new Headers(init?.headers)
  if (init?.body != null && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json')
  }

  const response = await fetch(`${BASE_URL}${path}`, { ...init, headers })

  if (response.status === 204) {
    return undefined as T
  }

  if (!response.ok) {
    let message = 'Request failed'
    try {
      const body = await response.json() as Record<string, unknown>
      const detail = body.detail
      const msg = body.message
      if (typeof detail === 'string') message = detail
      else if (typeof msg === 'string') message = msg
    } catch {
      // ignore parse errors
    }
    throw new ApiError(response.status, message)
  }

  return response.json() as Promise<T>
}
