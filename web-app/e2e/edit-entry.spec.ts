// Before running this suite, start the FastAPI server:
//   cd server && SQLITE_PATH=/absolute/path/to/porquilo.db uv run fastapi dev --port 8000 src/porquilo/main.py
// The Vite dev server is started automatically by playwright.config.ts.

import { test, expect } from '@playwright/test'
import { authHeaders, ensureAdminSession, loginAsAdmin } from './helpers/auth'

// Tests mutate shared diary state so must not run in parallel
test.describe.configure({ mode: 'serial' })

const API = 'http://localhost:8000'
const today = new Date().toISOString().slice(0, 10)

let foodId: string
let breakfastMealId: string
let adminToken: string

test.beforeAll(async ({ request }) => {
  const admin = await ensureAdminSession(request)
  adminToken = admin.token

  const foodRes = await request.post(`${API}/api/foods`, {
    headers: authHeaders(adminToken),
    data: {
      name: `e2e whole milk ${Date.now()}`,
      nutrients: [
        { nutrient_key: 'calories_kcal', value_per_100: 61 },
        { nutrient_key: 'protein_g',     value_per_100: 3.2 },
        { nutrient_key: 'carbs_g',       value_per_100: 4.8 },
        { nutrient_key: 'fat_g',         value_per_100: 3.3 },
      ],
    },
  })
  expect(foodRes.status()).toBe(201)
  foodId = (await foodRes.json()).id

  const mealsRes = await request.get(`${API}/api/meals`, { headers: authHeaders(adminToken) })
  expect(mealsRes.ok()).toBeTruthy()
  const meals = await mealsRes.json()
  breakfastMealId = meals.find((m: { name: string }) => m.name === 'Breakfast').id
})

test.beforeEach(async ({ request, page }) => {
  // Delete all of today's entries so each test starts clean
  const diaryRes = await request.get(`${API}/api/diary/${today}`, { headers: authHeaders(adminToken) })
  if (diaryRes.ok()) {
    const diary = await diaryRes.json()
    for (const meal of diary.meals ?? []) {
      for (const entry of meal.entries ?? []) {
        await request.delete(`${API}/api/entries/${entry.id}`, { headers: authHeaders(adminToken) })
      }
    }
  }

  // Seed one entry at 250 g
  const entryRes = await request.post(`${API}/api/entries`, {
    headers: authHeaders(adminToken),
    data: {
      food_id: foodId,
      meal_id: breakfastMealId,
      weight_g: 250,
      eaten_at: `${today}T08:30:00`,
      weight_source: 'scale',
      input_method: 'manual',
    },
  })
  expect(entryRes.status()).toBe(201)

  await loginAsAdmin(page)
})

test('clicking an entry row opens EditEntryPanel with pre-filled fields', async ({ page }) => {
  const breakfast = page.locator('[data-testid="meal-section-breakfast"]')
  const entryRow = breakfast.locator('[role="button"]')
  await expect(entryRow).toBeVisible()
  await entryRow.click()

  const drawer = page.locator('[data-testid="edit-entry-drawer"]')
  await expect(drawer).toBeVisible()

  // Weight pre-filled to 250
  await expect(drawer.getByRole('spinbutton')).toHaveValue('250')

  // Meal pre-selected
  await expect(drawer.getByRole('combobox').first()).toHaveValue('scale')

  // Time pre-filled
  await expect(drawer.locator('input[type="time"]')).toBeVisible()
})

test('macro preview updates live as weight changes', async ({ page }) => {
  const breakfast = page.locator('[data-testid="meal-section-breakfast"]')
  await breakfast.getByRole('button').click()

  const drawer = page.locator('[data-testid="edit-entry-drawer"]')
  await expect(drawer.getByText('153')).toBeVisible() // 61 kcal/100g × 250 ≈ 153

  await drawer.getByRole('spinbutton').fill('500')
  await expect(drawer.getByText('305')).toBeVisible() // 61 kcal/100g × 500 ≈ 305
})

test('Save button is disabled when weight is 0', async ({ page }) => {
  const breakfast = page.locator('[data-testid="meal-section-breakfast"]')
  await breakfast.getByRole('button').click()

  const drawer = page.locator('[data-testid="edit-entry-drawer"]')
  await drawer.getByRole('spinbutton').fill('0')

  await expect(drawer.getByRole('button', { name: 'Save' })).toBeDisabled()
})

test('Save updates the entry and diary refetches with new values', async ({ page }) => {
  const breakfast = page.locator('[data-testid="meal-section-breakfast"]')
  await breakfast.getByRole('button').click()

  const drawer = page.locator('[data-testid="edit-entry-drawer"]')
  await drawer.getByRole('spinbutton').fill('500')
  await drawer.getByRole('button', { name: 'Save' }).click()

  // Panel closes and diary shows updated values
  await expect(drawer).toHaveAttribute('data-state', 'closed')
  await expect(breakfast).toContainText('500')
  await expect(breakfast).toContainText('305')
})

test('scrim click closes the panel without saving', async ({ page }) => {
  const breakfast = page.locator('[data-testid="meal-section-breakfast"]')
  await breakfast.getByRole('button').click()

  const drawer = page.locator('[data-testid="edit-entry-drawer"]')
  await drawer.getByRole('spinbutton').fill('999')

  // Click the scrim (the overlay behind the drawer)
  await page.locator('[data-testid="edit-entry-scrim"]').click({ position: { x: 10, y: 10 } })

  await expect(drawer).toHaveAttribute('data-state', 'closed')

  // Diary still shows original 250 g
  await expect(breakfast).toContainText('250')
})

test('Delete entry transitions to confirmation; Cancel returns to edit view', async ({ page }) => {
  const breakfast = page.locator('[data-testid="meal-section-breakfast"]')
  await breakfast.getByRole('button').click()

  const drawer = page.locator('[data-testid="edit-entry-drawer"]')
  await drawer.getByRole('button', { name: 'Delete entry' }).click()

  await expect(drawer.getByText('Delete this entry? This cannot be undone.')).toBeVisible()
  await expect(drawer.getByRole('button', { name: 'Confirm delete' })).toBeVisible()

  // Cancel returns to edit view
  await drawer.getByRole('button', { name: 'Cancel' }).click()
  await expect(drawer.getByRole('button', { name: 'Save' })).toBeVisible()
  await expect(drawer.getByRole('button', { name: 'Delete entry' })).toBeVisible()
})

test('Confirm delete removes the entry and diary refetches', async ({ page }) => {
  const breakfast = page.locator('[data-testid="meal-section-breakfast"]')
  await breakfast.getByRole('button').click()

  const drawer = page.locator('[data-testid="edit-entry-drawer"]')
  await drawer.getByRole('button', { name: 'Delete entry' }).click()
  await drawer.getByRole('button', { name: 'Confirm delete' }).click()

  // Panel closes and entry is gone from the diary
  await expect(drawer).toHaveAttribute('data-state', 'closed')
  await expect(breakfast.getByText('+ Add food')).toBeVisible()
  await expect(breakfast).not.toContainText('250')
})
