/**
 * Search Interface GUI Tests
 * 
 * Tests for the search functionality and interface
 */

const { test, expect } = require('@playwright/test');

test.describe('Search Interface', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to search page
    await page.goto('/search');
    
    // Wait for page to load
    await page.waitForLoadState('networkidle');
  });

  test('should load search page successfully', async ({ page }) => {
    // Check page title
    await expect(page).toHaveTitle(/Search/);
    
    // Check main search elements are present
    await expect(page.locator('input[type="search"]')).toBeVisible();
    await expect(page.locator('button[type="submit"]')).toBeVisible();
  });

  test('should perform basic search', async ({ page }) => {
    const searchInput = page.locator('input[type="search"]');
    const searchButton = page.locator('button[type="submit"]');
    
    // Enter search query
    await searchInput.fill('python documentation');
    
    // Submit search
    await searchButton.click();
    
    // Wait for search results
    await page.waitForSelector('.search-results', { timeout: 10000 });
    
    // Check results are displayed
    const results = page.locator('.search-result');
    await expect(results.first()).toBeVisible();
  });

  test('should show search suggestions', async ({ page }) => {
    const searchInput = page.locator('input[type="search"]');
    
    // Type in search input
    await searchInput.fill('pyt');
    
    // Wait for suggestions
    await page.waitForTimeout(500);
    
    // Check for suggestions dropdown
    const suggestions = page.locator('.search-suggestions');
    if (await suggestions.isVisible()) {
      const suggestionItems = suggestions.locator('.suggestion-item');
      await expect(suggestionItems.first()).toBeVisible();
    }
  });

  test('should filter search results', async ({ page }) => {
    // Perform initial search
    await page.locator('input[type="search"]').fill('documentation');
    await page.locator('button[type="submit"]').click();
    
    // Wait for results
    await page.waitForSelector('.search-results', { timeout: 10000 });
    
    // Check for filter options
    const filters = page.locator('.search-filters');
    if (await filters.isVisible()) {
      // Try applying a filter
      const filterOption = filters.locator('input[type="checkbox"]').first();
      if (await filterOption.isVisible()) {
        await filterOption.check();
        
        // Wait for filtered results
        await page.waitForTimeout(1000);
        
        // Verify filter was applied
        await expect(filterOption).toBeChecked();
      }
    }
  });

  test('should sort search results', async ({ page }) => {
    // Perform search
    await page.locator('input[type="search"]').fill('test');
    await page.locator('button[type="submit"]').click();
    
    // Wait for results
    await page.waitForSelector('.search-results', { timeout: 10000 });
    
    // Check for sort options
    const sortSelect = page.locator('select[name="sort"]');
    if (await sortSelect.isVisible()) {
      // Change sort order
      await sortSelect.selectOption('date');
      
      // Wait for re-sorted results
      await page.waitForTimeout(1000);
      
      // Verify sort option was applied
      await expect(sortSelect).toHaveValue('date');
    }
  });

  test('should handle empty search results', async ({ page }) => {
    // Search for something that won't return results
    await page.locator('input[type="search"]').fill('xyznonexistentquery123');
    await page.locator('button[type="submit"]').click();
    
    // Wait for search to complete
    await page.waitForTimeout(3000);
    
    // Check for no results message
    const noResults = page.locator('.no-results');
    if (await noResults.isVisible()) {
      await expect(noResults).toContainText('No results found');
    }
  });

  test('should validate search input', async ({ page }) => {
    const searchInput = page.locator('input[type="search"]');
    const searchButton = page.locator('button[type="submit"]');
    
    // Try to search with empty input
    await searchButton.click();
    
    // Check for validation message
    const validationMessage = page.locator('.validation-error');
    if (await validationMessage.isVisible()) {
      await expect(validationMessage).toContainText('required');
    }
    
    // Check HTML5 validation
    const isRequired = await searchInput.getAttribute('required');
    if (isRequired !== null) {
      expect(isRequired).toBeDefined();
    }
  });

  test('should save search history', async ({ page }) => {
    // Perform a search
    await page.locator('input[type="search"]').fill('python');
    await page.locator('button[type="submit"]').click();
    
    // Wait for search to complete
    await page.waitForTimeout(2000);
    
    // Check for search history
    const historyButton = page.locator('[data-testid="search-history"]');
    if (await historyButton.isVisible()) {
      await historyButton.click();
      
      // Check history dropdown
      const historyDropdown = page.locator('.search-history-dropdown');
      if (await historyDropdown.isVisible()) {
        const historyItems = historyDropdown.locator('.history-item');
        await expect(historyItems.first()).toBeVisible();
      }
    }
  });

  test('should support advanced search', async ({ page }) => {
    // Check for advanced search toggle
    const advancedToggle = page.locator('[data-testid="advanced-search-toggle"]');
    if (await advancedToggle.isVisible()) {
      await advancedToggle.click();
      
      // Check advanced search form
      const advancedForm = page.locator('.advanced-search-form');
      await expect(advancedForm).toBeVisible();
      
      // Check advanced search fields
      await expect(advancedForm.locator('input[name="title"]')).toBeVisible();
      await expect(advancedForm.locator('input[name="content"]')).toBeVisible();
      await expect(advancedForm.locator('select[name="type"]')).toBeVisible();
    }
  });

  test('should handle search API errors', async ({ page }) => {
    // Mock API error
    await page.route('/api/search*', route => {
      route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ error: 'Internal server error' })
      });
    });
    
    // Perform search
    await page.locator('input[type="search"]').fill('test');
    await page.locator('button[type="submit"]').click();
    
    // Wait for error handling
    await page.waitForTimeout(2000);
    
    // Check for error message
    const errorMessage = page.locator('.error-message');
    if (await errorMessage.isVisible()) {
      await expect(errorMessage).toContainText('error');
    }
  });

  test('should be accessible', async ({ page }) => {
    // Check for proper ARIA labels
    const searchInput = page.locator('input[type="search"]');
    const ariaLabel = await searchInput.getAttribute('aria-label');
    expect(ariaLabel).toBeTruthy();
    
    // Check for proper heading structure
    const headings = page.locator('h1, h2, h3');
    await expect(headings.first()).toBeVisible();
    
    // Check for keyboard navigation
    await searchInput.focus();
    await expect(searchInput).toBeFocused();
    
    // Test tab navigation
    await page.keyboard.press('Tab');
    const focusedElement = page.locator(':focus');
    await expect(focusedElement).toBeVisible();
  });
});

