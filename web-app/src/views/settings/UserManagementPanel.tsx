import { Fragment, useEffect, useRef, useState } from 'react'
import type { CSSProperties, FormEvent } from 'react'
import QRCode from 'qrcode'
import {
  useUsers,
  useCreateUser,
  useSetUserActive,
  useResetUserPassword,
  useGeneratePairingCode,
} from '../../hooks/useUsers'
import { useToast } from '../../contexts/ToastContext'
import { Button } from '../../components/Button'
import { parseUtcTimestamp } from '../../utils/dates'
import type { AdminUser } from '../../types/api'

const inputStyle: CSSProperties = {
  padding: '6px 9px',
  background: 'var(--bg-sunken)',
  border: '1px solid var(--border-soft)',
  borderRadius: 6,
  fontSize: 13,
  color: 'var(--fg1)',
  outline: 'none',
  fontFamily: 'var(--font-body)',
  boxSizing: 'border-box',
}

const cellStyle: CSSProperties = {
  padding: '10px 8px',
  fontSize: 13,
  color: 'var(--fg1)',
  borderBottom: '1px dashed var(--border-soft)',
  verticalAlign: 'top',
}

type PairingEntry = { code: string; expiresAt: Date } | 'expired'

function remainingSeconds(expiresAt: Date): number {
  return Math.max(0, Math.floor((expiresAt.getTime() - Date.now()) / 1000))
}

function formatCountdown(seconds: number): string {
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  return `${m}:${s.toString().padStart(2, '0')}`
}

