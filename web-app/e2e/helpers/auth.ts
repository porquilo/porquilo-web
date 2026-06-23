import * as fs from 'fs'
import * as os from 'os'
import * as path from 'path'
import type { APIRequestContext, Page } from '@playwright/test'
import { expect, request as playwrightRequest } from '@playwright/test'

export const API_BASE_URL = 'http://localhost:8000'

export const ADMIN_USERNAME = process.env.E2E_ADMIN_USERNAME ?? 'e2e_admin'
export const ADMIN_PASSWORD = process.env.E2E_ADMIN_PASSWORD ?? 'E2eAdmin!Pass123'

// POST /api/auth/token is rate-limited to 10/minute per client IP, shared by every
// e2e worker process and spec. A file-backed cache (rather than a module-level one)
// means the whole suite — across however many parallel workers — bootstraps the
// admin session at most once, instead of once per worker.
const SESSION_CACHE_PATH = path.join(os.tmpdir(), 'porquilo-e2e-admin-session.json')

interface SessionUser {
  id: string
  username: string
  role: 'admin' | 'member'
}

interface Session {
  username: string
  password: string
  token: string
  user: SessionUser
}

// A transient 429 here is expected under e2e load, not a real failure — back off
// and retry rather than failing the test. The limiter window is roughly a minute,
// so this retries long enough to span a window rollover.
export async function postWithRetry(
  api: APIRequestContext,
  path: string,
  data: Record<string, unknown>,
  retries = 4,
) {
  for (let attempt = 0; ; attempt++) {
    const res = await api.post(path, { data })
    if (res.status() !== 429 || attempt >= retries) return res
    await new Promise(resolve => setTimeout(resolve, 5000))
  }
}

function readCachedSession(): Session | null {
  try {
    return JSON.parse(fs.readFileSync(SESSION_CACHE_PATH, 'utf-8')) as Session
  } catch {
    return null
  }
}

function writeCachedSession(session: Session): void {
  fs.writeFileSync(SESSION_CACHE_PATH, JSON.stringify(session))
}

// The e2e database persists across runs and the setup wizard only succeeds once,
// so this must work whether this is the very first run (no users yet) or the
// hundredth (the e2e admin already exists). The cache is also self-healing: if a
// dev wipes their local DB but leaves the cache file behind (e.g. /var/folders
// temp dir on macOS, which survives independently of the app's own DB resets),
// the cached token would otherwise be silently invalid — so it's verified with a
// cheap authenticated call (not rate-limited) before being trusted.
export async function ensureAdminSession(api: APIRequestContext): Promise<Session> {
  const cached = readCachedSession()
  if (cached && cached.username === ADMIN_USERNAME && cached.password === ADMIN_PASSWORD) {
    const probe = await api.get('/api/users', { headers: authHeaders(cached.token) })
    if (probe.ok()) return cached
  }

  const statusRes = await api.get('/api/setup/status')
  if (!statusRes.ok()) {
    throw new Error(`GET /api/setup/status failed: ${statusRes.status()} ${await statusRes.text()}`)
  }
  const { initialized } = (await statusRes.json()) as { initialized: boolean }

  if (!initialized) {
    const initRes = await postWithRetry(api, '/api/setup/init', {
      username: ADMIN_USERNAME,
      password: ADMIN_PASSWORD,
      name: 'E2E Admin',
    })
    if (!initRes.ok()) {
      throw new Error(`POST /api/setup/init failed: ${initRes.status()} ${await initRes.text()}`)
    }
    const body = (await initRes.json()) as { token: string; user: SessionUser }
    const session = { username: ADMIN_USERNAME, password: ADMIN_PASSWORD, token: body.token, user: body.user }
    writeCachedSession(session)
    return session
  }

  const loginRes = await postWithRetry(api, '/api/auth/token', {
    username: ADMIN_USERNAME,
    password: ADMIN_PASSWORD,
  })
  if (!loginRes.ok()) {
    throw new Error(
      `POST /api/auth/token failed for fixed e2e admin "${ADMIN_USERNAME}": ${loginRes.status()} ${await loginRes.text()}. ` +
        'The setup wizard already ran with different credentials than this suite expects — reset the e2e database or set E2E_ADMIN_USERNAME/E2E_ADMIN_PASSWORD to match.',
    )
  }
  const body = (await loginRes.json()) as { token: string; user: SessionUser }
  const session = { username: ADMIN_USERNAME, password: ADMIN_PASSWORD, token: body.token, user: body.user }
  writeCachedSession(session)
  return session
}

