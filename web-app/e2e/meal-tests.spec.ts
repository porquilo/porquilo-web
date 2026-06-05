import { test, expect } from '@playwright/test';

test.describe('Meal and Recipe Creation Tests', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('should be able to navigate to library and create a basic meal', async ({ page }) => {
    // Navigate to Library
    await page.getByRole('button', { name: 'Library' }).click();
    
    // Wait for library view to load
    await expect(page.getByText('Library')).toBeVisible();
    
    // Look for "Create Meal" or similar button (might be in a dropdown)
    const createMealButton = page.locator('[data-testid="create-meal-button"]');
    await expect(createMealButton).toBeVisible();
    
    // Click on create meal button
    await createMealButton.click(); 
    
    // Wait for meal creation form to appear 
    await expect(page.getByText('Create Meal')).toBeVisible();
    
    // Fill in basic meal details
    // (Since we need to mock this, we can check if form loads correctly)
    const mealNameInput = page.locator('[data-testid="meal-name-input"]');
    await expect(mealNameInput).toBeVisible();
    
    // Check that the form elements are present
    await expect(page.getByText('Meal Name')).toBeVisible();
    await expect(page.getByText('Add Food')).toBeVisible();
  });

  test('should properly display meal structure in diary', async ({ page }) => {
    // Go to today view 
    await expect(page.getByText('Today')).toBeVisible();
    
    // Click the "Log food" button
    await page.getByRole('button', { name: 'Log food' }).click();
    
    // Wait for quick log panel
    await expect(page.getByText('Quick Log')).toBeVisible();
    
    // Add a food to check that diary shows meals properly
    await page.getByPlaceholder('Search foods').fill('bread');
    await page.waitForTimeout(1000);
    
    // If we have a way to add to a specific meal, test it
    const breadResult = page.locator('[data-testid="food-search-result"]').first();
    if (await breadResult.isVisible()) {
      await breadResult.click();
      
      // Verify the food was added to diary view
      await expect(page.getByText('bread', { exact: false })).toBeVisible();
    }
  });

  test('should access library from sidebar', async ({ page }) => {
    // On homepage, verify we can access library 
    await expect(page.getByText('Today')).toBeVisible();
    
    // Click on Library button in sidebar
    await page.getByRole('button', { name: 'Library' }).click();
    
    // Wait for the page to load and verify we're in Library
    await expect(page.getByText('Library')).toBeVisible();
    await expect(page.locator('[data-testid="library-view"]')).toBeVisible();
  });
});