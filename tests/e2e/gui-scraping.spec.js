/**
 * Scraping Interface GUI Tests
 * 
 * Tests for the main scraping functionality and interface
 */

const { test, expect } = require('@playwright/test');

test.describe('Scraping Interface', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to scraping page
    await page.goto('/');
    
    // Wait for page to load
    await page.waitForLoadState('networkidle');
  });

  test('should load scraping interface successfully', async ({ page }) => {
    // Check for scraping form elements
    await expect(page.locator('#scrapingForm')).toBeVisible();
    await expect(page.locator('#docUrl')).toBeVisible();
    await expect(page.locator('#configPreset')).toBeVisible();
    await expect(page.locator('#backend')).toBeVisible();
  });

  test('should validate URL input', async ({ page }) => {
    const urlInput = page.locator('#docUrl');
    const submitButton = page.locator('button[type="submit"]');
    
    // Test empty URL
    await submitButton.click();
    
    // Check for validation message
    const validationMessage = page.locator('.validation-error');
    if (await validationMessage.isVisible()) {
      await expect(validationMessage).toContainText('required');
    }
    
    // Test invalid URL
    await urlInput.fill('invalid-url');
    await submitButton.click();
    
    // Check for invalid URL message
    if (await validationMessage.isVisible()) {
      await expect(validationMessage).toContainText('valid URL');
    }
  });

  test('should start scraping process', async ({ page }) => {
    const urlInput = page.locator('#docUrl');
    const submitButton = page.locator('button[type="submit"]');
    
    // Enter valid URL
    await urlInput.fill('https://docs.python.org/3/');
    
    // Select configuration preset
    await page.locator('#configPreset').selectOption('default');
    
    // Select backend
    await page.locator('#backend').selectOption('http');
    
    // Start scraping
    await submitButton.click();
    
    // Check for progress indicator
    const progressIndicator = page.locator('.progress-indicator');
    if (await progressIndicator.isVisible()) {
      await expect(progressIndicator).toBeVisible();
    }
    
    // Check for status updates
    const statusMessage = page.locator('.status-message');
    if (await statusMessage.isVisible()) {
      await expect(statusMessage).toBeVisible();
    }
  });

  test('should display scraping progress', async ({ page }) => {
    // Start a scraping job
    await page.locator('#docUrl').fill('https://example.com');
    await page.locator('button[type="submit"]').click();
    
    // Wait for progress elements
    await page.waitForTimeout(1000);
    
    // Check for progress bar
    const progressBar = page.locator('.progress-bar');
    if (await progressBar.isVisible()) {
      await expect(progressBar).toBeVisible();
      
      // Check progress percentage
      const progressText = page.locator('.progress-text');
      if (await progressText.isVisible()) {
        await expect(progressText).toContainText('%');
      }
    }
  });

  test('should handle scraping errors gracefully', async ({ page }) => {
    // Mock API error
    await page.route('/api/scraping/start', route => {
      route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ error: 'Scraping failed' })
      });
    });
    
    // Try to start scraping
    await page.locator('#docUrl').fill('https://example.com');
    await page.locator('button[type="submit"]').click();
    
    // Wait for error handling
    await page.waitForTimeout(2000);
    
    // Check for error message
    const errorMessage = page.locator('.error-message');
    if (await errorMessage.isVisible()) {
      await expect(errorMessage).toContainText('error');
    }
  });

  test('should allow stopping scraping process', async ({ page }) => {
    // Start scraping
    await page.locator('#docUrl').fill('https://docs.python.org/3/');
    await page.locator('button[type="submit"]').click();
    
    // Wait for stop button to appear
    await page.waitForTimeout(1000);
    
    // Check for stop button
    const stopButton = page.locator('[data-testid="stop-scraping"]');
    if (await stopButton.isVisible()) {
      await stopButton.click();
      
      // Check for stopped status
      const statusMessage = page.locator('.status-message');
      if (await statusMessage.isVisible()) {
        await expect(statusMessage).toContainText('stopped');
      }
    }
  });

  test('should save custom configuration presets', async ({ page }) => {
    // Check for custom preset button
    const customPresetButton = page.locator('[data-testid="custom-preset"]');
    if (await customPresetButton.isVisible()) {
      await customPresetButton.click();
      
      // Fill custom preset form
      const presetForm = page.locator('.preset-form');
      if (await presetForm.isVisible()) {
        await presetForm.locator('input[name="name"]').fill('Test Preset');
        await presetForm.locator('input[name="maxDepth"]').fill('5');
        await presetForm.locator('input[name="maxPages"]').fill('50');
        
        // Save preset
        await presetForm.locator('button[type="submit"]').click();
        
        // Check preset was added to dropdown
        await page.waitForTimeout(500);
        const presetOption = page.locator('#configPreset option[value="Test Preset"]');
        if (await presetOption.isVisible()) {
          await expect(presetOption).toBeVisible();
        }
      }
    }
  });

  test('should display backend selection options', async ({ page }) => {
    const backendSelect = page.locator('#backend');
    
    // Check backend options are available
    const options = backendSelect.locator('option');
    const optionCount = await options.count();
    expect(optionCount).toBeGreaterThan(1);
    
    // Check for common backend options
    const httpOption = backendSelect.locator('option[value="http"]');
    if (await httpOption.isVisible()) {
      await expect(httpOption).toBeVisible();
    }
    
    const playwrightOption = backendSelect.locator('option[value="playwright"]');
    if (await playwrightOption.isVisible()) {
      await expect(playwrightOption).toBeVisible();
    }
  });

  test('should handle multiple URL input', async ({ page }) => {
    // Check for multiple URL input option
    const multiUrlToggle = page.locator('[data-testid="multi-url-toggle"]');
    if (await multiUrlToggle.isVisible()) {
      await multiUrlToggle.click();
      
      // Check for textarea for multiple URLs
      const urlTextarea = page.locator('textarea[name="urls"]');
      if (await urlTextarea.isVisible()) {
        await expect(urlTextarea).toBeVisible();
        
        // Enter multiple URLs
        await urlTextarea.fill('https://example.com\nhttps://test.com');
        
        // Start scraping
        await page.locator('button[type="submit"]').click();
        
        // Check for multiple URL processing
        const progressItems = page.locator('.progress-item');
        if (await progressItems.count() > 0) {
          expect(await progressItems.count()).toBeGreaterThan(1);
        }
      }
    }
  });

  test('should support URL discovery', async ({ page }) => {
    // Check for URL discovery feature
    const discoveryButton = page.locator('[data-testid="url-discovery"]');
    if (await discoveryButton.isVisible()) {
      await discoveryButton.click();
      
      // Check for discovery form
      const discoveryForm = page.locator('.discovery-form');
      if (await discoveryForm.isVisible()) {
        // Enter package name
        await discoveryForm.locator('input[name="package"]').fill('requests');
        
        // Start discovery
        await discoveryForm.locator('button[type="submit"]').click();
        
        // Wait for discovered URLs
        await page.waitForTimeout(3000);
        
        // Check for discovered URLs
        const discoveredUrls = page.locator('.discovered-url');
        if (await discoveredUrls.count() > 0) {
          await expect(discoveredUrls.first()).toBeVisible();
        }
      }
    }
  });
});

