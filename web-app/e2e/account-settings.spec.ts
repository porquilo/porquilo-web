import { test, expect, request } from '@playwright/test'
import { API_BASE_URL, createMemberUser, ensureAdminSession, postWithRetry, submitLoginForm } from './helpers/auth'

let memberUsername: string
let memberPassword: string

test.beforeAll(async () => {
  const api = await request.newContext({ baseURL: API_BASE_URL })
  const admin = await ensureAdminSession(api)
  // Use a throwaway member account here, not the shared admin, so changing its
  // password doesn't disturb the admin credentials other specs rely on.
  const member = await createMemberUser(api, admin.token, { username: `e2e_account_${Date.now()}` })
  memberUsername = member.username
  memberPassword = member.password
  await api.dispose()
})

// Single test (one login) covering the member's self-service password job:
// rejecting a mismatched confirmation, then a real update that takes effect.
// /api/auth/token is shared and rate-limited across the whole e2e suite, so this
// keeps the number of times this spec hits it to a minimum.
test('member can change their own password, with mismatch rejected client-side', async ({ page }) => {
  await page.goto('/')
  await submitLoginForm(page, memberUsername, memberPassword)
  await expect(page.getByRole('button', { name: 'Log food' })).toBeVisible()

  await page.getByRole('button', { name: 'Settings' }).click()

  // Mismatched confirmation is rejected without hitting the API
  await page.getByText('Current password').locator('xpath=following-sibling::input').fill(memberPassword)
  await page.getByText('New password', { exact: true }).locator('xpath=following-sibling::input').fill('AttemptOne!789')
  await page.getByText('Confirm new password').locator('xpath=following-sibling::input').fill('AttemptTwo!789')
  await page.getByRole('button', { name: 'Update password' }).click()

  await expect(page.getByText('New passwords do not match')).toBeVisible()
  await expect(page.getByText('Password updated')).not.toBeVisible()

  // A real update with matching passwords succeeds
  const newPassword = 'NewE2ePass!456'
  await page.getByText('Current password').locator('xpath=following-sibling::input').fill(memberPassword)
  await page.getByText('New password', { exact: true }).locator('xpath=following-sibling::input').fill(newPassword)
  await page.getByText('Confirm new password').locator('xpath=following-sibling::input').fill(newPassword)
  await page.getByRole('button', { name: 'Update password' }).click()

  await expect(page.getByText('Password updated')).toBeVisible()

  // Verify the new password took effect server-side, without spending another
  // UI login attempt against the rate-limited endpoint.
  const api = await request.newContext({ baseURL: API_BASE_URL })
  const loginRes = await postWithRetry(api, '/api/auth/token', { username: memberUsername, password: newPassword })
  expect(loginRes.ok()).toBeTruthy()
  await api.dispose()
})
