import { test, expect } from '@playwright/test';

test.describe('Scraping GUI End-to-End Tests', () => {
  const baseUrl = 'http://localhost:3000'; // Adjust if needed

  test('should load scraping dashboard', async ({ page }) => {
    await page.goto(`${baseUrl}/`);
    await expect(page).toHaveTitle(/Documentation Scraping Dashboard|Lib2DocScrape/i);
  });

  test('should start scraping with valid URL and display results (live backend)', async ({ page }) => {
    await page.goto(`${baseUrl}/`);

    // Input a valid URL
    await page.fill('#docUrl', 'https://example.com');
    await page.click('#start-scraping-button');

    // Wait for scraping results to appear
    const results = await page.waitForSelector('#scraping-results');
    await expect(results.isVisible()).resolves.toBe(true);

    // Verify some expected content in results
    const content = await results.textContent();
    expect(content).toContain('example.com');
  });

  test('should handle invalid URL format gracefully', async ({ page }) => {
    await page.goto(`${baseUrl}/`);

    await page.fill('#docUrl', 'invalid-url');
    await page.click('#start-scraping-button');

    const errorMessage = await page.waitForSelector('#error-message');
    await expect(errorMessage.isVisible()).resolves.toBe(true);
    await expect(errorMessage.textContent()).resolves.toMatch(/Invalid URL format|Network error/i);
  });

  test('should handle network failure (mock backend)', async ({ page }) => {
    await page.route('**/crawl', route => {
      route.abort('failed');
    });

    await page.goto(`${baseUrl}/`);
    await page.fill('#docUrl', 'https://example.com');
    await page.click('#start-scraping-button');

    const errorMessage = await page.waitForSelector('#error-message');
    await expect(errorMessage.isVisible()).resolves.toBe(true);
    await expect(errorMessage.textContent()).resolves.toMatch(/Network error/i);
  });

  test('should handle backend timeout (mock backend)', async ({ page }) => {
    await page.route('**/crawl', async route => {
      // Delay response to simulate timeout
      await new Promise(resolve => setTimeout(resolve, 10000));
      route.fulfill({
        status: 504,
        contentType: 'application/json',
        body: JSON.stringify({ error: 'Timeout' }),
      });
    });

    await page.goto(`${baseUrl}/`);
    await page.fill('#docUrl', 'https://example.com');
    await page.click('#start-scraping-button');

    const errorMessage = await page.waitForSelector('#error-message');
    await expect(errorMessage.isVisible()).resolves.toBe(true);
    await expect(errorMessage.textContent()).resolves.toMatch(/Timeout/i);
  });

  test('should allow backend selection', async ({ page }) => {
    await page.goto(`${baseUrl}/`);
    
    // Test backend selection
    await page.selectOption('#backend', 'crawl4ai');
    const selectedValue = await page.inputValue('#backend');
    expect(selectedValue).toBe('crawl4ai');
    
    // Check if description updates
    const description = await page.textContent('#backendDescription');
    expect(description).toContain('AI-powered');
  });

  test('should allow configuration preset changes', async ({ page }) => {
    await page.goto(`${baseUrl}/`);
    
    // Test preset selection
    await page.selectOption('#configPreset', 'performance');
    
    // Check if form values update
    const maxDepth = await page.inputValue('#maxDepth');
    const maxPages = await page.inputValue('#maxPages');
    
    expect(parseInt(maxDepth)).toBeLessThanOrEqual(3); // Performance preset should have lower values
    expect(parseInt(maxPages)).toBeLessThanOrEqual(50);
  });

  test('should show help modal', async ({ page }) => {
    await page.goto(`${baseUrl}/`);
    
    // Click help button
    await page.click('#helpBtn');
    
    // Wait for modal to appear
    const modal = await page.waitForSelector('#helpModal');
    await expect(modal.isVisible()).resolves.toBe(true);
    
    // Check modal content
    const modalContent = await modal.textContent();
    expect(modalContent).toContain('Quick Start Guide');
  });

  test('should handle form validation', async ({ page }) => {
    await page.goto(`${baseUrl}/`);
    
    // Try to submit without URL
    await page.click('#start-scraping-button');
    
    // Check if browser validation prevents submission
    const urlInput = page.locator('#docUrl');
    const validationMessage = await urlInput.evaluate((el: HTMLInputElement) => el.validationMessage);
    expect(validationMessage).toBeTruthy();
  });

  test('should show benchmark modal', async ({ page }) => {
    await page.goto(`${baseUrl}/`);
    
    // Click benchmark button
    await page.click('#benchmarkBtn');
    
    // Wait for modal to appear
    const modal = await page.waitForSelector('#benchmarkModal');
    await expect(modal.isVisible()).resolves.toBe(true);
    
    // Check modal content
    const modalContent = await modal.textContent();
    expect(modalContent).toContain('Backend Performance Benchmark');
  });

  test('should handle successful scraping response', async ({ page }) => {
    // Mock successful response
    await page.route('**/crawl', route => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          status: 'success',
          url: 'https://example.com',
          scraping_id: 'test123',
          results: []
        }),
      });
    });

    await page.goto(`${baseUrl}/`);
    await page.fill('#docUrl', 'https://example.com');
    await page.click('#start-scraping-button');

    // Wait for success message
    const successMessage = await page.waitForSelector('#success-message');
    await expect(successMessage.isVisible()).resolves.toBe(true);
    
    // Check if results section appears
    const results = await page.waitForSelector('#scraping-results');
    await expect(results.isVisible()).resolves.toBe(true);
  });

  test('should search for library documentation', async ({ page }) => {
    // Mock library search response
    await page.route('**/discover', route => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          urls: {
            'https://requests.readthedocs.io/': { source: 'ReadTheDocs' },
            'https://docs.python-requests.org/': { source: 'PyPI Documentation' },
            'https://github.com/psf/requests': { source: 'GitHub' }
          }
        }),
      });
    });

    await page.goto(`${baseUrl}/`);
    
    // Enter library name
    await page.fill('#docUrl', 'requests');
    
    // Click search button
    await page.click('#searchLibraryBtn');
    
    // Wait for search results to appear
    const searchResults = await page.waitForSelector('#librarySearchResults');
    await expect(searchResults.isVisible()).resolves.toBe(true);
    
    // Check that results are displayed
    const resultsList = await page.textContent('#searchResultsList');
    expect(resultsList).toContain('requests.readthedocs.io');
    expect(resultsList).toContain('ReadTheDocs');
  });

  test('should select library URL from search results', async ({ page }) => {
    // Mock library search response
    await page.route('**/discover', route => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          urls: {
            'https://fastapi.tiangolo.com/': { source: 'Official Documentation' }
          }
        }),
      });
    });

    await page.goto(`${baseUrl}/`);
    
    // Search for library
    await page.fill('#docUrl', 'fastapi');
    await page.click('#searchLibraryBtn');
    
    // Wait for results and select first one
    await page.waitForSelector('#librarySearchResults');
    await page.click('button:has-text("Use This")');
    
    // Check that URL was populated
    const urlValue = await page.inputValue('#docUrl');
    expect(urlValue).toBe('https://fastapi.tiangolo.com/');
    
    // Check that search results are hidden
    const searchResults = page.locator('#librarySearchResults');
    await expect(searchResults).toHaveClass(/d-none/);
  });

  test('should handle library search with no results', async ({ page }) => {
    // Mock empty search response
    await page.route('**/discover', route => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ urls: {} }),
      });
    });

    await page.goto(`${baseUrl}/`);
    
    // Search for non-existent library
    await page.fill('#docUrl', 'nonexistentlibrary123');
    await page.click('#searchLibraryBtn');
    
    // Wait for results
    await page.waitForSelector('#librarySearchResults');
    
    // Check for no results message
    const resultsList = await page.textContent('#searchResultsList');
    expect(resultsList).toContain('No documentation found');
  });

  test('should handle library search errors', async ({ page }) => {
    // Mock search error
    await page.route('**/discover', route => {
      route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ error: 'Search service unavailable' }),
      });
    });

    await page.goto(`${baseUrl}/`);
    
    // Try to search
    await page.fill('#docUrl', 'requests');
    await page.click('#searchLibraryBtn');
    
    // Wait for error message
    const errorMessage = await page.waitForSelector('#error-message');
    await expect(errorMessage.isVisible()).resolves.toBe(true);
    
    const errorText = await errorMessage.textContent();
    expect(errorText).toContain('Search failed');
  });

  test('should detect URLs and skip search', async ({ page }) => {
    await page.goto(`${baseUrl}/`);
    
    // Enter a URL
    await page.fill('#docUrl', 'https://docs.python.org');
    await page.click('#searchLibraryBtn');
    
    // Should show success message about URL detection
    const successMessage = await page.waitForSelector('#success-message');
    await expect(successMessage.isVisible()).resolves.toBe(true);
    
    const successText = await successMessage.textContent();
    expect(successText).toContain('URL detected');
  });

  test('should close search results', async ({ page }) => {
    // Mock library search response
    await page.route('**/discover', route => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          urls: {
            'https://example.com/docs': { source: 'Test' }
          }
        }),
      });
    });

    await page.goto(`${baseUrl}/`);
    
    // Search and show results
    await page.fill('#docUrl', 'test');
    await page.click('#searchLibraryBtn');
    await page.waitForSelector('#librarySearchResults');
    
    // Close results
    await page.click('#closeSearchResults');
    
    // Check that results are hidden
    const searchResults = page.locator('#librarySearchResults');
    await expect(searchResults).toHaveClass(/d-none/);
  });
});