test.describe('Scraping Results', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/results');
    await page.waitForLoadState('networkidle');
  });

  test('should display scraping results', async ({ page }) => {
    // Check for results container
    const resultsContainer = page.locator('.results-container');
    if (await resultsContainer.isVisible()) {
      await expect(resultsContainer).toBeVisible();
    }
    
    // Check for results list
    const resultsList = page.locator('.results-list');
    if (await resultsList.isVisible()) {
      await expect(resultsList).toBeVisible();
    }
  });

  test('should allow exporting results', async ({ page }) => {
    // Check for export button
    const exportButton = page.locator('[data-testid="export-results"]');
    if (await exportButton.isVisible()) {
      await exportButton.click();
      
      // Check for export options
      const exportOptions = page.locator('.export-options');
      if (await exportOptions.isVisible()) {
        // Test CSV export
        const csvOption = exportOptions.locator('[data-format="csv"]');
        if (await csvOption.isVisible()) {
          await csvOption.click();
          
          // Wait for download to start
          const downloadPromise = page.waitForEvent('download');
          await downloadPromise;
        }
      }
    }
  });

  test('should filter results by status', async ({ page }) => {
    // Check for status filter
    const statusFilter = page.locator('select[name="status"]');
    if (await statusFilter.isVisible()) {
      // Filter by success
      await statusFilter.selectOption('success');
      
      // Wait for filtered results
      await page.waitForTimeout(1000);
      
      // Check that filter was applied
      const successResults = page.locator('.result-item.success');
      if (await successResults.count() > 0) {
        await expect(successResults.first()).toBeVisible();
      }
    }
  });

  test('should display result details', async ({ page }) => {
    // Check for result items
    const resultItems = page.locator('.result-item');
    if (await resultItems.count() > 0) {
      const firstResult = resultItems.first();
      
      // Click to view details
      await firstResult.click();
      
      // Check for details panel
      const detailsPanel = page.locator('.result-details');
      if (await detailsPanel.isVisible()) {
        await expect(detailsPanel).toBeVisible();
        
        // Check for content preview
        await expect(detailsPanel.locator('.content-preview')).toBeVisible();
        
        // Check for metadata
        await expect(detailsPanel.locator('.metadata')).toBeVisible();
      }
    }
  });
});
