import { test, expect } from '@playwright/test'

test('renders Today view on load', async ({ page }) => {
  await page.goto('/')
  await expect(page.getByRole('button', { name: 'Log food' })).toBeVisible()
})

test('can navigate to all four tabs', async ({ page }) => {
  await page.goto('/')

  await page.getByRole('button', { name: 'Library' }).click()
  await expect(page.getByRole('heading', { name: 'Library' })).toBeVisible()

  await page.getByRole('button', { name: 'Reports' }).click()
  await expect(page.getByRole('heading', { name: 'Reports' })).toBeVisible()

  await page.getByRole('button', { name: 'Settings' }).click()
  await expect(page.getByRole('heading', { name: 'Settings' })).toBeVisible()

  await page.getByRole('button', { name: 'Today' }).click()
  await expect(page.getByRole('button', { name: 'Log food' })).toBeVisible()
})

test('date navigation changes the displayed date', async ({ page }) => {
  await page.goto('/')

  const todayLabel = new Intl.DateTimeFormat('en-US', {
    weekday: 'long',
    month: 'long',
    day: 'numeric',
  }).format(new Date())

  await expect(page.getByRole('heading', { level: 1 })).toContainText(todayLabel)

  await page.locator('[data-testid="next-day"]').click()

  await expect(page.getByRole('heading', { level: 1 })).not.toContainText(todayLabel)
})

test('Quick log panel opens and can be closed', async ({ page }) => {
  await page.goto('/')
  await page.getByRole('button', { name: 'Log food' }).click()

  await expect(page.getByText('Quick log')).toBeVisible()

  await page.getByRole('button', { name: 'Close' }).click()

  await expect(page.getByText('Quick log')).not.toBeVisible()
})
