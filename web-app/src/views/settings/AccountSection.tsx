import { useState } from 'react'
import type { CSSProperties, FormEvent } from 'react'
import { useAuth } from '../../contexts/AuthContext'
import { useChangePassword } from '../../hooks/useAuth'
import { useToast } from '../../contexts/ToastContext'
import { Button } from '../../components/Button'
import UserManagementPanel from './UserManagementPanel'

const inputStyle: CSSProperties = {
  padding: '7px 10px',
  background: 'var(--bg-sunken)',
  border: '1px solid var(--border-soft)',
  borderRadius: 8,
  fontSize: 13,
  color: 'var(--fg1)',
  outline: 'none',
  width: '100%',
  fontFamily: 'var(--font-body)',
  boxSizing: 'border-box',
}

const rowStyle: CSSProperties = {
  display: 'grid',
  gridTemplateColumns: '160px 1fr',
  gap: 12,
  padding: '6px 0',
  borderBottom: '1px dashed var(--border-soft)',
  alignItems: 'center',
}

const cardStyle: CSSProperties = {
  background: 'var(--bg-elevated)',
  border: '1px solid var(--border)',
  borderRadius: 14,
  boxShadow: 'var(--shadow-2)',
  padding: '18px 20px',
  display: 'flex',
  flexDirection: 'column',
  gap: 14,
}

const cardHeadStyle: CSSProperties = {
  fontFamily: 'var(--font-display)',
  fontStyle: 'italic',
  fontSize: 20,
  fontVariationSettings: "'opsz' 28",
  fontWeight: 400,
  color: 'var(--fg1)',
  lineHeight: 1.2,
}

function PasswordChangeForm() {
  const changePassword = useChangePassword()
  const { setToast } = useToast()
  const [current, setCurrent] = useState('')
  const [next, setNext] = useState('')
  const [confirm, setConfirm] = useState('')
  const [error, setError] = useState<string | null>(null)

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    if (next !== confirm) {
      setError('New passwords do not match')
      return
    }
    setError(null)
    try {
      await changePassword.mutateAsync({ currentPassword: current, newPassword: next })
      setToast('Password updated')
      setCurrent('')
      setNext('')
      setConfirm('')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Update failed')
    }
  }

  return (
    <form
      onSubmit={(e) => void handleSubmit(e)}
      style={{ display: 'flex', flexDirection: 'column', gap: 8 }}
    >
      <div style={rowStyle}>
        <span style={{ fontSize: 12, color: 'var(--fg3)' }}>Current password</span>
        <input
          type="password"
          value={current}
          onChange={e => setCurrent(e.target.value)}
          autoComplete="current-password"
          style={inputStyle}
        />
      </div>
      <div style={rowStyle}>
        <span style={{ fontSize: 12, color: 'var(--fg3)' }}>New password</span>
        <input
          type="password"
          value={next}
          onChange={e => setNext(e.target.value)}
          autoComplete="new-password"
          style={inputStyle}
        />
      </div>
      <div style={{ ...rowStyle, borderBottom: 'none' }}>
        <span style={{ fontSize: 12, color: 'var(--fg3)' }}>Confirm new password</span>
        <input
          type="password"
          value={confirm}
          onChange={e => setConfirm(e.target.value)}
          autoComplete="new-password"
          style={inputStyle}
        />
      </div>
      {error !== null && (
        <div style={{ fontSize: 12, color: 'var(--danger-fg)', paddingLeft: 2 }}>{error}</div>
      )}
      <div style={{ marginTop: 4 }}>
        <Button type="submit" variant="primary" disabled={changePassword.isPending}>
          {changePassword.isPending ? 'Updating…' : 'Update password'}
        </Button>
      </div>
    </form>
  )
}

export default function AccountSection() {
  const { user, logout } = useAuth()

  if (user === null) return null

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      {/* Account card */}
      <div style={cardStyle}>
        <div style={cardHeadStyle}>Account</div>

        <div style={rowStyle}>
          <span style={{ fontSize: 12, color: 'var(--fg3)' }}>Username</span>
          <span style={{
            fontFamily: 'var(--font-mono)',
            fontSize: 13,
            color: 'var(--fg1)',
          }}>
            {user.username}
          </span>
        </div>

        <div>
          <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--fg2)', marginBottom: 10 }}>
            Change password
          </div>
          <PasswordChangeForm />
        </div>

        <div style={{ paddingTop: 4, borderTop: '1px dashed var(--border-soft)' }}>
          <Button variant="secondary" onClick={() => void logout()}>
            Log out
          </Button>
        </div>
      </div>

      {/* Admin: household accounts */}
      {user.role === 'admin' && (
        <div style={cardStyle}>
          <div style={cardHeadStyle}>Household accounts</div>
          <UserManagementPanel />
        </div>
      )}
    </div>
  )
}