// Navigates the page to an authenticated Today view, bootstrapping the admin
// account first if this is a fresh database.
export async function loginAsAdmin(page: Page): Promise<void> {
  const api = await playwrightRequest.newContext({ baseURL: API_BASE_URL })
  const session = await ensureAdminSession(api)
  await api.dispose()
  await applySession(page, session)
}

// Like loginAsAdmin, but always performs a fresh login instead of reusing the
// shared file-cached session. Use this for tests that revoke their own token
// (e.g. logging out) — doing that with the cached session would invalidate it
// for every other spec still relying on the cache.
export async function loginAsFreshAdmin(page: Page): Promise<void> {
  const api = await playwrightRequest.newContext({ baseURL: API_BASE_URL })
  await ensureAdminSession(api) // make sure the admin account exists at all
  const loginRes = await postWithRetry(api, '/api/auth/token', {
    username: ADMIN_USERNAME,
    password: ADMIN_PASSWORD,
  })
  if (!loginRes.ok()) {
    throw new Error(`POST /api/auth/token failed: ${loginRes.status()} ${await loginRes.text()}`)
  }
  const body = (await loginRes.json()) as { token: string; user: SessionUser }
  await api.dispose()
  await applySession(page, { username: ADMIN_USERNAME, password: ADMIN_PASSWORD, token: body.token, user: body.user })
}

async function applySession(page: Page, session: Session): Promise<void> {
  await page.goto('/')
  await page.evaluate(
    ({ token, user }) => {
      localStorage.setItem('porquilo_token', token)
      localStorage.setItem('porquilo_user', JSON.stringify(user))
    },
    { token: session.token, user: session.user },
  )
  await page.reload()
}

// Drives the actual LoginView form. Retries on the rate-limit error toast since
// /api/auth/token is shared and rate-limited across all e2e workers/specs.
export async function submitLoginForm(page: Page, username: string, password: string, retries = 4): Promise<void> {
  const rateLimitError = page.getByText('Too many attempts. Try again in a few minutes.')

  for (let attempt = 0; ; attempt++) {
    await page.getByPlaceholder('Username').fill(username)
    await page.getByPlaceholder('Password').fill(password)
    await page.getByRole('button', { name: 'Log in' }).click()

    const rateLimited = await expect(rateLimitError)
      .toBeVisible({ timeout: 1500 })
      .then(() => true)
      .catch(() => false)
    if (!rateLimited || attempt >= retries) return

    await page.waitForTimeout(5000)
  }
}

// Protected routes (foods, diary, entries, meals, …) now require a bearer token —
// pass this to every direct backend API call e2e specs make for seeding/cleanup.
export function authHeaders(token: string): Record<string, string> {
  return { Authorization: `Bearer ${token}` }
}

export async function createMemberUser(
  api: APIRequestContext,
  adminToken: string,
  overrides?: { username?: string; password?: string; name?: string; role?: string },
): Promise<{ username: string; password: string; id: string; role: string }> {
  const username = overrides?.username ?? `e2e_member_${Date.now()}`
  const password = overrides?.password ?? 'E2eMember!Pass123'
  const res = await api.post('/api/users', {
    headers: { Authorization: `Bearer ${adminToken}` },
    data: {
      username,
      password,
      name: overrides?.name,
      role: overrides?.role ?? 'member',
    },
  })
  if (!res.ok()) {
    throw new Error(`POST /api/users failed: ${res.status()} ${await res.text()}`)
  }
  const body = (await res.json()) as { id: string; role: string }
  return { username, password, id: body.id, role: body.role }
}
