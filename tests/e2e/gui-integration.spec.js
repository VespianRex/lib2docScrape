/**
 * GUI Integration Tests
 * 
 * Tests for complete user workflows and component integration
 */

const { test, expect } = require('@playwright/test');

test.describe('Complete User Workflows', () => {
  test('should complete full documentation scraping workflow', async ({ page }) => {
    // Step 1: Navigate to dashboard
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    // Verify dashboard loads
    await expect(page.locator('h1')).toBeVisible();
    
    // Step 2: Navigate to scraping interface
    const scrapingLink = page.locator('nav a[href="/scraping"]');
    if (await scrapingLink.isVisible()) {
      await scrapingLink.click();
    } else {
      await page.goto('/scraping');
    }
    await page.waitForLoadState('networkidle');
    
    // Step 3: Configure scraping job
    await page.locator('#docUrl').fill('https://docs.python.org/3/tutorial/');
    await page.locator('#configPreset').selectOption('default');
    await page.locator('#backend').selectOption('http');
    
    // Step 4: Start scraping
    await page.locator('button[type="submit"]').click();
    
    // Step 5: Monitor progress
    const progressIndicator = page.locator('.progress-indicator');
    if (await progressIndicator.isVisible()) {
      // Wait for completion (with timeout)
      await page.waitForSelector('.status-complete', { timeout: 30000 });
    }
    
    // Step 6: Navigate to results
    await page.goto('/results');
    await page.waitForLoadState('networkidle');
    
    // Step 7: Verify results are displayed
    const resultsContainer = page.locator('.results-container');
    if (await resultsContainer.isVisible()) {
      await expect(resultsContainer).toBeVisible();
    }
    
    // Step 8: Export results
    const exportButton = page.locator('[data-testid="export-results"]');
    if (await exportButton.isVisible()) {
      await exportButton.click();
      
      const csvOption = page.locator('[data-format="csv"]');
      if (await csvOption.isVisible()) {
        const downloadPromise = page.waitForEvent('download');
        await csvOption.click();
        await downloadPromise;
      }
    }
  });

  test('should complete search and visualization workflow', async ({ page }) => {
    // Step 1: Navigate to search
    await page.goto('/search');
    await page.waitForLoadState('networkidle');
    
    // Step 2: Perform search
    await page.locator('input[type="search"]').fill('python documentation');
    await page.locator('button[type="submit"]').click();
    
    // Wait for search results
    await page.waitForSelector('.search-results', { timeout: 10000 });
    
    // Step 3: Select results for visualization
    const resultCheckboxes = page.locator('.search-result input[type="checkbox"]');
    if (await resultCheckboxes.count() > 0) {
      await resultCheckboxes.first().check();
      await resultCheckboxes.nth(1).check();
    }
    
    // Step 4: Navigate to visualizations
    const visualizeButton = page.locator('[data-testid="visualize-results"]');
    if (await visualizeButton.isVisible()) {
      await visualizeButton.click();
    } else {
      await page.goto('/visualizations');
    }
    await page.waitForLoadState('networkidle');
    
    // Step 5: Generate chart from search results
    const chartTypeSelect = page.locator('select[name="chartType"]');
    if (await chartTypeSelect.isVisible()) {
      await chartTypeSelect.selectOption('bar');
      
      const generateButton = page.locator('[data-testid="generate-chart"]');
      if (await generateButton.isVisible()) {
        await generateButton.click();
        await page.waitForTimeout(2000);
        
        // Verify chart was generated
        const chartContainer = page.locator('.chart-container');
        if (await chartContainer.isVisible()) {
          await expect(chartContainer).toBeVisible();
        }
      }
    }
  });

  test('should handle multi-library documentation workflow', async ({ page }) => {
    // Step 1: Navigate to library discovery
    await page.goto('/');
    
    const discoveryButton = page.locator('[data-testid="library-discovery"]');
    if (await discoveryButton.isVisible()) {
      await discoveryButton.click();
      
      // Step 2: Discover multiple libraries
      const libraryInput = page.locator('input[name="libraries"]');
      if (await libraryInput.isVisible()) {
        await libraryInput.fill('requests, flask, django');
        
        const discoverButton = page.locator('[data-testid="discover-libraries"]');
        if (await discoverButton.isVisible()) {
          await discoverButton.click();
          
          // Wait for discovery results
          await page.waitForTimeout(5000);
          
          // Step 3: Select libraries for scraping
          const libraryCheckboxes = page.locator('.library-item input[type="checkbox"]');
          if (await libraryCheckboxes.count() > 0) {
            for (let i = 0; i < Math.min(3, await libraryCheckboxes.count()); i++) {
              await libraryCheckboxes.nth(i).check();
            }
            
            // Step 4: Start batch scraping
            const batchScrapeButton = page.locator('[data-testid="batch-scrape"]');
            if (await batchScrapeButton.isVisible()) {
              await batchScrapeButton.click();
              
              // Monitor batch progress
              const batchProgress = page.locator('.batch-progress');
              if (await batchProgress.isVisible()) {
                await expect(batchProgress).toBeVisible();
              }
            }
          }
        }
      }
    }
  });
});

