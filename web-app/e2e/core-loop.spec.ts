// Before running the suite, start the FastAPI server separately:
//   cd server && uv run uvicorn porquilo.main:app --port 8000
// The Vite dev server is started automatically by playwright.config.ts:
//   cd web-app && npm run dev

import { test, expect, request } from '@playwright/test'

let foodName: string

test.beforeAll(async () => {
  const api = await request.newContext({ baseURL: 'http://localhost:8000' })
  foodName = `e2e banana ${Date.now()}`
  const res = await api.post('/api/foods', {
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
  await page.goto('/')
  await page.getByRole('button', { name: 'Log food' }).click()
  await expect(page.getByText('Quick log')).toBeVisible()

  await page.getByPlaceholder('What did you eat?').fill(foodName)

  const foodButton = page.getByRole('button', { name: new RegExp(foodName) })
  await expect(foodButton).toBeVisible()
  await foodButton.click()

  await expect(page.getByText(foodName)).toBeVisible()

  const amountInput = page.getByRole('spinbutton')
  await amountInput.fill('150')

  // 89 kcal/100g × 1.5 = 133.5 → rounds to 134
  await expect(page.getByText('134')).toBeVisible()

  await page.getByRole('button', { name: 'Log it' }).click()

  const diaryCard = page.locator('[data-testid="diary-card"]')
  await expect(diaryCard.getByText(foodName)).toBeVisible()
  await expect(diaryCard.getByText('134 kcal')).toBeVisible()
})

test('Log it is disabled when amount is 0', async ({ page }) => {
  await page.goto('/')
  await page.getByRole('button', { name: 'Log food' }).click()
  await expect(page.getByText('Quick log')).toBeVisible()

  await page.getByPlaceholder('What did you eat?').fill(foodName)

  const foodButton = page.getByRole('button', { name: new RegExp(foodName) })
  await expect(foodButton).toBeVisible()
  await foodButton.click()

  const amountInput = page.getByRole('spinbutton')
  await amountInput.fill('0')

  await expect(page.getByRole('button', { name: 'Log it' })).toBeDisabled()
})
