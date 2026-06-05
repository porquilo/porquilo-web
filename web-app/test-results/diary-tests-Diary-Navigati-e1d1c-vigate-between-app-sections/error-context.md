# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: diary-tests.spec.ts >> Diary Navigation and Food Entry Tests >> should navigate between app sections
- Location: e2e/diary-tests.spec.ts:58:3

# Error details

```
Error: expect(locator).toBeVisible() failed

Locator: getByText('Library')
Expected: visible
Error: strict mode violation: getByText('Library') resolved to 3 elements:
    1) <button>…</button> aka getByRole('button', { name: 'Library', exact: true })
    2) <h1>Library</h1> aka getByRole('heading', { name: 'Library' })
    3) <button type="button">Add to library</button> aka getByRole('button', { name: 'Add to library' })

Call log:
  - Expect "toBeVisible" with timeout 5000ms
  - waiting for getByText('Library')

```

# Page snapshot

```yaml
- generic [ref=e3]:
  - generic [ref=e4]:
    - generic [ref=e5]:
      - img [ref=e6]
      - generic [ref=e11]: Porquilo
    - navigation [ref=e12]:
      - button "Today" [ref=e13] [cursor=pointer]:
        - img [ref=e14]
        - text: Today
      - button "Library" [active] [ref=e18] [cursor=pointer]:
        - img [ref=e19]
        - text: Library
      - button "Reports" [ref=e23] [cursor=pointer]:
        - img [ref=e24]
        - text: Reports
      - button "Settings" [ref=e27] [cursor=pointer]:
        - img [ref=e28]
        - text: Settings
    - generic [ref=e33]:
      - generic [ref=e36]: porq.local
      - text: Your data. Your hardware.
  - generic [ref=e37]:
    - generic [ref=e39]:
      - banner [ref=e40]:
        - generic [ref=e41]:
          - heading "Library" [level=1] [ref=e42]
          - generic [ref=e43]: Foods and recipes — search, edit, and log directly.
        - button "Add custom food" [ref=e44] [cursor=pointer]
      - generic [ref=e45]:
        - button "Foods · 0" [ref=e46] [cursor=pointer]
        - button "Recipes · 5" [ref=e47] [cursor=pointer]
      - generic [ref=e48]:
        - generic [ref=e49]:
          - img [ref=e50]
          - textbox "banana, oat milk, …" [ref=e54]
        - generic [ref=e55]:
          - button "All" [ref=e56] [cursor=pointer]
          - button "Custom" [ref=e57] [cursor=pointer]
          - button "USDA" [ref=e58] [cursor=pointer]
          - button "Open Food Facts" [ref=e59] [cursor=pointer]
          - button "Drinks" [ref=e60] [cursor=pointer]
      - generic [ref=e61]:
        - generic [ref=e62]:
          - generic [ref=e63]: Name
          - generic [ref=e64]: Source
          - generic [ref=e65]: kcal/100g
          - generic [ref=e66]: Protein
          - generic [ref=e67]: Fat
          - generic [ref=e68]: Carbs
          - generic [ref=e69]: Quantity
        - generic [ref=e71]: No foods found
      - generic:
        - generic:
          - generic:
            - generic: Add custom food
            - button:
              - img
          - generic:
            - generic:
              - generic:
                - generic: Name *
                - textbox "e.g. Banana, raw"
              - generic:
                - generic: Brand
                - textbox "e.g. Fage (optional)"
              - generic:
                - generic: Barcode
                - textbox "e.g. 5449000214911 (optional)"
            - generic:
              - generic: Default unit
              - generic:
                - button "g"
                - button "ml"
            - generic:
              - generic: Nutrients per 100g
              - generic:
                - generic:
                  - generic: Calories (kcal) *
                  - spinbutton
                - generic:
                  - generic: Protein (g)
                  - spinbutton
                - generic:
                  - generic: Carbs (g)
                  - spinbutton
                - generic:
                  - generic: Fat (g)
                  - spinbutton
            - generic:
              - button "Show more nutrients":
                - img
                - text: Show more nutrients
            - generic:
              - generic: Serving variants
              - button "+ Add variant"
          - generic:
            - button "Add to library"
    - generic:
      - generic:
        - generic:
          - generic: Quick log
          - button:
            - img
        - generic:
          - generic:
            - img
            - textbox "What did you eat?"
```

