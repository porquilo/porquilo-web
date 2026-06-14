import { test, expect } from '@playwright/test'

test.beforeEach(async ({ request, page }) => {
  // Clear today's diary entries so meals appear empty regardless of test order
  const today = new Date().toISOString().slice(0, 10)
  const res = await request.get(`http://localhost:8000/api/diary/${today}`)
  if (res.ok()) {
    const diary = await res.json()
    for (const meal of diary.meals ?? []) {
      for (const entry of meal.entries ?? []) {
        await request.delete(`http://localhost:8000/api/entries/${entry.id}`)
      }
    }
  }
  await page.goto('/')
})

test('skipping a meal shows Eating after all and hides food controls', async ({ page }) => {
  const breakfast = page.locator('[data-testid="meal-section-breakfast"]')

  await breakfast.getByRole('button', { name: 'Not eating' }).click()

  await expect(breakfast.getByRole('button', { name: 'Eating after all' })).toBeVisible()
  await expect(breakfast.getByRole('button', { name: 'Not eating' })).not.toBeVisible()
  await expect(breakfast.getByText('+ Add food')).not.toBeVisible()

  await breakfast.getByRole('button', { name: 'Eating after all' }).click()
})

test('unskipping a meal restores Add food and Not eating', async ({ page }) => {
  const lunch = page.locator('[data-testid="meal-section-lunch"]')

  await lunch.getByRole('button', { name: 'Not eating' }).click()
  await expect(lunch.getByRole('button', { name: 'Eating after all' })).toBeVisible()

  await lunch.getByRole('button', { name: 'Eating after all' }).click()

  await expect(lunch.getByRole('button', { name: 'Not eating' })).toBeVisible()
  await expect(lunch.getByText('+ Add food')).toBeVisible()
})

test('a skip persists after page reload', async ({ page }) => {
  const dinner = page.locator('[data-testid="meal-section-dinner"]')

  await dinner.getByRole('button', { name: 'Not eating' }).click()
  await expect(dinner.getByRole('button', { name: 'Eating after all' })).toBeVisible()

  await page.reload()

  const dinnerAfterReload = page.locator('[data-testid="meal-section-dinner"]')
  await expect(dinnerAfterReload.getByRole('button', { name: 'Eating after all' })).toBeVisible()

  await dinnerAfterReload.getByRole('button', { name: 'Eating after all' }).click()
})
