import { beforeEach, describe, expect, it, vi } from 'vitest'
import { ApiError, apiFetch } from './client'

const mockFetch = vi.fn()
vi.stubGlobal('fetch', mockFetch)

function mockResponse(status: number, body: unknown): Response {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: () => Promise.resolve(body),
  } as unknown as Response
}

describe('apiFetch', () => {
  beforeEach(() => {
    mockFetch.mockReset()
  })

  it('returns parsed JSON on a 200 response', async () => {
    mockFetch.mockResolvedValueOnce(mockResponse(200, { id: '1' }))
    const result = await apiFetch<{ id: string }>('/test')
    expect(result).toEqual({ id: '1' })
  })

  it('returns undefined on 204 No Content', async () => {
    mockFetch.mockResolvedValueOnce(mockResponse(204, null))
    const result = await apiFetch<void>('/test')
    expect(result).toBeUndefined()
  })

  it('throws ApiError with correct status on a 422 response', async () => {
    mockFetch.mockResolvedValueOnce(mockResponse(422, { detail: 'Validation error' }))
    let caught: unknown
    try { await apiFetch('/test') } catch (e) { caught = e }
    expect(caught).toBeInstanceOf(ApiError)
    expect((caught as ApiError).status).toBe(422)
  })

  it('uses detail field as the error message', async () => {
    mockFetch.mockResolvedValueOnce(mockResponse(422, { detail: 'field required' }))
    let caught: unknown
    try { await apiFetch('/test') } catch (e) { caught = e }
    expect(caught).toBeInstanceOf(ApiError)
    expect((caught as ApiError).message).toBe('field required')
  })

  it('falls back to message field when detail is absent', async () => {
    mockFetch.mockResolvedValueOnce(mockResponse(500, { message: 'server blew up' }))
    let caught: unknown
    try { await apiFetch('/test') } catch (e) { caught = e }
    expect((caught as ApiError).message).toBe('server blew up')
  })

  it('falls back to "Request failed" when body has neither detail nor message', async () => {
    mockFetch.mockResolvedValueOnce(mockResponse(500, {}))
    let caught: unknown
    try { await apiFetch('/test') } catch (e) { caught = e }
    expect((caught as ApiError).message).toBe('Request failed')
  })

  it('sets Content-Type: application/json when a body is present', async () => {
    mockFetch.mockResolvedValueOnce(mockResponse(201, {}))
    await apiFetch('/test', { method: 'POST', body: JSON.stringify({ x: 1 }) })
    const [, init] = mockFetch.mock.calls[0] as [string, { headers: Headers }]
    expect(init.headers.get('Content-Type')).toBe('application/json')
  })

  it('does not set Content-Type when no body is present', async () => {
    mockFetch.mockResolvedValueOnce(mockResponse(200, {}))
    await apiFetch('/test')
    const [, init] = mockFetch.mock.calls[0] as [string, { headers: Headers }]
    expect(init.headers.get('Content-Type')).toBeNull()
  })
})
