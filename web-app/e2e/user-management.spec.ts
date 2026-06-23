import { test, expect, request } from '@playwright/test'
import { API_BASE_URL, createMemberUser, ensureAdminSession, loginAsAdmin, postWithRetry } from './helpers/auth'

test.beforeEach(async ({ page }) => {
  await loginAsAdmin(page)
  await page.getByRole('button', { name: 'Settings' }).click()
})

test('admin can add a household member', async ({ page }) => {
  const username = `e2e_new_member_${Date.now()}`

  await page.getByRole('button', { name: 'Add account' }).click()
  await page.getByPlaceholder('Username').fill(username)
  await page.getByPlaceholder('Password').fill('NewMemberPass!123')
  await page.getByPlaceholder('Display name (optional)').fill('E2E New Member')
  await page.getByRole('combobox').selectOption('member')
  await page.getByRole('button', { name: 'Create account' }).click()

  await expect(page.getByText('Account created')).toBeVisible()
  const row = page.locator('tr', { hasText: username })
  await expect(row).toContainText('member')
  await expect(row).toContainText('Active')
})

test('admin can reset a member\'s password', async ({ page }) => {
  const api = await request.newContext({ baseURL: API_BASE_URL })
  const admin = await ensureAdminSession(api)
  const member = await createMemberUser(api, admin.token, { username: `e2e_reset_${Date.now()}` })

  await page.reload()
  await page.getByRole('button', { name: 'Settings' }).click()

  const row = page.locator('tr', { hasText: member.username })
  await row.getByRole('button', { name: 'Reset password' }).click()
  await row.getByPlaceholder('New password').fill('ResetByAdmin!456')
  await row.getByRole('button', { name: 'Set' }).click()

  await expect(page.getByText('Password reset')).toBeVisible()

  const loginRes = await postWithRetry(api, '/api/auth/token', {
    username: member.username,
    password: 'ResetByAdmin!456',
  })
  expect(loginRes.ok()).toBeTruthy()
  await api.dispose()
})

test('admin can deactivate and reactivate a member', async ({ page }) => {
  const api = await request.newContext({ baseURL: API_BASE_URL })
  const admin = await ensureAdminSession(api)
  const member = await createMemberUser(api, admin.token, { username: `e2e_deactivate_${Date.now()}` })

  await page.reload()
  await page.getByRole('button', { name: 'Settings' }).click()

  const row = page.locator('tr', { hasText: member.username })
  await row.getByRole('button', { name: 'Deactivate' }).click()

  await expect(page.getByText('Account deactivated')).toBeVisible()
  await expect(row).toContainText('Deactivated')
  await expect(row.getByRole('button', { name: 'Reactivate' })).toBeVisible()

  const deactivatedLoginRes = await postWithRetry(api, '/api/auth/token', {
    username: member.username,
    password: member.password,
  })
  expect(deactivatedLoginRes.status()).toBe(403)
  const body = (await deactivatedLoginRes.json()) as { error: { code: string } }
  expect(body.error.code).toBe('account_deactivated')

  await row.getByRole('button', { name: 'Reactivate' }).click()
  await expect(page.getByText('Account reactivated')).toBeVisible()

  const reactivatedLoginRes = await postWithRetry(api, '/api/auth/token', {
    username: member.username,
    password: member.password,
  })
  expect(reactivatedLoginRes.ok()).toBeTruthy()
  await api.dispose()
})
