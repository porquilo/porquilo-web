const BASE_URL: string = import.meta.env.VITE_API_BASE_URL ?? ''

let _token: string | null = null

export function setToken(t: string | null): void {
  _token = t
}

export class ApiError extends Error {
  status: number
  code: string
  details: Record<string, unknown>

  constructor(
    status: number,
    message: string,
    code = '',
    details: Record<string, unknown> = {},
  ) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.code = code
    this.details = details
  }
}

export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const headers = new Headers(init?.headers)
  if (init?.body != null && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json')
  }
  if (_token !== null && !headers.has('Authorization')) {
    headers.set('Authorization', `Bearer ${_token}`)
  }

  const response = await fetch(`${BASE_URL}${path}`, { ...init, headers })

  if (response.status === 204) {
    return undefined as T
  }

  if (!response.ok) {
    if (response.status === 401) {
      setToken(null)
      window.dispatchEvent(new CustomEvent('porquilo:unauthorized'))
    }

    let message = 'Request failed'
    let code = ''
    let details: Record<string, unknown> = {}
    try {
      const body = await response.json() as Record<string, unknown>
      const rawEnvelope = body.error
      if (typeof rawEnvelope === 'object' && rawEnvelope !== null) {
        const envelope = rawEnvelope as Record<string, unknown>
        if (typeof envelope.message === 'string') {
          message = envelope.message
          code = typeof envelope.code === 'string' ? envelope.code : ''
          details = typeof envelope.details === 'object' && envelope.details !== null
            ? envelope.details as Record<string, unknown>
            : {}
        }
      } else if (typeof body.detail === 'string') {
        message = body.detail
      } else if (typeof body.message === 'string') {
        message = body.message
      }
    } catch {
      // ignore parse errors
    }
    throw new ApiError(response.status, message, code, details)
  }

  return response.json() as Promise<T>
}
