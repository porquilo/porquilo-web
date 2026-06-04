# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: diary-tests.spec.ts >> Diary Navigation and Food Entry Tests >> should log food entry successfully
- Location: e2e/diary-tests.spec.ts:30:3

# Error details

```
Test timeout of 30000ms exceeded.
```

```
Error: locator.fill: Test timeout of 30000ms exceeded.
Call log:
  - waiting for getByPlaceholder('Search foods')

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
      - button "Library" [ref=e18] [cursor=pointer]:
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
      - generic [ref=e40]:
        - generic [ref=e41]:
          - generic [ref=e42]:
            - button [ref=e43] [cursor=pointer]:
              - img [ref=e44]
            - heading "Thursday, June 4" [level=1] [ref=e46]
            - button [ref=e47] [cursor=pointer]:
              - img [ref=e48]
          - button "Log food" [ref=e50] [cursor=pointer]
        - generic [ref=e51]:
          - button "MON 1" [ref=e52] [cursor=pointer]:
            - generic [ref=e53]: MON
            - generic [ref=e54]: "1"
          - button "TUE 2" [ref=e56] [cursor=pointer]:
            - generic [ref=e57]: TUE
            - generic [ref=e58]: "2"
          - button "WED 3" [ref=e60] [cursor=pointer]:
            - generic [ref=e61]: WED
            - generic [ref=e62]: "3"
          - button "THU 4" [ref=e64] [cursor=pointer]:
            - generic [ref=e65]: THU
            - generic [ref=e66]: "4"
          - button "FRI 5" [ref=e68] [cursor=pointer]:
            - generic [ref=e69]: FRI
            - generic [ref=e70]: "5"
          - button "SAT 6" [ref=e72] [cursor=pointer]:
            - generic [ref=e73]: SAT
            - generic [ref=e74]: "6"
          - button "SUN 7" [ref=e76] [cursor=pointer]:
            - generic [ref=e77]: SUN
            - generic [ref=e78]: "7"
        - generic [ref=e80]:
          - generic [ref=e81]:
            - generic [ref=e82]:
              - generic [ref=e83]: ~
              - generic [ref=e84]: 1,514
              - generic [ref=e85]: kcal
            - generic [ref=e86]: 4 entries, 4 estimated
            - generic [ref=e91]:
              - generic [ref=e92]:
                - generic [ref=e94]: 19g
                - text: protein
              - generic [ref=e95]:
                - generic [ref=e97]: 15g
                - text: carbs
              - generic [ref=e98]:
                - generic [ref=e100]: 15g
                - text: fat
          - generic [ref=e102]:
            - generic [ref=e103]: Day at a glance
            - generic [ref=e104]:
              - generic [ref=e105]:
                - generic [ref=e106]: Total weight
                - generic [ref=e107]: 670 g
              - generic [ref=e108]:
                - generic [ref=e109]: Entries
                - generic [ref=e110]: "4"
              - generic [ref=e111]:
                - generic [ref=e112]: Last logged
                - generic [ref=e113]: 17:34
            - generic [ref=e114]: How you knew
            - generic [ref=e117]:
              - generic [ref=e118]:
                - generic [ref=e121]: Measured
                - generic [ref=e122]: "0"
              - generic [ref=e123]:
                - generic [ref=e126]: Calculated
                - generic [ref=e127]: "0"
              - generic [ref=e128]:
                - generic [ref=e131]: Estimated
                - generic [ref=e132]: "4"
      - generic [ref=e135]:
        - generic [ref=e136]:
          - generic [ref=e137]:
            - generic [ref=e138]: Breakfast
            - generic [ref=e139]: ~700 kcal · 100 g
          - generic [ref=e140]:
            - generic [ref=e141]: 14:22
            - generic [ref=e144]: Test food 2
            - generic [ref=e146]: quick_log
            - generic [ref=e148]: ~100 g
            - generic [ref=e149]: ~700 kcal
        - generic [ref=e150]:
          - generic [ref=e151]: Lunch
          - button "Eating after all" [ref=e152] [cursor=pointer]
        - generic [ref=e153]:
          - generic [ref=e154]:
            - generic [ref=e155]: Dinner
            - generic [ref=e156]: ~100 kcal · 200 g
          - generic [ref=e157]:
            - generic [ref=e158]: 14:10
            - generic [ref=e161]: Test food
            - generic [ref=e163]: quick_log
            - generic [ref=e165]: ~100 g
            - generic [ref=e166]: ~50 kcal
          - generic [ref=e167]:
            - generic [ref=e168]: 16:24
            - generic [ref=e171]: Test food
            - generic [ref=e173]: quick_log
            - generic [ref=e175]: ~100 g
            - generic [ref=e176]: ~50 kcal
        - generic [ref=e177]:
          - generic [ref=e178]:
            - generic [ref=e179]: Snack
            - generic [ref=e180]: ~714 kcal · 370 g
          - generic [ref=e181]:
            - generic [ref=e182]: 17:34
            - generic [ref=e185]: "test food #3"
            - generic [ref=e187]: quick_log
            - generic [ref=e189]: ~370 g
            - generic [ref=e190]: ~714 kcal
    - generic [ref=e193]:
      - generic [ref=e194]:
        - generic [ref=e195]: Quick log
        - button [ref=e196] [cursor=pointer]:
          - img [ref=e197]
      - generic [ref=e200]:
        - img [ref=e201]
        - textbox "What did you eat?" [active] [ref=e205]
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
> 38 |     await page.getByPlaceholder('Search foods').fill('apple');
     |                                                 ^ Error: locator.fill: Test timeout of 30000ms exceeded.
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
  65 |     await expect(page.getByText('Library')).toBeVisible();
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