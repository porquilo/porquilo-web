// Before running the suite, start the FastAPI server separately:
//   cd server && uv run uvicorn porquilo.main:app --port 8000
// The Vite dev server is started automatically by playwright.config.ts:
//   cd web-app && npm run dev

import { test, expect, request } from '@playwright/test'
import { authHeaders, ensureAdminSession, loginAsAdmin } from './helpers/auth'

let foodName: string

test.beforeAll(async () => {
  const api = await request.newContext({ baseURL: 'http://localhost:8000' })
  const admin = await ensureAdminSession(api)
  foodName = `e2e banana ${Date.now()}`
  const res = await api.post('/api/foods', {
    headers: authHeaders(admin.token),
    data: {
      name: foodName,
      source: 'custom',
      nutrients: [
        { nutrient_key: 'calories_kcal', value_per_100: 89 },
        { nutrient_key: 'protein_g',     value_per_100: 1.1 },
        { nutrient_key: 'carbs_g',       value_per_100: 23  },
        { nutrient_key: 'fat_g',         value_per_100: 0.3 },
      ],
    },
  })
  expect(res.status()).toBe(201)
  await api.dispose()
})

test('logs a food via quick log and the entry appears in the diary', async ({ page }) => {
  await loginAsAdmin(page)
  await page.getByRole('button', { name: 'Log food' }).click()
  const drawer = page.locator('[data-testid="quick-log-drawer"]')
  await expect(drawer.getByText('Quick log')).toBeVisible()

  await page.getByPlaceholder('What did you eat?').fill(foodName)

  const foodButton = drawer.getByRole('button', { name: new RegExp(foodName) })
  await expect(foodButton).toBeVisible()
  await foodButton.click()

  await expect(page.getByText(foodName)).toBeVisible()

  await drawer.getByRole('spinbutton').fill('150')

  // 89 kcal/100g × 1.5 = 133.5 → rounds to 134
  await expect(drawer.getByText('134', { exact: true })).toBeVisible()

  await drawer.getByRole('button', { name: 'Log it' }).click()

  const diaryCard = page.locator('[data-testid="diary-card"]')
  await expect(diaryCard).toContainText(foodName)
  await expect(diaryCard).toContainText('~134 kcal')
})

test('Log it is disabled when amount is 0', async ({ page }) => {
  await loginAsAdmin(page)
  await page.getByRole('button', { name: 'Log food' }).click()
  const drawer = page.locator('[data-testid="quick-log-drawer"]')
  await expect(drawer.getByText('Quick log')).toBeVisible()

  await page.getByPlaceholder('What did you eat?').fill(foodName)

  const foodButton = drawer.getByRole('button', { name: new RegExp(foodName) })
  await expect(foodButton).toBeVisible()
  await foodButton.click()

  await drawer.getByRole('spinbutton').fill('0')

  await expect(drawer.getByRole('button', { name: 'Log it' })).toBeDisabled()
})