# Test source

```ts
  1  | import { test, expect } from '@playwright/test';
  2  | 
  3  | test.describe('Diary Navigation and Food Entry Tests', () => {
  4  |   test.beforeEach(async ({ page }) => {
  5  |     await page.goto('/');
  6  |   });
  7  | 
  8  |   test('should navigate between dates in diary', async ({ page }) => {
  9  |     // Check that we're on the today view
  10 |     await expect(page.getByText('Today')).toBeVisible();
  11 |     
  12 |     // Navigate to next day
  13 |     await page.getByRole('button', { name: '>' }).click();
  14 |     await page.waitForTimeout(500); // Wait for date change
  15 |     
  16 |     // Verify date navigation worked
  17 |     const currentDate = new Date();
  18 |     const tomorrow = new Date(currentDate);
  19 |     tomorrow.setDate(tomorrow.getDate() + 1);
  20 |     
  21 |     const formattedTomorrow = tomorrow.toISOString().split('T')[0];
  22 |     await expect(page.getByText(formattedTomorrow)).toBeVisible();
  23 |     
  24 |     // Navigate back to today  
  25 |     await page.getByRole('button', { name: '<' }).click();
  26 |     await page.waitForTimeout(500); // Wait for date change
  27 |     await expect(page.getByText(new Date().toISOString().split('T')[0])).toBeVisible();
  28 |   });
  29 | 
  30 |   test('should log food entry successfully', async ({ page }) => {
  31 |     // Click the "Log food" button to open quick log panel
  32 |     await page.getByRole('button', { name: 'Log food' }).click();
  33 |     
  34 |     // Wait for the quick log panel to appear
  35 |     await expect(page.getByText('Quick Log')).toBeVisible();
  36 |     
  37 |     // Search for a food item (using a common food like "apple")
  38 |     await page.getByPlaceholder('Search foods').fill('apple');
  39 |     
  40 |     // Wait for search results to appear
  41 |     await page.waitForTimeout(1000);
  42 |     
  43 |     // Select an apple from search results - assuming the first result is what we want
  44 |     const firstResult = page.locator('[data-testid="food-search-result"]').first();
  45 |     await expect(firstResult).toBeVisible();
  46 |     
  47 |     // Click on the food to add it to diary (we'll assume clicking the first item works)
  48 |     await firstResult.click();
  49 |     
  50 |     // Verify food was added by checking that the search field is cleared
  51 |     await expect(page.getByPlaceholder('Search foods')).toHaveValue('');
  52 |     
  53 |     // Check that food appears in diary view
  54 |     await page.waitForTimeout(1000);
  55 |     await expect(page.getByText('apple', { exact: false })).toBeVisible();
  56 |   });
  57 | 
  58 |   test('should navigate between app sections', async ({ page }) => {
  59 |     // Start on Today view
  60 |     await expect(page.getByText('Today')).toBeVisible();
  61 |     
  62 |     // Navigate to Library
  63 |     await page.getByRole('button', { name: 'Library' }).click();
  64 |     await page.waitForTimeout(500);
> 65 |     await expect(page.getByText('Library')).toBeVisible();
     |                                             ^ Error: expect(locator).toBeVisible() failed
  66 |     
  67 |     // Navigate to Reports
  68 |     await page.getByRole('button', { name: 'Reports' }).click();
  69 |     await page.waitForTimeout(500); 
  70 |     await expect(page.getByText('Reports')).toBeVisible();
  71 |     
  72 |     // Navigate to Settings
  73 |     await page.getByRole('button', { name: 'Settings' }).click();
  74 |     await page.waitForTimeout(500);
  75 |     await expect(page.getByText('Settings')).toBeVisible();
  76 |     
  77 |     // Return to Today view
  78 |     await page.getByRole('button', { name: 'Today' }).click();
  79 |     await page.waitForTimeout(500);
  80 |     await expect(page.getByText('Today')).toBeVisible();
  81 |   });
  82 | });
```