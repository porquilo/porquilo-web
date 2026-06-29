import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { render, screen, fireEvent, waitFor, cleanup } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import type { ReactNode } from 'react'
import UserManagementPanel from './UserManagementPanel'
import { generatePairingCode, listUsers } from '../../api/users'
import QRCode from 'qrcode'

vi.mock('../../api/users', () => ({
  listUsers: vi.fn(),
  createUser: vi.fn(),
  setUserActive: vi.fn(),
  resetUserPassword: vi.fn(),
  generatePairingCode: vi.fn(),
}))

vi.mock('qrcode', () => ({
  default: { toCanvas: vi.fn().mockResolvedValue(undefined) },
}))

const ACTIVE_USER = {
  id: 'user-1',
  username: 'alice',
  role: 'member',
  name: 'Alice',
  is_active: true,
  created_at: '2026-01-01T00:00:00Z',
}

const DEACTIVATED_USER = {
  id: 'user-2',
  username: 'bob',
  role: 'member',
  name: 'Bob',
  is_active: false,
  created_at: '2026-01-01T00:00:00Z',
}

const SECOND_ACTIVE_USER = {
  id: 'user-3',
  username: 'carol',
  role: 'member',
  name: 'Carol',
  is_active: true,
  created_at: '2026-01-01T00:00:00Z',
}

function renderPanel() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  function Wrapper({ children }: { children: ReactNode }) {
    return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  }
  return render(<UserManagementPanel />, { wrapper: Wrapper })
}

