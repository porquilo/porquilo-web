import { useState } from 'react'
import type { CSSProperties, FormEvent } from 'react'
import { useAuth } from '../contexts/AuthContext'
import { WLogoMark } from '../components/LogoMark'
import { Button } from '../components/Button'

const inputStyle: CSSProperties = {
  padding: '9px 12px',
  background: 'var(--bg-sunken)',
  border: '1px solid var(--border-soft)',
  borderRadius: 8,
  fontSize: 14,
  color: 'var(--fg1)',
  outline: 'none',
  width: '100%',
  fontFamily: 'var(--font-body)',
  boxSizing: 'border-box',
}

export default function SetupWizardView() {
  const { completeSetup } = useAuth()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [displayName, setDisplayName] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    if (password !== confirmPassword) {
      setError('Passwords do not match')
      return
    }
    setError(null)
    setSubmitting(true)
    try {
      await completeSetup(username, password, displayName.trim() || undefined)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Setup failed')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      height: '100vh',
      background: 'var(--bg)',
    }}>
      <div style={{ width: '100%', maxWidth: 400, padding: '0 24px' }}>
        <div style={{ display: 'flex', justifyContent: 'center', marginBottom: 32 }}>
          <WLogoMark size={48} />
        </div>
        <h1 style={{
          fontFamily: 'var(--font-display)',
          fontStyle: 'italic',
          fontVariationSettings: "'opsz' 36",
          fontSize: 28,
          fontWeight: 400,
          color: 'var(--fg1)',
          margin: '0 0 8px',
          textAlign: 'center',
          lineHeight: 1.2,
        }}>
          Welcome to Porquilo
        </h1>
        <p style={{
          fontSize: 14,
          color: 'var(--fg3)',
          textAlign: 'center',
          margin: '0 0 24px',
          lineHeight: 1.5,
        }}>
          Create your admin account to get started.
        </p>
        <form
          onSubmit={(e) => void handleSubmit(e)}
          style={{ display: 'flex', flexDirection: 'column', gap: 12 }}
        >
          <input
            autoFocus
            type="text"
            placeholder="Username"
            value={username}
            onChange={e => setUsername(e.target.value)}
            autoComplete="username"
            style={inputStyle}
          />
          <input
            type="password"
            placeholder="Password"
            value={password}
            onChange={e => setPassword(e.target.value)}
            autoComplete="new-password"
            style={inputStyle}
          />
          <input
            type="password"
            placeholder="Confirm password"
            value={confirmPassword}
            onChange={e => setConfirmPassword(e.target.value)}
            autoComplete="new-password"
            style={inputStyle}
          />
          <input
            type="text"
            placeholder="Your name (optional)"
            value={displayName}
            onChange={e => setDisplayName(e.target.value)}
            autoComplete="name"
            style={inputStyle}
          />
          {error !== null && (
            <div style={{ fontSize: 13, color: 'var(--danger-fg)' }}>
              {error}
            </div>
          )}
          <Button
            type="submit"
            variant="primary"
            disabled={submitting}
            style={{ marginTop: 4, width: '100%', justifyContent: 'center' }}
          >
            {submitting ? 'Creating account…' : 'Create account'}
          </Button>
        </form>
      </div>
    </div>
  )
}
