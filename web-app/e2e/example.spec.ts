import { test, expect } from '@playwright/test';

test('basic navigation test', async ({ page }) => {
  await page.goto('/');
  
  // Check that the app loaded correctly
  await expect(page.getByText('Today')).toBeVisible();
  await expect(page.getByRole('button', { name: 'Log food' })).toBeVisible();
  
  // Check that we have the sidebar
  await expect(page.getByRole('button', { name: 'Library' })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Reports' })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Settings' })).toBeVisible();
});