import { createContext, useContext, useEffect, useState } from 'react'
import type { ReactNode } from 'react'
import { setToken } from '../api/client'
import { login as apiLogin, logout as apiLogout } from '../api/auth'
import { getSetupStatus, initSetup } from '../api/setup'
import { getProfile, updateProfile } from '../api/profile'
import type { AuthUser } from '../types/api'

// Best-effort: keeps User.timezone in sync with the browser's IANA zone so the
// server can bucket diary entries by the user's actual local calendar day.
// Errors are swallowed — a stale/missing timezone just falls back to UTC server-side.
async function syncBrowserTimezone(): Promise<void> {
  try {
    const detected = Intl.DateTimeFormat().resolvedOptions().timeZone
    const profile = await getProfile()
    if (profile.timezone !== detected) {
      await updateProfile({ timezone: detected })
    }
  } catch {
    // ignore — best-effort sync
  }
}

interface AuthContextValue {
  user: AuthUser | null
  token: string | null
  initialized: boolean | null
  isLoading: boolean
  login: (username: string, password: string) => Promise<void>
  completeSetup: (username: string, password: string, name?: string) => Promise<void>
  logout: () => Promise<void>
}

const AuthContext = createContext<AuthContextValue>({
  user: null,
  token: null,
  initialized: null,
  isLoading: true,
  login: async () => {},
  completeSetup: async () => {},
  logout: async () => {},
})

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null)
  const [token, setTokenState] = useState<string | null>(null)
  const [initialized, setInitialized] = useState<boolean | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    async function init() {
      try {
        const status = await getSetupStatus()
        setInitialized(status.initialized)
        if (status.initialized) {
          const storedToken = localStorage.getItem('porquilo_token')
          const storedUser = localStorage.getItem('porquilo_user')
          if (storedToken && storedUser) {
            try {
              const parsedUser = JSON.parse(storedUser) as AuthUser
              setToken(storedToken)
              setTokenState(storedToken)
              // Awaited so the diary view can't fetch under a stale/unset
              // timezone before this resolves — see syncBrowserTimezone above.
              await syncBrowserTimezone()
              setUser(parsedUser)
            } catch {
              localStorage.removeItem('porquilo_token')
              localStorage.removeItem('porquilo_user')
            }
          }
        }
      } catch {
        setInitialized(true)
      } finally {
        setIsLoading(false)
      }
    }
    void init()
  }, [])

  useEffect(() => {
    function handleUnauthorized() {
      localStorage.removeItem('porquilo_token')
      localStorage.removeItem('porquilo_user')
      setToken(null)
      setTokenState(null)
      setUser(null)
    }
    window.addEventListener('porquilo:unauthorized', handleUnauthorized)
    return () => window.removeEventListener('porquilo:unauthorized', handleUnauthorized)
  }, [])

  async function login(username: string, password: string): Promise<void> {
    const result = await apiLogin(username, password)
    localStorage.setItem('porquilo_token', result.token)
    localStorage.setItem('porquilo_user', JSON.stringify(result.user))
    setToken(result.token)
    setTokenState(result.token)
    await syncBrowserTimezone()
    setUser(result.user)
  }

  async function completeSetup(username: string, password: string, name?: string): Promise<void> {
    const result = await initSetup(username, password, name)
    localStorage.setItem('porquilo_token', result.token)
    localStorage.setItem('porquilo_user', JSON.stringify(result.user))
    setToken(result.token)
    setTokenState(result.token)
    await syncBrowserTimezone()
    setUser(result.user)
    setInitialized(true)
  }

  async function logout(): Promise<void> {
    try {
      await apiLogout()
    } catch {
      // best-effort — ignore server errors on logout
    }
    setToken(null)
    localStorage.removeItem('porquilo_token')
    localStorage.removeItem('porquilo_user')
    setTokenState(null)
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, token, initialized, isLoading, login, completeSetup, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth(): AuthContextValue {
  return useContext(AuthContext)
}
