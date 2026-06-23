import { test, expect, request } from '@playwright/test'
import {
  ADMIN_PASSWORD,
  ADMIN_USERNAME,
  API_BASE_URL,
  ensureAdminSession,
  loginAsFreshAdmin,
  submitLoginForm,
} from './helpers/auth'

test('first-time setup creates the admin account and logs them in', async ({ page }) => {
  const api = await request.newContext({ baseURL: API_BASE_URL })
  const statusRes = await api.get('/api/setup/status')
  const { initialized } = (await statusRes.json()) as { initialized: boolean }
  await api.dispose()

  // The e2e database persists across runs, and the setup wizard only succeeds
  // once — this test is only meaningful against a genuinely fresh database.
  test.skip(initialized, 'database is already initialized from a previous run')

  await page.goto('/')
  await page.getByPlaceholder('Username').fill(ADMIN_USERNAME)
  await page.getByPlaceholder('Password').fill(ADMIN_PASSWORD)
  await page.getByPlaceholder('Confirm password').fill(ADMIN_PASSWORD)
  await page.getByRole('button', { name: 'Create account' }).click()

  await expect(page.getByRole('button', { name: 'Log food' })).toBeVisible()
})

test('logging in with valid credentials reaches the diary', async ({ page }) => {
  const api = await request.newContext({ baseURL: API_BASE_URL })
  await ensureAdminSession(api)
  await api.dispose()

  await page.goto('/')
  await submitLoginForm(page, ADMIN_USERNAME, ADMIN_PASSWORD)

  await expect(page.getByRole('button', { name: 'Log food' })).toBeVisible()
})

test('logging in with the wrong password shows an error', async ({ page }) => {
  const api = await request.newContext({ baseURL: API_BASE_URL })
  await ensureAdminSession(api)
  await api.dispose()

  await page.goto('/')
  await submitLoginForm(page, ADMIN_USERNAME, 'definitely-the-wrong-password')

  await expect(page.getByRole('heading', { name: 'Log in' })).toBeVisible()
  await expect(page.getByText("That username and password don't match.")).toBeVisible()
  await expect(page.getByRole('button', { name: 'Log food' })).not.toBeVisible()
})

test('logging out returns to the login screen', async ({ page }) => {
  // A fresh login (not the shared cached session) — logging out revokes the
  // token, which would otherwise break every other spec relying on the cache.
  await loginAsFreshAdmin(page)

  await page.getByRole('button', { name: 'Settings' }).click()
  await page.getByRole('button', { name: 'Log out' }).click()

  await expect(page.getByRole('heading', { name: 'Log in' })).toBeVisible()
})
