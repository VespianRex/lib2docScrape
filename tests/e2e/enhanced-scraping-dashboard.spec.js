/**
 * Enhanced Scraping Dashboard Tests
 * 
 * Comprehensive tests for the scraping dashboard functionality
 */

const { test, expect } = require('@playwright/test');

test.describe('Enhanced Scraping Dashboard Tests', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to the scraping dashboard before each test
    await page.goto('/scraping_dashboard.html');
    await expect(page).toHaveTitle(/Scraping Dashboard/i);
  });

  test('should load all UI components correctly', async ({ page }) => {
    // Verify all major UI components are present
    await expect(page.locator('#docUrl')).toBeVisible();
    await expect(page.locator('#backend')).toBeVisible();
    await expect(page.locator('#configPreset')).toBeVisible();
    await expect(page.locator('#comprehensiveSettings')).toBeVisible();
    await expect(page.locator('#startScrapingBtn')).toBeVisible();
  });

  test('should validate URL input', async ({ page }) => {
    // Test empty URL
    await page.locator('#startScrapingBtn').click();
    await expect(page.locator('.invalid-feedback')).toBeVisible();
    
    // Test invalid URL format
    await page.locator('#docUrl').fill('invalid-url');
    await page.locator('#startScrapingBtn').click();
    await expect(page.locator('.invalid-feedback')).toBeVisible();
    
    // Test valid URL
    await page.locator('#docUrl').fill('https://example.com');
    await page.locator('#startScrapingBtn').click();
    await expect(page.locator('.invalid-feedback')).not.toBeVisible();
  });

  test('should change backend description when backend is changed', async ({ page }) => {
    // Get initial description
    const initialDescription = await page.locator('#backendDescription').textContent();
    
    // Change backend
    await page.locator('#backend').selectOption('crawl4ai');
    
    // Verify description changed
    const newDescription = await page.locator('#backendDescription').textContent();
    expect(newDescription).not.toEqual(initialDescription);
  });

  test('should update settings when configuration preset is changed', async ({ page }) => {
    // Get initial max depth value
    await page.locator('#maxDepth').isVisible();
    const initialMaxDepth = await page.locator('#maxDepth').inputValue();
    
    // Change preset to comprehensive
    await page.locator('#configPreset').selectOption('comprehensive');
    
    // Verify settings changed
    const newMaxDepth = await page.locator('#maxDepth').inputValue();
    expect(newMaxDepth).not.toEqual(initialMaxDepth);
  });

  test('should save custom preset', async ({ page }) => {
    // Set custom values
    await page.locator('#maxDepth').fill('5');
    await page.locator('#maxPages').fill('100');
    
    // Save as custom preset
    await page.locator('#configPreset').selectOption('custom');
    await page.locator('#savePresetBtn').click();
    
    // Enter preset name in modal
    await page.locator('#presetNameInput').fill('My Custom Preset');
    await page.locator('#savePresetModalBtn').click();
    
    // Verify preset is saved and selectable
    await expect(page.locator('#configPreset option:has-text("My Custom Preset")')).toBeVisible();
  });

  test('should start scraping with valid configuration', async ({ page }) => {
    // Configure scraping
    await page.locator('#docUrl').fill('https://example.com');
    await page.locator('#backend').selectOption('http');
    await page.locator('#configPreset').selectOption('minimal');
    
    // Start scraping
    await page.locator('#startScrapingBtn').click();
    
    // Verify loading indicator appears
    await expect(page.locator('#scrapingProgress')).toBeVisible();
    
    // Verify results appear (with timeout for scraping to complete)
    await expect(page.locator('#scrapingResults')).toBeVisible({ timeout: 30000 });
  });

  test('should display benchmark results', async ({ page }) => {
    // Configure scraping
    await page.locator('#docUrl').fill('https://example.com');
    
    // Click benchmark button
    await page.locator('#benchmarkBtn').click();
    
    // Verify benchmark modal appears
    await expect(page.locator('#benchmarkModal')).toBeVisible();
    
    // Start benchmark
    await page.locator('#startBenchmarkBtn').click();
    
    // Verify benchmark results appear (with timeout for benchmark to complete)
    await expect(page.locator('#benchmarkResults')).toBeVisible({ timeout: 60000 });
    
    // Verify results contain performance metrics for different backends
    await expect(page.locator('#benchmarkResults')).toContainText('HTTP');
    await expect(page.locator('#benchmarkResults')).toContainText('Crawl4AI');
  });

  test('should handle server errors gracefully', async ({ page }) => {
    // Mock server error
    await page.route('**/api/scrape', route => {
      route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ error: 'Internal Server Error' }),
      });
    });
    
    // Configure scraping
    await page.locator('#docUrl').fill('https://example.com');
    await page.locator('#startScrapingBtn').click();
    
    // Verify error message appears
    await expect(page.locator('#errorAlert')).toBeVisible();
    await expect(page.locator('#errorAlert')).toContainText('Internal Server Error');
  });

  test('should persist settings in local storage', async ({ page }) => {
    // Configure settings
    await page.locator('#docUrl').fill('https://example.com');
    await page.locator('#backend').selectOption('playwright');
    await page.locator('#maxDepth').fill('3');
    
    // Save settings
    await page.locator('#saveSettingsBtn').click();
    
    // Reload page
    await page.reload();
    
    // Verify settings are restored
    await expect(page.locator('#docUrl')).toHaveValue('https://example.com');
    await expect(page.locator('#backend')).toHaveValue('playwright');
    await expect(page.locator('#maxDepth')).toHaveValue('3');
  });
});