export default function UserManagementPanel() {
  const { data: users = [], isLoading } = useUsers()
  const createUser = useCreateUser()
  const setActive = useSetUserActive()
  const resetPw = useResetUserPassword()
  const generatePairing = useGeneratePairingCode()
  const { setToast } = useToast()

  const [showAddForm, setShowAddForm] = useState(false)
  const [addForm, setAddForm] = useState({ username: '', password: '', name: '', role: 'member' })
  const [addError, setAddError] = useState<string | null>(null)

  const [showResetFor, setShowResetFor] = useState<string | null>(null)
  const [resetPwValue, setResetPwValue] = useState('')

  const [pairingState, setPairingState] = useState<Map<string, PairingEntry>>(new Map())
  const [pairingError, setPairingError] = useState<Map<string, string>>(new Map())
  const canvasRefs = useRef<Map<string, HTMLCanvasElement>>(new Map())
  const [, setTick] = useState(0)

  useEffect(() => {
    const hasActiveEntry = Array.from(pairingState.values()).some(entry => entry !== 'expired')
    if (!hasActiveEntry) return

    const interval = setInterval(() => {
      setPairingState(prev => {
        let changed = false
        const next = new Map(prev)
        for (const [userId, entry] of prev) {
          if (entry !== 'expired' && remainingSeconds(entry.expiresAt) <= 0) {
            next.set(userId, 'expired')
            canvasRefs.current.delete(userId)
            changed = true
          }
        }
        return changed ? next : prev
      })
      setTick(t => t + 1)
    }, 1000)

    return () => clearInterval(interval)
  }, [pairingState])

  async function handleAddUser(e: FormEvent) {
    e.preventDefault()
    setAddError(null)
    try {
      await createUser.mutateAsync({
        username: addForm.username,
        password: addForm.password,
        role: addForm.role,
        name: addForm.name.trim() || undefined,
      })
      setShowAddForm(false)
      setAddForm({ username: '', password: '', name: '', role: 'member' })
      setToast('Account created')
    } catch (err) {
      setAddError(err instanceof Error ? err.message : 'Failed to create account')
    }
  }

  async function handleToggleActive(user: AdminUser) {
    try {
      await setActive.mutateAsync({ userId: user.id, isActive: !user.is_active })
      setToast(user.is_active ? 'Account deactivated' : 'Account reactivated')
    } catch (err) {
      setToast(err instanceof Error ? err.message : 'Update failed')
    }
  }

  async function handleResetPassword(userId: string) {
    if (!resetPwValue.trim()) return
    try {
      await resetPw.mutateAsync({ userId, newPassword: resetPwValue })
      setShowResetFor(null)
      setResetPwValue('')
      setToast('Password reset')
    } catch (err) {
      setToast(err instanceof Error ? err.message : 'Reset failed')
    }
  }

  async function handlePairDevice(userId: string) {
    setPairingError(prev => {
      if (!prev.has(userId)) return prev
      const next = new Map(prev)
      next.delete(userId)
      return next
    })
    try {
      const result = await generatePairing.mutateAsync(userId)
      setPairingState(prev =>
        new Map(prev).set(userId, { code: result.code, expiresAt: parseUtcTimestamp(result.expires_at) })
      )
    } catch (err) {
      setPairingError(prev =>
        new Map(prev).set(userId, err instanceof Error ? err.message : 'Failed to generate pairing code')
      )
    }
  }

  function handleDonePairing(userId: string) {
    canvasRefs.current.delete(userId)
    setPairingState(prev => {
      const next = new Map(prev)
      next.delete(userId)
      return next
    })
  }

  function canvasRefCallback(userId: string, entry: PairingEntry) {
    return (el: HTMLCanvasElement | null) => {
      if (!el) {
        canvasRefs.current.delete(userId)
        return
      }
      canvasRefs.current.set(userId, el)
      if (entry !== 'expired') {
        const payload = JSON.stringify({ server: window.location.origin, code: entry.code })
        void QRCode.toCanvas(el, payload, { width: 240, margin: 2 })
      }
    }
  }

  if (isLoading) {
    return (
      <div style={{ fontSize: 13, color: 'var(--fg3)', padding: '4px 0' }}>
        Loading…
      </div>
    )
  }

  return (
    <div>
      {/* Add account */}
      {showAddForm ? (
        <form
          onSubmit={(e) => void handleAddUser(e)}
          style={{
            background: 'var(--bg-sunken)',
            borderRadius: 8,
            padding: '12px 14px',
            marginBottom: 14,
            display: 'flex',
            flexDirection: 'column',
            gap: 8,
          }}
        >
          <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--fg2)', marginBottom: 2 }}>
            New account
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
            <input
              autoFocus
              required
              type="text"
              placeholder="Username"
              value={addForm.username}
              onChange={e => setAddForm(f => ({ ...f, username: e.target.value }))}
              style={{ ...inputStyle, width: '100%' }}
            />
            <input
              required
              type="password"
              placeholder="Password"
              value={addForm.password}
              onChange={e => setAddForm(f => ({ ...f, password: e.target.value }))}
              style={{ ...inputStyle, width: '100%' }}
            />
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
            <input
              type="text"
              placeholder="Display name (optional)"
              value={addForm.name}
              onChange={e => setAddForm(f => ({ ...f, name: e.target.value }))}
              style={{ ...inputStyle, width: '100%' }}
            />
            <select
              value={addForm.role}
              onChange={e => setAddForm(f => ({ ...f, role: e.target.value }))}
              style={{ ...inputStyle, width: '100%' }}
            >
              <option value="member">Member</option>
              <option value="admin">Admin</option>
            </select>
          </div>
          {addError !== null && (
            <div style={{ fontSize: 12, color: 'var(--danger-fg)' }}>{addError}</div>
          )}
          <div style={{ display: 'flex', gap: 8 }}>
            <Button type="submit" variant="primary" disabled={createUser.isPending}>
              {createUser.isPending ? 'Creating…' : 'Create account'}
            </Button>
            <Button
              variant="secondary"
              onClick={() => {
                setShowAddForm(false)
                setAddError(null)
                setAddForm({ username: '', password: '', name: '', role: 'member' })
              }}
            >
              Cancel
            </Button>
          </div>
        </form>
      ) : (
        <div style={{ marginBottom: 14 }}>
          <Button variant="secondary" onClick={() => setShowAddForm(true)}>
            Add account
          </Button>
        </div>
      )}

      {/* User table */}
      <div style={{ overflowX: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr>
              {['Username', 'Role', 'Display name', 'Status', 'Actions'].map(h => (
                <th
                  key={h}
                  style={{
                    ...cellStyle,
                    fontSize: 11,
                    color: 'var(--fg3)',
                    fontWeight: 600,
                    textAlign: 'left',
                    letterSpacing: '0.02em',
                    padding: '4px 8px 8px',
                  }}
                >
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {users.map(user => {
              const entry = pairingState.get(user.id)
              const error = pairingError.get(user.id)
              return (
                <Fragment key={user.id}>
                  <tr>
                    <td style={{ ...cellStyle, fontFamily: 'var(--font-mono)', fontSize: 13 }}>
                      {user.username}
                    </td>
                    <td style={{ ...cellStyle, color: 'var(--fg2)' }}>
                      {user.role}
                    </td>
                    <td style={{ ...cellStyle, color: 'var(--fg2)' }}>
                      {user.name ?? <span style={{ color: 'var(--fg4)' }}>—</span>}
                    </td>
                    <td style={{ ...cellStyle }}>
                      <span style={{
                        fontSize: 11,
                        fontWeight: 600,
                        color: user.is_active ? 'var(--success-fg)' : 'var(--fg4)',
                        background: user.is_active ? 'var(--success-bg)' : 'var(--bg-sunken)',
                        borderRadius: 4,
                        padding: '2px 6px',
                        whiteSpace: 'nowrap',
                      }}>
                        {user.is_active ? 'Active' : 'Deactivated'}
                      </span>
                    </td>
                    <td style={{ ...cellStyle }}>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                        {showResetFor === user.id ? (
                          <div style={{ display: 'flex', gap: 6, alignItems: 'center', flexWrap: 'wrap' }}>
                            <input
                              autoFocus
                              type="password"
                              placeholder="New password"
                              value={resetPwValue}
                              onChange={e => setResetPwValue(e.target.value)}
                              style={{ ...inputStyle, width: 130 }}
                            />
                            <Button
                              variant="primary"
                              disabled={resetPw.isPending}
                              onClick={() => void handleResetPassword(user.id)}
                            >
                              {resetPw.isPending ? '…' : 'Set'}
                            </Button>
                            <Button
                              variant="secondary"
                              onClick={() => {
                                setShowResetFor(null)
                                setResetPwValue('')
                              }}
                            >
                              Cancel
                            </Button>
                          </div>
                        ) : (
                          <button
                            onClick={() => {
                              setShowResetFor(user.id)
                              setResetPwValue('')
                            }}
                            style={{
                              background: 'none',
                              border: 'none',
                              cursor: 'pointer',
                              fontSize: 12,
                              color: 'var(--fg2)',
                              padding: 0,
                              textAlign: 'left',
                              fontFamily: 'var(--font-body)',
                            }}
                          >
                            Reset password
                          </button>
                        )}
                        <button
                          onClick={() => void handleToggleActive(user)}
                          disabled={setActive.isPending}
                          style={{
                            background: 'none',
                            border: 'none',
                            cursor: setActive.isPending ? 'not-allowed' : 'pointer',
                            fontSize: 12,
                            color: user.is_active ? 'var(--danger-fg)' : 'var(--accent)',
                            padding: 0,
                            textAlign: 'left',
                            opacity: setActive.isPending ? 0.5 : 1,
                            fontFamily: 'var(--font-body)',
                          }}
                        >
                          {user.is_active ? 'Deactivate' : 'Reactivate'}
                        </button>
                        {user.is_active && (
                          <button
                            onClick={() => void handlePairDevice(user.id)}
                            style={{
                              background: 'none',
                              border: 'none',
                              cursor: 'pointer',
                              fontSize: 12,
                              color: 'var(--fg2)',
                              padding: 0,
                              textAlign: 'left',
                              fontFamily: 'var(--font-body)',
                            }}
                          >
                            Pair device
                          </button>
                        )}
                        {error !== undefined && (
                          <div style={{ fontSize: 12, color: 'var(--danger-fg)' }}>{error}</div>
                        )}
                      </div>
                    </td>
                  </tr>
                  {entry !== undefined && (
                    <tr>
                      <td colSpan={5} style={{ padding: '0 8px 12px', borderBottom: '1px dashed var(--border-soft)' }}>
                        <div
                          style={{
                            background: 'var(--bg-elevated)',
                            boxShadow: 'var(--shadow-2)',
                            borderRadius: 8,
                            padding: '16px',
                            display: 'flex',
                            flexDirection: 'column',
                            alignItems: 'center',
                            gap: 10,
                          }}
                        >
                          {entry === 'expired' ? (
                            <div style={{ fontSize: 13, color: 'var(--fg2)', padding: '40px 0' }}>
                              Code expired.
                            </div>
                          ) : (
                            <>
                              <canvas
                                ref={canvasRefCallback(user.id, entry)}
                                width={240}
                                height={240}
                                style={{ width: 240, height: 240 }}
                              />
                              <div style={{ fontSize: 12, color: 'var(--fg3)' }}>
                                Expires in {formatCountdown(remainingSeconds(entry.expiresAt))}
                              </div>
                            </>
                          )}
                          <div style={{ display: 'flex', gap: 8, alignSelf: 'flex-end' }}>
                            {entry === 'expired' && (
                              <Button variant="secondary" onClick={() => void handlePairDevice(user.id)}>
                                Regenerate
                              </Button>
                            )}
                            <Button variant="secondary" onClick={() => handleDonePairing(user.id)}>
                              Done
                            </Button>
                          </div>
                        </div>
                      </td>
                    </tr>
                  )}
                </Fragment>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}
