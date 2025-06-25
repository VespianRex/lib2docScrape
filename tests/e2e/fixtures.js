/**
 * Test Fixtures
 * 
 * Common fixtures for Playwright tests
 */

const { test: base } = require('@playwright/test');
const { mockSuccessResponse, mockErrorResponse } = require('./test-utils');

/**
 * Extend the base test with custom fixtures
 */
const test = base.extend({
  /**
   * Authenticated page fixture
   */
  authenticatedPage: async ({ page }, use) => {
    // Simulate login
    await page.goto('/login.html');
    await page.locator('#username').fill('testuser');
    await page.locator('#password').fill('password');
    await page.locator('#loginButton').click();
    
    // Wait for login to complete
    await page.waitForURL('**/dashboard.html');
    
    // Use the authenticated page
    await use(page);
  },
  
  /**
   * Page with mocked scraping data
   */
  pageWithMockedScraping: async ({ page }, use) => {
    // Mock scraping API response
    await mockSuccessResponse(page, '**/api/scrape', {
      success: true,
      url: 'https://example.com',
      pages_scraped: 10,
      time_taken: 2.5,
      results: [
        {
          title: 'Example Domain',
          url: 'https://example.com',
          content: 'This domain is for use in illustrative examples in documents.',
          metadata: {
            last_updated: '2023-01-01',
            author: 'Example Author',
          }
        },
        {
          title: 'Example Page',
          url: 'https://example.com/page',
          content: 'This is an example page.',
          metadata: {
            last_updated: '2023-01-02',
            author: 'Example Author',
          }
        }
      ]
    });
    
    // Use the page with mocked data
    await use(page);
  },
  
  /**
   * Page with mocked search data
   */
  pageWithMockedSearch: async ({ page }, use) => {
    // Mock search API response
    await mockSuccessResponse(page, '**/api/search*', {
      success: true,
      query: 'example',
      total_results: 25,
      page: 1,
      page_size: 10,
      results: Array.from({ length: 10 }, (_, i) => ({
        id: `result-${i}`,
        title: `Example Result ${i}`,
        url: `https://example.com/result-${i}`,
        content: `This is example result ${i} containing the search term example.`,
        highlight: `This is <mark>example</mark> result ${i} containing the search term <mark>example</mark>.`,
        score: 0.9 - (i * 0.05),
        last_updated: `2023-01-${i + 1}`,
      }))
    });
    
    // Use the page with mocked search data
    await use(page);
  },
  
  /**
   * Page with mocked visualization data
   */
  pageWithMockedVisualizations: async ({ page }, use) => {
    // Mock visualization API responses
    await mockSuccessResponse(page, '**/api/visualizations/coverage', {
      success: true,
      labels: ['Module 1', 'Module 2', 'Module 3', 'Module 4', 'Module 5'],
      datasets: [
        {
          label: 'Documentation Coverage',
          data: [85, 70, 95, 60, 80],
        }
      ]
    });
    
    await mockSuccessResponse(page, '**/api/visualizations/dependencies', {
      success: true,
      nodes: Array.from({ length: 10 }, (_, i) => ({
        id: `node-${i}`,
        label: `Module ${i}`,
        size: 10 + (i * 5),
      })),
      edges: [
        { source: 'node-0', target: 'node-1' },
        { source: 'node-0', target: 'node-2' },
        { source: 'node-1', target: 'node-3' },
        { source: 'node-2', target: 'node-4' },
        { source: 'node-3', target: 'node-5' },
        { source: 'node-5', target: 'node-6' },
        { source: 'node-6', target: 'node-7' },
        { source: 'node-7', target: 'node-8' },
        { source: 'node-8', target: 'node-9' },
      ]
    });
    
    await mockSuccessResponse(page, '**/api/visualizations/timeline', {
      success: true,
      labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
      datasets: [
        {
          label: 'Documentation Updates',
          data: [12, 19, 8, 15, 20, 14],
        }
      ]
    });
    
    // Use the page with mocked visualization data
    await use(page);
  },
  
  /**
   * Page with error states
   */
  pageWithErrors: async ({ page }, use) => {
    // Mock various error responses
    await mockErrorResponse(page, '**/api/scrape', 500, {
      success: false,
      error: 'Internal Server Error',
      message: 'An unexpected error occurred while scraping the documentation.'
    });
    
    await mockErrorResponse(page, '**/api/search*', 400, {
      success: false,
      error: 'Bad Request',
      message: 'Invalid search query parameters.'
    });
    
    await mockErrorResponse(page, '**/api/visualizations/*', 404, {
      success: false,
      error: 'Not Found',
      message: 'Visualization data not found.'
    });
    
    // Use the page with error states
    await use(page);
  },
});

module.exports = { test };