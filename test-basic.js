const { test, expect } = require('@playwright/test');

test('basic test', async ({ page }) => {
  console.log('Starting basic test...');
  await page.goto('data:text/html,<h1>Hello World</h1>');
  console.log('Page loaded');
  await expect(page.locator('h1')).toHaveText('Hello World');
  console.log('Test completed successfully');
});
