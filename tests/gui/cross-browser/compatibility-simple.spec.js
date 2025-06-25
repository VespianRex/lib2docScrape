/**
 * Cross-Browser Compatibility Tests (Simplified)
 * 
 * Tests GUI components across different browsers and viewports
 */

const { test, expect } = require('@playwright/test');

test.describe('Cross-Browser GUI Compatibility', () => {
  
  test.beforeEach(async ({ page }) => {
    // Navigate to the test fixture
    await page.goto('index.html');
    await page.waitForLoadState('networkidle');
  });

  test('should load page correctly in all browsers', async ({ page }) => {
    // Check if the page loads with correct title
    await expect(page).toHaveTitle(/Lib2DocScrape/);
    
    // Check if main navigation is visible
    const nav = page.locator('nav.navbar');
    await expect(nav).toBeVisible();
    
    // Check if brand is visible
    const brand = page.locator('.navbar-brand');
    await expect(brand).toContainText('Lib2DocScrape');
  });

  test('should display navigation correctly', async ({ page }) => {
    // Check navigation links
    const homeLink = page.locator('[data-testid="nav-home"]');
    const configLink = page.locator('[data-testid="nav-config"]');
    const resultsLink = page.locator('[data-testid="nav-results"]');
    
    await expect(homeLink).toBeVisible();
    await expect(configLink).toBeVisible();
    await expect(resultsLink).toBeVisible();
    
    // Check icons are present
    await expect(homeLink.locator('i.bi-play-circle')).toBeVisible();
    await expect(configLink.locator('i.bi-gear')).toBeVisible();
  });

  test('should render form elements correctly', async ({ page }) => {
    // Check form is visible
    const form = page.locator('[data-testid="scraper-form"]');
    await expect(form).toBeVisible();
    
    // Check input fields
    const libraryName = page.locator('[data-testid="library-name"]');
    const baseUrl = page.locator('[data-testid="base-url"]');
    const maxDepth = page.locator('[data-testid="max-depth"]');
    
    await expect(libraryName).toBeVisible();
    await expect(baseUrl).toBeVisible();
    await expect(maxDepth).toBeVisible();
    
    // Check select dropdown
    const backendSelect = page.locator('[data-testid="backend-select"]');
    await expect(backendSelect).toBeVisible();
    
    // Check submit button
    const submitButton = page.locator('[data-testid="start-scraping"]');
    await expect(submitButton).toBeVisible();
    await expect(submitButton).toContainText('Start Scraping');
  });

  test('should handle form interaction', async ({ page }) => {
    // Fill out the form
    await page.fill('[data-testid="library-name"]', 'React');
    await page.fill('[data-testid="base-url"]', 'https://react.dev/learn');
    await page.selectOption('[data-testid="backend-select"]', 'playwright');
    
    // Check values are set
    await expect(page.locator('[data-testid="library-name"]')).toHaveValue('React');
    await expect(page.locator('[data-testid="base-url"]')).toHaveValue('https://react.dev/learn');
    await expect(page.locator('[data-testid="backend-select"]')).toHaveValue('playwright');
  });

  test('should display status panels correctly', async ({ page }) => {
    // Check connection status
    const connectionStatus = page.locator('[data-testid="connection-status"]');
    await expect(connectionStatus).toBeVisible();
    await expect(connectionStatus).toContainText('Disconnected');
    
    // Check updates panel
    const updatesList = page.locator('[data-testid="updates-list"]');
    await expect(updatesList).toBeVisible();
    
    // Check quick actions
    const viewResults = page.locator('[data-testid="view-results"]');
    const downloadResults = page.locator('[data-testid="download-results"]');
    
    await expect(viewResults).toBeVisible();
    await expect(downloadResults).toBeVisible();
  });

  test('should show progress section when form is submitted', async ({ page }) => {
    // Fill and submit form
    await page.fill('[data-testid="library-name"]', 'Vue');
    await page.fill('[data-testid="base-url"]', 'https://vuejs.org/guide/');
    
    // Submit form
    await page.click('[data-testid="start-scraping"]');
    
    // Loading overlay should appear briefly
    await expect(page.locator('[data-testid="loading-overlay"]')).toBeVisible();
    
    // Wait for loading to finish
    await expect(page.locator('[data-testid="loading-overlay"]')).toBeHidden({ timeout: 2000 });
    
    // Progress section should become visible
    await expect(page.locator('[data-testid="progress-section"]')).toBeVisible();
    
    // Connection status should change
    await expect(page.locator('[data-testid="connection-status"]')).toContainText('Connected');
  });

  test('should be responsive on mobile viewports', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    
    // Check if navbar toggle is visible on mobile
    const navbarToggle = page.locator('.navbar-toggler');
    await expect(navbarToggle).toBeVisible();
    
    // Check if main content is still accessible
    const form = page.locator('[data-testid="scraper-form"]');
    await expect(form).toBeVisible();
    
    // Check if form fields stack properly on mobile
    const libraryName = page.locator('[data-testid="library-name"]');
    await expect(libraryName).toBeVisible();
    
    // Check if buttons are still clickable
    const submitButton = page.locator('[data-testid="start-scraping"]');
    await expect(submitButton).toBeVisible();
  });

  test('should handle keyboard navigation', async ({ page }) => {
    // Tab through form fields
    await page.keyboard.press('Tab'); // Should focus on library name
    
    const libraryName = page.locator('[data-testid="library-name"]');
    await expect(libraryName).toBeFocused();
    
    // Type in focused field
    await page.keyboard.type('Angular');
    await expect(libraryName).toHaveValue('Angular');
    
    // Tab to next field
    await page.keyboard.press('Tab');
    const baseUrl = page.locator('[data-testid="base-url"]');
    await expect(baseUrl).toBeFocused();
  });

  test('should maintain visual consistency across browsers', async ({ page, browserName }) => {
    // Check if Bootstrap classes are applied correctly
    const navbar = page.locator('nav.navbar');
    await expect(navbar).toHaveClass(/navbar-dark/);
    await expect(navbar).toHaveClass(/bg-dark/);
    
    // Check if form has proper Bootstrap styling
    const formControls = page.locator('.form-control');
    await expect(formControls.first()).toBeVisible();
    
    // Check if buttons have proper styling
    const primaryButton = page.locator('.btn-primary');
    await expect(primaryButton).toBeVisible();
    
    // Take a screenshot for visual comparison
    await page.screenshot({ 
      path: `tests/gui/screenshots/main-page-${browserName}.png`,
      fullPage: true 
    });
  });

  test('should handle error states gracefully', async ({ page }) => {
    // Try to submit form with invalid data
    await page.fill('[data-testid="library-name"]', '');
    await page.fill('[data-testid="base-url"]', 'not-a-url');
    
    // Attempt to submit (HTML5 validation should prevent it)
    await page.click('[data-testid="start-scraping"]');
    
    // Form should not submit (no progress section should appear)
    await page.waitForTimeout(500);
    const progressSection = page.locator('[data-testid="progress-section"]');
    await expect(progressSection).toBeHidden();
  });

  test('should support different screen sizes', async ({ page }) => {
    const sizes = [
      { width: 1920, height: 1080, name: 'desktop-large' },
      { width: 1366, height: 768, name: 'desktop' },
      { width: 768, height: 1024, name: 'tablet' },
      { width: 375, height: 667, name: 'mobile' }
    ];
    
    for (const size of sizes) {
      await page.setViewportSize({ width: size.width, height: size.height });
      
      // Check if main elements are still visible and accessible
      const brand = page.locator('.navbar-brand');
      await expect(brand).toBeVisible();
      
      const form = page.locator('[data-testid="scraper-form"]');
      await expect(form).toBeVisible();
      
      // For mobile, check navbar toggle
      if (size.width < 992) {
        const toggle = page.locator('.navbar-toggler');
        await expect(toggle).toBeVisible();
      }
      
      // Take screenshot for each size
      await page.screenshot({ 
        path: `tests/gui/screenshots/responsive-${size.name}.png`,
        fullPage: false 
      });
    }
  });
});