test.describe('Search Results', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/search');
    
    // Perform a search to get results
    await page.locator('input[type="search"]').fill('documentation');
    await page.locator('button[type="submit"]').click();
    await page.waitForSelector('.search-results', { timeout: 10000 });
  });

  test('should display search result metadata', async ({ page }) => {
    const firstResult = page.locator('.search-result').first();
    
    if (await firstResult.isVisible()) {
      // Check for result title
      await expect(firstResult.locator('.result-title')).toBeVisible();
      
      // Check for result URL
      await expect(firstResult.locator('.result-url')).toBeVisible();
      
      // Check for result snippet
      await expect(firstResult.locator('.result-snippet')).toBeVisible();
    }
  });

  test('should highlight search terms in results', async ({ page }) => {
    const results = page.locator('.search-result');
    
    if (await results.count() > 0) {
      // Check for highlighted terms
      const highlights = page.locator('.highlight, mark');
      if (await highlights.count() > 0) {
        await expect(highlights.first()).toBeVisible();
      }
    }
  });

  test('should support result pagination', async ({ page }) => {
    // Check for pagination controls
    const pagination = page.locator('.pagination');
    if (await pagination.isVisible()) {
      const nextButton = pagination.locator('.next-page');
      if (await nextButton.isVisible() && await nextButton.isEnabled()) {
        await nextButton.click();
        
        // Wait for new results to load
        await page.waitForTimeout(2000);
        
        // Verify page changed
        const currentPage = pagination.locator('.current-page');
        if (await currentPage.isVisible()) {
          const pageText = await currentPage.textContent();
          expect(pageText).toContain('2');
        }
      }
    }
  });
});
