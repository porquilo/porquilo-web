import { test, expect } from '@playwright/test';

const fmt = (d: Date) =>
  new Intl.DateTimeFormat('en-US', { weekday: 'long', month: 'long', day: 'numeric' }).format(d);

test.describe('Application Navigation Tests', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('should navigate properly between all main sections', async ({ page }) => {
    await expect(page.getByText('Today')).toBeVisible();

    await page.getByRole('button', { name: 'Library' }).click();
    await expect(page.getByRole('heading', { name: 'Library' })).toBeVisible();

    await page.getByRole('button', { name: 'Today' }).click();
    await expect(page.getByText('Today')).toBeVisible();

    await page.getByRole('button', { name: 'Reports' }).click();
    await expect(page.locator('span').filter({ hasText: /^Reports$/ })).toBeVisible();

    await page.getByRole('button', { name: 'Today' }).click();
    await expect(page.getByText('Today')).toBeVisible();

    await page.getByRole('button', { name: 'Settings' }).click();
    await expect(page.getByRole('heading', { name: 'Settings' })).toBeVisible();

    await page.getByRole('button', { name: 'Today' }).click();
    await expect(page.getByText('Today')).toBeVisible();
  });

  test('should maintain state when navigating between sections', async ({ page }) => {
    await expect(page.getByText('Today')).toBeVisible();

    await page.getByRole('button', { name: 'Library' }).click();
    await expect(page.getByRole('heading', { name: 'Library' })).toBeVisible();

    await page.getByRole('button', { name: 'Today' }).click();
    await expect(page.getByText('Today')).toBeVisible();
  });

  test('should handle date navigation correctly', async ({ page }) => {
    await expect(page.getByText('Today')).toBeVisible();

    const today = new Date();
    const nextDate = new Date(today);
    nextDate.setDate(nextDate.getDate() + 1);

    await page.locator('[data-testid="next-day"]').click();
    await expect(page.getByRole('heading', { name: fmt(nextDate) })).toBeVisible();
  });
});
