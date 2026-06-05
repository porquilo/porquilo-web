import { test, expect } from '@playwright/test';

test.describe('Meal and Recipe Creation Tests', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('should navigate to library and show Add custom food button', async ({ page }) => {
    await page.getByRole('button', { name: 'Library' }).click();
    await expect(page.getByRole('heading', { name: 'Library' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Add custom food' })).toBeVisible();
  });

  test('should open quick log panel and accept search input', async ({ page }) => {
    await expect(page.getByText('Today')).toBeVisible();

    await page.getByRole('button', { name: 'Log food' }).click();
    await expect(page.getByText('Quick log')).toBeVisible();

    const searchInput = page.getByPlaceholder('What did you eat?');
    await expect(searchInput).toBeVisible();
    await searchInput.fill('bread');
    await expect(searchInput).toHaveValue('bread');
  });

  test('should access library from sidebar', async ({ page }) => {
    await expect(page.getByText('Today')).toBeVisible();

    await page.getByRole('button', { name: 'Library' }).click();
    await expect(page.getByRole('heading', { name: 'Library' })).toBeVisible();
  });
});
