import { test, expect } from '@playwright/test';

const fmt = (d: Date) =>
  new Intl.DateTimeFormat('en-US', { weekday: 'long', month: 'long', day: 'numeric' }).format(d);

test.describe('Diary Navigation and Food Entry Tests', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('should navigate between dates in diary', async ({ page }) => {
    await expect(page.getByText('Today')).toBeVisible();

    const today = new Date();
    const tomorrow = new Date(today);
    tomorrow.setDate(tomorrow.getDate() + 1);

    await page.locator('[data-testid="next-day"]').click();
    await expect(page.getByRole('heading', { name: fmt(tomorrow) })).toBeVisible();

    await page.locator('[data-testid="prev-day"]').click();
    await expect(page.getByRole('heading', { name: fmt(today) })).toBeVisible();
  });

  test('should open quick log panel and accept search input', async ({ page }) => {
    await page.getByRole('button', { name: 'Log food' }).click();

    await expect(page.getByText('Quick log')).toBeVisible();

    const searchInput = page.getByPlaceholder('What did you eat?');
    await expect(searchInput).toBeVisible();
    await searchInput.fill('apple');
    await expect(searchInput).toHaveValue('apple');
  });

  test('should navigate between app sections', async ({ page }) => {
    await expect(page.getByText('Today')).toBeVisible();

    await page.getByRole('button', { name: 'Library' }).click();
    await expect(page.getByRole('heading', { name: 'Library' })).toBeVisible();

    await page.getByRole('button', { name: 'Reports' }).click();
    await expect(page.locator('span').filter({ hasText: /^Reports$/ })).toBeVisible();

    await page.getByRole('button', { name: 'Settings' }).click();
    await expect(page.getByRole('heading', { name: 'Settings' })).toBeVisible();

    await page.getByRole('button', { name: 'Today' }).click();
    await expect(page.getByText('Today')).toBeVisible();
  });
});
