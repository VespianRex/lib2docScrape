/**
 * Playwright Configuration for GUI Testing (Standalone)
 * 
 * Simplified configuration for testing GUI components without server dependencies
 */

const { defineConfig, devices } = require('@playwright/test');

module.exports = defineConfig({
  // Test directory for GUI tests
  testDir: './tests/gui',
  
  // Run tests in files in parallel
  fullyParallel: true,
  
  // Retry configuration
  retries: 0,
  
  // Use fewer workers to avoid resource issues
  workers: 2,
  
  // Reporter to use
  reporter: [
    ['list'],
    ['html', { outputFolder: 'playwright-report-gui' }]
  ],
  
  // Shared settings for all the projects below
  use: {
    // Use static HTML files for testing
    baseURL: 'file://' + __dirname + '/tests/gui/fixtures/',
    
    // Collect trace when retrying the failed test
    trace: 'on-first-retry',
    
    // Take screenshot on failure
    screenshot: 'only-on-failure',
    
    // Reduced timeouts to prevent hanging
    actionTimeout: 5000,
    navigationTimeout: 10000,
  },

  // Configure projects for major browsers (reduced set)
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'], headless: true },
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'], headless: true },
    },
  ],
  
  // Test timeout (reduced to prevent hanging)
  timeout: 30000,
  
  // Expect timeout
  expect: {
    timeout: 5000,
  },
});
