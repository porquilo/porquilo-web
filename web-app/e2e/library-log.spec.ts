import { test, expect, request } from '@playwright/test'
import { authHeaders, ensureAdminSession, loginAsAdmin } from './helpers/auth'

let foodName: string

test.beforeAll(async () => {
  const api = await request.newContext({ baseURL: 'http://localhost:8000' })
  const admin = await ensureAdminSession(api)
  foodName = `e2e oat milk ${Date.now()}`
  const res = await api.post('/api/foods', {
    headers: authHeaders(admin.token),
    data: {
      name: foodName,
      source: 'custom',
      nutrients: [
        { nutrient_key: 'calories_kcal', value_per_100: 40  },
        { nutrient_key: 'protein_g',     value_per_100: 0.4 },
        { nutrient_key: 'carbs_g',       value_per_100: 5   },
        { nutrient_key: 'fat_g',         value_per_100: 1.5 },
      ],
    },
  })
  expect(res.status()).toBe(201)
  await api.dispose()
})

test('food created via API appears in the Library', async ({ page }) => {
  await loginAsAdmin(page)
  await page.getByRole('button', { name: 'Library' }).click()

  await page.getByPlaceholder('banana, oat milk, …').fill(foodName)

  await expect(page.getByText(foodName)).toBeVisible()
})

test('inline log button triggers a toast confirming the log', async ({ page }) => {
  await loginAsAdmin(page)
  await page.getByRole('button', { name: 'Library' }).click()

  await page.getByPlaceholder('banana, oat milk, …').fill(foodName)
  await expect(page.getByText(foodName)).toBeVisible()

  // Scope to the specific food row to avoid strict mode with other rows' inputs
  const foodRow = page.locator('[data-testid="food-row"]').filter({ hasText: foodName })
  await foodRow.getByRole('spinbutton').fill('200')
  await foodRow.getByRole('button', { name: 'Log' }).click()

  await expect(page.getByText(/Logged/)).toBeVisible()
})
