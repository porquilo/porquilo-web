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

export default function LoginView() {
  const { login } = useAuth()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      await login(username, password)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed')
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
      <div style={{ width: '100%', maxWidth: 360, padding: '0 24px' }}>
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
          margin: '0 0 24px',
          textAlign: 'center',
          lineHeight: 1.2,
        }}>
          Log in
        </h1>
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
            autoComplete="current-password"
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
            {submitting ? 'Logging in…' : 'Log in'}
          </Button>
        </form>
      </div>
    </div>
  )
}
