/**
 * Enhanced Integration Tests
 * 
 * Comprehensive end-to-end tests for the complete workflow
 */

const { test, expect } = require('@playwright/test');

test.describe('Enhanced Integration Tests', () => {
  test('should perform complete scraping workflow', async ({ page }) => {
    // 1. Start at the dashboard
    await page.goto('/scraping_dashboard.html');
    await expect(page).toHaveTitle(/Scraping Dashboard/i);
    
    // 2. Configure scraping
    await page.locator('#docUrl').fill('https://example.com');
    await page.locator('#backend').selectOption('http');
    await page.locator('#configPreset').selectOption('minimal');
    
    // 3. Start scraping
    await page.locator('#startScrapingBtn').click();
    
    // 4. Wait for scraping to complete
    await expect(page.locator('#scrapingResults')).toBeVisible({ timeout: 30000 });
    
    // 5. Verify results contain expected data
    await expect(page.locator('#scrapingResults')).toContainText('example.com');
    
    // 6. Navigate to document viewer
    await page.locator('#viewDocumentsBtn').click();
    
    // 7. Verify document viewer loaded
    await expect(page).toHaveTitle(/Document Viewer/i);
    
    // 8. Verify document content is displayed
    await expect(page.locator('#documentContent')).toBeVisible();
    
    // 9. Navigate to search page
    await page.locator('nav a[href*="search"]').click();
    
    // 10. Verify search page loaded
    await expect(page).toHaveTitle(/Search/i);
    
    // 11. Perform search
    await page.locator('#searchInput').fill('example');
    await page.locator('#searchButton').click();
    
    // 12. Verify search results
    await expect(page.locator('#searchResults')).toBeVisible();
    
    // 13. Navigate to visualizations
    await page.locator('nav a[href*="visualizations"]').click();
    
    // 14. Verify visualizations page loaded
    await expect(page).toHaveTitle(/Visualizations/i);
    
    // 15. Verify charts are displayed
    await expect(page.locator('#coverageChart')).toBeVisible();
    await expect(page.locator('#dependencyGraph')).toBeVisible();
  });

  test('should handle errors throughout the workflow', async ({ page }) => {
    // 1. Start at the dashboard with invalid URL
    await page.goto('/scraping_dashboard.html');
    await page.locator('#docUrl').fill('invalid-url');
    await page.locator('#startScrapingBtn').click();
    
    // 2. Verify error message
    await expect(page.locator('.invalid-feedback')).toBeVisible();
    
    // 3. Fix URL and proceed
    await page.locator('#docUrl').fill('https://example.com');
    
    // 4. Mock server error
    await page.route('**/api/scrape', route => {
      route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ error: 'Internal Server Error' }),
      });
    });
    
    // 5. Start scraping
    await page.locator('#startScrapingBtn').click();
    
    // 6. Verify error message
    await expect(page.locator('#errorAlert')).toBeVisible();
    
    // 7. Restore normal behavior
    await page.unroute('**/api/scrape');
    
    // 8. Navigate to document viewer with nonexistent document
    await page.goto('/doc_viewer.html?doc=nonexistent');
    
    // 9. Verify error message
    await expect(page.locator('#errorMessage')).toBeVisible();
    
    // 10. Navigate to search and search for nonexistent term
    await page.goto('/search.html');
    await page.locator('#searchInput').fill('xyznonexistentterm123');
    await page.locator('#searchButton').click();
    
    // 11. Verify no results message
    await expect(page.locator('#noResultsMessage')).toBeVisible();
  });

  test('should maintain state between pages', async ({ page }) => {
    // 1. Start at the dashboard
    await page.goto('/scraping_dashboard.html');
    
    // 2. Configure scraping
    await page.locator('#docUrl').fill('https://example.com');
    await page.locator('#backend').selectOption('http');
    
    // 3. Start scraping
    await page.locator('#startScrapingBtn').click();
    
    // 4. Wait for scraping to complete
    await expect(page.locator('#scrapingResults')).toBeVisible({ timeout: 30000 });
    
    // 5. Navigate to search page
    await page.locator('nav a[href*="search"]').click();
    
    // 6. Verify the recently scraped content is available in search
    await page.locator('#searchInput').fill('example');
    await page.locator('#searchButton').click();
    await expect(page.locator('#searchResults')).toBeVisible();
    
    // 7. Navigate to document viewer
    await page.locator('nav a[href*="doc_viewer"]').click();
    
    // 8. Verify recently scraped documents are listed
    await expect(page.locator('#documentsList')).toContainText('example.com');
    
    // 9. Navigate to visualizations
    await page.locator('nav a[href*="visualizations"]').click();
    
    // 10. Verify visualizations include recent scraping data
    await expect(page.locator('#coverageChart')).toBeVisible();
    
    // 11. Verify scraping source is displayed in filters
    await expect(page.locator('#libraryFilter')).toContainText('example.com');
  });

  test('should handle mobile responsive layout', async ({ page }) => {
    // 1. Set viewport to mobile size
    await page.setViewportSize({ width: 375, height: 667 });
    
    // 2. Navigate to dashboard
    await page.goto('/scraping_dashboard.html');
    
    // 3. Verify mobile menu is present
    await expect(page.locator('.navbar-toggler')).toBeVisible();
    
    // 4. Open mobile menu
    await page.locator('.navbar-toggler').click();
    
    // 5. Verify menu items are visible
    await expect(page.locator('.navbar-collapse.show')).toBeVisible();
    
    // 6. Configure and start scraping
    await page.locator('#docUrl').fill('https://example.com');
    await page.locator('#startScrapingBtn').click();
    
    // 7. Verify results are displayed properly on mobile
    await expect(page.locator('#scrapingResults')).toBeVisible({ timeout: 30000 });
    
    // 8. Navigate to document viewer
    await page.locator('nav a[href*="doc_viewer"]').click();
    
    // 9. Verify document viewer is usable on mobile
    await expect(page.locator('#documentContent')).toBeVisible();
    
    // 10. Verify mobile-specific controls are present
    await expect(page.locator('#mobileNavControls')).toBeVisible();
  });

  test('should support keyboard navigation', async ({ page }) => {
    // 1. Navigate to dashboard
    await page.goto('/scraping_dashboard.html');
    
    // 2. Focus on URL input
    await page.locator('#docUrl').focus();
    
    // 3. Fill URL using keyboard
    await page.keyboard.type('https://example.com');
    
    // 4. Tab to backend selection
    await page.keyboard.press('Tab');
    
    // 5. Verify backend selection is focused
    await expect(page.locator('#backend')).toBeFocused();
    
    // 6. Select backend using keyboard
    await page.keyboard.press('ArrowDown');
    await page.keyboard.press('Enter');
    
    // 7. Tab to start button
    await page.keyboard.press('Tab');
    await page.keyboard.press('Tab');
    await page.keyboard.press('Tab');
    
    // 8. Press start button using keyboard
    await page.keyboard.press('Enter');
    
    // 9. Verify scraping started
    await expect(page.locator('#scrapingProgress')).toBeVisible();
  });
});