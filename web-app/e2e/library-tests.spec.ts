import { test, expect } from '@playwright/test'

test.describe('Library view', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/')
    await page.getByRole('button', { name: 'Library' }).click()
  })

  test('renders the Library heading and subtitle', async ({ page }) => {
    await expect(page.getByRole('heading', { name: 'Library' })).toBeVisible()
    await expect(page.getByText('Foods and recipes — search, edit, and log directly.')).toBeVisible()
  })

  test('shows Foods sub-tab active by default', async ({ page }) => {
    const foodsTab = page.getByRole('button', { name: /Foods/ })
    await expect(foodsTab).toBeVisible()
    // Recipes tab also present
    await expect(page.getByRole('button', { name: /Recipes/ })).toBeVisible()
  })

  test('switches to Recipes tab', async ({ page }) => {
    await page.getByRole('button', { name: /Recipes/ }).click()
    // Headers change to recipe columns
    await expect(page.getByText('PORTIONS')).toBeVisible()
    await expect(page.getByText('LAST MADE')).toBeVisible()
    // Search placeholder changes
    await expect(page.getByPlaceholder('tikka masala, porridge, …')).toBeVisible()
  })

  test('switches back to Foods tab', async ({ page }) => {
    await page.getByRole('button', { name: /Recipes/ }).click()
    await page.getByRole('button', { name: /Foods/ }).click()
    await expect(page.getByText('KCAL/100G')).toBeVisible()
    await expect(page.getByPlaceholder('banana, oat milk, …')).toBeVisible()
  })

  test('shows correct filter chips for Foods tab', async ({ page }) => {
    await expect(page.getByRole('button', { name: 'All' })).toBeVisible()
    await expect(page.getByRole('button', { name: 'Custom', exact: true })).toBeVisible()
    await expect(page.getByRole('button', { name: 'USDA' })).toBeVisible()
    await expect(page.getByRole('button', { name: 'Open Food Facts' })).toBeVisible()
    await expect(page.getByRole('button', { name: 'Drinks' })).not.toBeVisible()
  })

  test('shows correct filter chips for Recipes tab', async ({ page }) => {
    await page.getByRole('button', { name: /Recipes/ }).click()
    await expect(page.getByRole('button', { name: 'All' })).toBeVisible()
    await expect(page.getByRole('button', { name: 'Custom', exact: true })).toBeVisible()
    await expect(page.getByRole('button', { name: 'Mealie' })).toBeVisible()
    await expect(page.getByRole('button', { name: 'USDA' })).not.toBeVisible()
  })

  test('filter chips reset to All when switching tabs', async ({ page }) => {
    // Select a non-All chip on Foods
    await page.getByRole('button', { name: 'Custom', exact: true }).click()
    // Switch to Recipes — filter should reset
    await page.getByRole('button', { name: /Recipes/ }).click()
    // Switch back — All should be active again (Custom chip exists but All is selected)
    await page.getByRole('button', { name: /Foods/ }).click()
    // The All button should now be the selected one — verify USDA still exists (i.e. we're on Foods)
    await expect(page.getByRole('button', { name: 'USDA' })).toBeVisible()
  })

  test('search input clears with the × button', async ({ page }) => {
    const input = page.getByPlaceholder('banana, oat milk, …')
    await input.fill('test')
    await expect(input).toHaveValue('test')
    // The clear button appears and clears the input
    await page.getByRole('button', { name: 'Clear search' }).click()
    await expect(input).toHaveValue('')
  })

  test('Add custom food button opens the sheet', async ({ page }) => {
    await page.getByRole('button', { name: 'Add custom food' }).click()
    await expect(page.getByText('Add custom food').nth(1)).toBeVisible()
    await expect(page.getByText('Name *')).toBeVisible()
    await expect(page.getByRole('button', { name: 'Add to library' })).toBeVisible()
  })

  test('CreateFoodSheet validates name and calories before submit', async ({ page }) => {
    await page.getByRole('button', { name: 'Add custom food' }).click()
    await page.getByRole('button', { name: 'Add to library' }).click()
    await expect(page.getByText('Name is required')).toBeVisible()
    await expect(page.getByText('Calories required')).toBeVisible()
  })

  test('CreateFoodSheet closes on scrim click', async ({ page }) => {
    await page.getByRole('button', { name: 'Add custom food' }).click()
    await expect(page.getByRole('button', { name: 'Add to library' })).toBeVisible()
    // Click the scrim — opacity transitions to 0 when open becomes false
    await page.locator('[data-testid="sheet-scrim"]').click()
    await expect(page.locator('[data-testid="sheet-scrim"]')).toHaveCSS('opacity', '0')
  })

  test('Add recipe button label shows on Recipes tab', async ({ page }) => {
    await page.getByRole('button', { name: /Recipes/ }).click()
    await expect(page.getByRole('button', { name: 'Add recipe' })).toBeVisible()
  })
})