describe('UserManagementPanel pairing', () => {
  beforeEach(() => {
    vi.mocked(listUsers).mockResolvedValue([ACTIVE_USER, DEACTIVATED_USER])
    vi.useFakeTimers({ shouldAdvanceTime: true })
  })

  afterEach(() => {
    cleanup()
    vi.useRealTimers()
    vi.clearAllMocks()
  })

  it('shows "Pair device" only on active rows', async () => {
    renderPanel()
    await waitFor(() => expect(screen.getByText('alice')).toBeDefined())

    const buttons = screen.getAllByText('Pair device')
    expect(buttons).toHaveLength(1)
  })

  it('generates a pairing code and renders a QR canvas with the expected payload', async () => {
    vi.mocked(generatePairingCode).mockResolvedValue({
      code: 'abc123',
      expires_at: new Date(Date.now() + 15 * 60 * 1000).toISOString(),
    })
    renderPanel()
    await waitFor(() => expect(screen.getByText('alice')).toBeDefined())

    fireEvent.click(screen.getByText('Pair device'))
    await waitFor(() => expect(generatePairingCode).toHaveBeenCalledWith('user-1'))
    await waitFor(() => expect(vi.mocked(QRCode.toCanvas)).toHaveBeenCalled())

    const payload = vi.mocked(QRCode.toCanvas).mock.calls[0][1]
    expect(payload).toBe(JSON.stringify({ server: window.location.origin, code: 'abc123' }))
    expect(screen.getByText(/Expires in/)).toBeDefined()
  })

  it('decrements the countdown each second', async () => {
    vi.mocked(generatePairingCode).mockResolvedValue({
      code: 'abc123',
      expires_at: new Date(Date.now() + 65 * 1000).toISOString(),
    })
    renderPanel()
    await waitFor(() => expect(screen.getByText('alice')).toBeDefined())
    fireEvent.click(screen.getByText('Pair device'))
    await waitFor(() => expect(screen.getByText(/Expires in/)).toBeDefined())
    const before = screen.getByText(/Expires in/).textContent
    const secondsBefore = Number(before?.match(/(\d+):(\d+)/)?.slice(1).join('') ?? '0')

    await vi.advanceTimersByTimeAsync(2000)
    const after = screen.getByText(/Expires in/).textContent
    const secondsAfter = Number(after?.match(/(\d+):(\d+)/)?.slice(1).join('') ?? '0')
    expect(secondsAfter).toBeLessThan(secondsBefore)
  })

  it('shows expiry message and Regenerate button when countdown hits zero', async () => {
    vi.mocked(generatePairingCode).mockResolvedValue({
      code: 'abc123',
      expires_at: new Date(Date.now() + 2 * 1000).toISOString(),
    })
    renderPanel()
    await waitFor(() => expect(screen.getByText('alice')).toBeDefined())
    fireEvent.click(screen.getByText('Pair device'))
    await waitFor(() => expect(screen.getByText(/Expires in/)).toBeDefined())

    await vi.advanceTimersByTimeAsync(3000)

    expect(screen.getByText('Code expired.')).toBeDefined()
    expect(screen.getByText('Regenerate')).toBeDefined()
    expect(screen.queryByText(/Expires in/)).toBeNull()
  })

  it('regenerates a fresh code and timer when Regenerate is clicked', async () => {
    vi.mocked(generatePairingCode)
      .mockResolvedValueOnce({
        code: 'abc123',
        expires_at: new Date(Date.now() + 2 * 1000).toISOString(),
      })
      .mockResolvedValueOnce({
        code: 'def456',
        expires_at: new Date(Date.now() + 15 * 60 * 1000).toISOString(),
      })
    renderPanel()
    await waitFor(() => expect(screen.getByText('alice')).toBeDefined())
    fireEvent.click(screen.getByText('Pair device'))
    await waitFor(() => expect(screen.getByText(/Expires in/)).toBeDefined())
    await vi.advanceTimersByTimeAsync(3000)
    expect(screen.getByText('Code expired.')).toBeDefined()

    fireEvent.click(screen.getByText('Regenerate'))
    await waitFor(() => expect(generatePairingCode).toHaveBeenCalledTimes(2))
    await waitFor(() => expect(screen.getByText(/Expires in/)).toBeDefined())
    expect(screen.queryByText('Code expired.')).toBeNull()
  })

  it('closes the panel when Done is clicked', async () => {
    vi.mocked(generatePairingCode).mockResolvedValue({
      code: 'abc123',
      expires_at: new Date(Date.now() + 15 * 60 * 1000).toISOString(),
    })
    renderPanel()
    await waitFor(() => expect(screen.getByText('alice')).toBeDefined())
    fireEvent.click(screen.getByText('Pair device'))
    await waitFor(() => expect(screen.getByText(/Expires in/)).toBeDefined())

    fireEvent.click(screen.getByText('Done'))
    expect(screen.queryByText(/Expires in/)).toBeNull()
  })

  it('shows an inline error and does not open the panel on failure', async () => {
    vi.mocked(generatePairingCode).mockRejectedValue(new Error('boom'))
    renderPanel()
    await waitFor(() => expect(screen.getByText('alice')).toBeDefined())
    fireEvent.click(screen.getByText('Pair device'))

    await waitFor(() => expect(screen.getByText('boom')).toBeDefined())
    expect(screen.queryByText(/Expires in/)).toBeNull()
  })

  it('supports two independent panels open at once', async () => {
    vi.mocked(listUsers).mockResolvedValue([ACTIVE_USER, SECOND_ACTIVE_USER])
    vi.mocked(generatePairingCode)
      .mockResolvedValueOnce({
        code: 'abc123',
        expires_at: new Date(Date.now() + 15 * 60 * 1000).toISOString(),
      })
      .mockResolvedValueOnce({
        code: 'def456',
        expires_at: new Date(Date.now() + 15 * 60 * 1000).toISOString(),
      })
    renderPanel()
    await waitFor(() => expect(screen.getByText('alice')).toBeDefined())

    const pairButtons = screen.getAllByText('Pair device')
    fireEvent.click(pairButtons[0])
    await waitFor(() => expect(generatePairingCode).toHaveBeenCalledTimes(1))
    fireEvent.click(pairButtons[1])
    await waitFor(() => expect(generatePairingCode).toHaveBeenCalledTimes(2))

    await waitFor(() => expect(screen.getAllByText(/Expires in/)).toHaveLength(2))
  })
})
