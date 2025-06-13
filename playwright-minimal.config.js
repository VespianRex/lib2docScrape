/**
 * Minimal Playwright Configuration for Testing
 */

const { defineConfig, devices } = require('@playwright/test');

module.exports = defineConfig({
  // Test directory
  testDir: './tests/e2e',
  
  // Run tests in files in parallel
  fullyParallel: false,
  
  // Retry on CI only
  retries: 0,
  
  // Workers
  workers: 1,
  
  // Reporter to use
  reporter: 'list',
  
  // Shared settings for all the projects below
  use: {
    // Collect trace when retrying the failed test
    trace: 'on-first-retry',
    
    // Take screenshot on failure
    screenshot: 'only-on-failure',
    
    // Global test timeout
    actionTimeout: 5000,
    navigationTimeout: 10000,
  },

  // Configure projects for major browsers
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'], headless: true },
    },
  ],

  // Test timeout
  timeout: 30000,
  
  // Expect timeout
  expect: {
    timeout: 5000,
  },
});