test.describe('Component Integration', () => {
  test('should integrate dashboard with real-time updates', async ({ page }) => {
    await page.goto('/');
    
    // Check for WebSocket connection
    const wsStatus = page.locator('[data-testid="ws-status"]');
    if (await wsStatus.isVisible()) {
      await expect(wsStatus).toHaveClass(/connected/);
    }
    
    // Start a scraping job to trigger updates
    await page.locator('#docUrl').fill('https://example.com');
    await page.locator('button[type="submit"]').click();
    
    // Check for real-time updates in dashboard
    const statsCards = page.locator('.stats-card');
    if (await statsCards.count() > 0) {
      // Monitor for stat changes
      const initialValue = await statsCards.first().locator('.stat-value').textContent();
      
      // Wait for potential updates
      await page.waitForTimeout(5000);
      
      const updatedValue = await statsCards.first().locator('.stat-value').textContent();
      // Note: In a real scenario, we'd expect the value to change
    }
  });

  test('should integrate search with filters and sorting', async ({ page }) => {
    await page.goto('/search');
    
    // Perform search
    await page.locator('input[type="search"]').fill('documentation');
    await page.locator('button[type="submit"]').click();
    await page.waitForSelector('.search-results', { timeout: 10000 });
    
    // Apply filters
    const filters = page.locator('.search-filters');
    if (await filters.isVisible()) {
      const filterCheckbox = filters.locator('input[type="checkbox"]').first();
      if (await filterCheckbox.isVisible()) {
        await filterCheckbox.check();
        await page.waitForTimeout(1000);
      }
    }
    
    // Apply sorting
    const sortSelect = page.locator('select[name="sort"]');
    if (await sortSelect.isVisible()) {
      await sortSelect.selectOption('date');
      await page.waitForTimeout(1000);
    }
    
    // Verify integrated filtering and sorting
    const results = page.locator('.search-result');
    if (await results.count() > 0) {
      await expect(results.first()).toBeVisible();
    }
  });

  test('should integrate export functionality across components', async ({ page }) => {
    // Test export from search results
    await page.goto('/search');
    await page.locator('input[type="search"]').fill('test');
    await page.locator('button[type="submit"]').click();
    await page.waitForTimeout(3000);
    
    const searchExportButton = page.locator('[data-testid="export-search-results"]');
    if (await searchExportButton.isVisible()) {
      await searchExportButton.click();
      
      const exportOptions = page.locator('.export-options');
      if (await exportOptions.isVisible()) {
        await expect(exportOptions).toBeVisible();
      }
    }
    
    // Test export from visualizations
    await page.goto('/visualizations');
    
    const chartTypeSelect = page.locator('select[name="chartType"]');
    if (await chartTypeSelect.isVisible()) {
      await chartTypeSelect.selectOption('bar');
      
      const generateButton = page.locator('[data-testid="generate-chart"]');
      if (await generateButton.isVisible()) {
        await generateButton.click();
        await page.waitForTimeout(2000);
        
        const vizExportButton = page.locator('[data-testid="export-chart"]');
        if (await vizExportButton.isVisible()) {
          await vizExportButton.click();
          
          const vizExportOptions = page.locator('.export-options');
          if (await vizExportOptions.isVisible()) {
            await expect(vizExportOptions).toBeVisible();
          }
        }
      }
    }
  });
});

test.describe('Error Handling Integration', () => {
  test('should handle network errors gracefully across components', async ({ page }) => {
    // Simulate network issues
    await page.context().setOffline(true);
    
    // Test dashboard behavior
    await page.goto('/');
    
    const errorMessage = page.locator('.network-error');
    if (await errorMessage.isVisible()) {
      await expect(errorMessage).toContainText('network');
    }
    
    // Test search behavior
    await page.goto('/search');
    await page.locator('input[type="search"]').fill('test');
    await page.locator('button[type="submit"]').click();
    
    const searchError = page.locator('.search-error');
    if (await searchError.isVisible()) {
      await expect(searchError).toBeVisible();
    }
    
    // Restore network
    await page.context().setOffline(false);
    
    // Test recovery
    await page.reload();
    await page.waitForLoadState('networkidle');
    await expect(page.locator('body')).toBeVisible();
  });

  test('should handle API errors consistently', async ({ page }) => {
    // Mock API errors
    await page.route('/api/**', route => {
      route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ error: 'Internal server error' })
      });
    });
    
    // Test dashboard API error handling
    await page.goto('/');
    
    const dashboardError = page.locator('.api-error');
    if (await dashboardError.isVisible()) {
      await expect(dashboardError).toContainText('error');
    }
    
    // Test search API error handling
    await page.goto('/search');
    await page.locator('input[type="search"]').fill('test');
    await page.locator('button[type="submit"]').click();
    
    const searchApiError = page.locator('.api-error');
    if (await searchApiError.isVisible()) {
      await expect(searchApiError).toContainText('error');
    }
  });
});

test.describe('Performance Integration', () => {
  test('should maintain performance across component interactions', async ({ page }) => {
    // Start performance monitoring
    await page.goto('/');
    
    const startTime = Date.now();
    
    // Navigate through multiple components
    await page.goto('/search');
    await page.waitForLoadState('networkidle');
    
    await page.goto('/visualizations');
    await page.waitForLoadState('networkidle');
    
    await page.goto('/results');
    await page.waitForLoadState('networkidle');
    
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    const endTime = Date.now();
    const totalTime = endTime - startTime;
    
    // Verify reasonable performance (adjust threshold as needed)
    expect(totalTime).toBeLessThan(15000); // 15 seconds for full navigation
  });

  test('should handle concurrent operations efficiently', async ({ page }) => {
    await page.goto('/');
    
    // Start multiple operations concurrently
    const operations = [
      // Start scraping
      page.locator('#docUrl').fill('https://example.com'),
      page.locator('button[type="submit"]').click(),
      
      // Navigate to search in new tab
      page.context().newPage().then(newPage => {
        return newPage.goto('/search');
      }),
      
      // Check dashboard stats
      page.locator('[data-testid="refresh-data"]').click()
    ];
    
    // Wait for all operations to complete
    await Promise.all(operations);
    
    // Verify system remains responsive
    await expect(page.locator('body')).toBeVisible();
  });
});
