const { test, expect } = require('@playwright/test');

test('GUI server connection test', async ({ page }) => {
  console.log('Starting GUI server test...');
  
  try {
    // Connect to the running GUI server
    await page.goto('http://127.0.0.1:47737');
    console.log('Connected to GUI server');
    
    // Check if the page loaded
    await expect(page.locator('title')).toContainText('Documentation Scraping Dashboard');
    console.log('Page title verified');
    
    // Check for main navigation
    await expect(page.locator('.navbar-brand')).toHaveText('Lib2DocScrape');
    console.log('Navigation verified');
    
    // Check for main content area
    await expect(page.locator('body')).toBeVisible();
    console.log('Body content verified');
    
    console.log('GUI server test completed successfully!');
  } catch (error) {
    console.error('Test failed:', error.message);
    throw error;
  }
});
