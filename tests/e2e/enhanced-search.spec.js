/**
 * Enhanced Search Tests
 * 
 * Comprehensive tests for the search functionality
 */

const { test, expect } = require('@playwright/test');

test.describe('Enhanced Search Tests', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to the search page
    await page.goto('/search.html');
    await expect(page).toHaveTitle(/Search/i);
  });

  test('should load search interface correctly', async ({ page }) => {
    // Verify search input is present
    await expect(page.locator('#searchInput')).toBeVisible();
    
    // Verify search button is present
    await expect(page.locator('#searchButton')).toBeVisible();
    
    // Verify filters are present
    await expect(page.locator('#searchFilters')).toBeVisible();
  });

  test('should perform basic search', async ({ page }) => {
    // Enter search term
    await page.locator('#searchInput').fill('example');
    
    // Click search button
    await page.locator('#searchButton').click();
    
    // Verify search results appear
    await expect(page.locator('#searchResults')).toBeVisible();
    
    // Verify results contain the search term
    await expect(page.locator('#searchResults')).toContainText('example');
  });

  test('should handle empty search results', async ({ page }) => {
    // Enter search term unlikely to match anything
    await page.locator('#searchInput').fill('xyznonexistentterm123');
    
    // Click search button
    await page.locator('#searchButton').click();
    
    // Verify no results message appears
    await expect(page.locator('#noResultsMessage')).toBeVisible();
  });

  test('should filter search results by category', async ({ page }) => {
    // Enter search term
    await page.locator('#searchInput').fill('example');
    
    // Click search button
    await page.locator('#searchButton').click();
    
    // Wait for results
    await expect(page.locator('#searchResults')).toBeVisible();
    
    // Get initial result count
    const initialResultCount = await page.locator('.search-result-item').count();
    
    // Apply category filter
    await page.locator('#categoryFilter').selectOption('api');
    
    // Verify results are filtered
    const filteredResultCount = await page.locator('.search-result-item').count();
    expect(filteredResultCount).toBeLessThanOrEqual(initialResultCount);
  });

  test('should sort search results', async ({ page }) => {
    // Enter search term
    await page.locator('#searchInput').fill('example');
    
    // Click search button
    await page.locator('#searchButton').click();
    
    // Wait for results
    await expect(page.locator('#searchResults')).toBeVisible();
    
    // Get initial first result title
    const initialFirstResultTitle = await page.locator('.search-result-item:first-child .result-title').textContent();
    
    // Change sort order
    await page.locator('#sortOrder').selectOption('date-desc');
    
    // Verify results are reordered
    const newFirstResultTitle = await page.locator('.search-result-item:first-child .result-title').textContent();
    expect(newFirstResultTitle).not.toEqual(initialFirstResultTitle);
  });

  test('should paginate search results', async ({ page }) => {
    // Enter search term likely to have many results
    await page.locator('#searchInput').fill('a');
    
    // Click search button
    await page.locator('#searchButton').click();
    
    // Wait for results
    await expect(page.locator('#searchResults')).toBeVisible();
    
    // Verify pagination controls are visible
    await expect(page.locator('#pagination')).toBeVisible();
    
    // Get first page results
    const firstPageResults = await page.locator('.search-result-item').allTextContents();
    
    // Go to second page
    await page.locator('#pagination .page-item:nth-child(3) a').click();
    
    // Verify results changed
    const secondPageResults = await page.locator('.search-result-item').allTextContents();
    expect(secondPageResults).not.toEqual(firstPageResults);
  });

  test('should highlight search terms in results', async ({ page }) => {
    // Enter search term
    await page.locator('#searchInput').fill('example');
    
    // Click search button
    await page.locator('#searchButton').click();
    
    // Wait for results
    await expect(page.locator('#searchResults')).toBeVisible();
    
    // Verify search term is highlighted
    const highlightedElements = await page.locator('.highlight').count();
    expect(highlightedElements).toBeGreaterThan(0);
  });

  test('should save recent searches', async ({ page }) => {
    // Enter and submit first search
    await page.locator('#searchInput').fill('first search');
    await page.locator('#searchButton').click();
    
    // Enter and submit second search
    await page.locator('#searchInput').fill('second search');
    await page.locator('#searchButton').click();
    
    // Click on recent searches dropdown
    await page.locator('#recentSearchesDropdown').click();
    
    // Verify recent searches are displayed
    await expect(page.locator('#recentSearchesList')).toContainText('first search');
    await expect(page.locator('#recentSearchesList')).toContainText('second search');
  });

  test('should perform advanced search with multiple criteria', async ({ page }) => {
    // Open advanced search
    await page.locator('#advancedSearchToggle').click();
    
    // Fill advanced search criteria
    await page.locator('#advancedKeywords').fill('example');
    await page.locator('#advancedCategory').selectOption('api');
    await page.locator('#advancedDateFrom').fill('2023-01-01');
    
    // Submit advanced search
    await page.locator('#advancedSearchButton').click();
    
    // Verify search results appear
    await expect(page.locator('#searchResults')).toBeVisible();
    
    // Verify applied filters are displayed
    await expect(page.locator('#appliedFilters')).toContainText('example');
    await expect(page.locator('#appliedFilters')).toContainText('api');
    await expect(page.locator('#appliedFilters')).toContainText('2023-01-01');
  });
});