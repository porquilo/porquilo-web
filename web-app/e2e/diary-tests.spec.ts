import { test, expect } from '@playwright/test';

test.describe('Diary Navigation and Food Entry Tests', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('should navigate between dates in diary', async ({ page }) => {
    // Check that we're on the today view
    await expect(page.getByText('Today')).toBeVisible();
    
    // Navigate to next day
    await page.getByRole('button', { name: '>' }).click();
    await page.waitForTimeout(500); // Wait for date change
    
    // Verify date navigation worked
    const currentDate = new Date();
    const tomorrow = new Date(currentDate);
    tomorrow.setDate(tomorrow.getDate() + 1);
    
    const formattedTomorrow = tomorrow.toISOString().split('T')[0];
    await expect(page.getByText(formattedTomorrow)).toBeVisible();
    
    // Navigate back to today  
    await page.getByRole('button', { name: '<' }).click();
    await page.waitForTimeout(500); // Wait for date change
    await expect(page.getByText(new Date().toISOString().split('T')[0])).toBeVisible();
  });

  test('should log food entry successfully', async ({ page }) => {
    // Click the "Log food" button to open quick log panel
    await page.getByRole('button', { name: 'Log food' }).click();
    
    // Wait for the quick log panel to appear
    await expect(page.getByText('Quick Log')).toBeVisible();
    
    // Search for a food item (using a common food like "apple")
    await page.getByPlaceholder('Search foods').fill('apple');
    
    // Wait for search results to appear
    await page.waitForTimeout(1000);
    
    // Select an apple from search results - assuming the first result is what we want
    const firstResult = page.locator('[data-testid="food-search-result"]').first();
    await expect(firstResult).toBeVisible();
    
    // Click on the food to add it to diary (we'll assume clicking the first item works)
    await firstResult.click();
    
    // Verify food was added by checking that the search field is cleared
    await expect(page.getByPlaceholder('Search foods')).toHaveValue('');
    
    // Check that food appears in diary view
    await page.waitForTimeout(1000);
    await expect(page.getByText('apple', { exact: false })).toBeVisible();
  });

  test('should navigate between app sections', async ({ page }) => {
    // Start on Today view
    await expect(page.getByText('Today')).toBeVisible();
    
    // Navigate to Library
    await page.getByRole('button', { name: 'Library' }).click();
    await page.waitForTimeout(500);
    await expect(page.getByText('Library')).toBeVisible();
    
    // Navigate to Reports
    await page.getByRole('button', { name: 'Reports' }).click();
    await page.waitForTimeout(500); 
    await expect(page.getByText('Reports')).toBeVisible();
    
    // Navigate to Settings
    await page.getByRole('button', { name: 'Settings' }).click();
    await page.waitForTimeout(500);
    await expect(page.getByText('Settings')).toBeVisible();
    
    // Return to Today view
    await page.getByRole('button', { name: 'Today' }).click();
    await page.waitForTimeout(500);
    await expect(page.getByText('Today')).toBeVisible();
  });
});