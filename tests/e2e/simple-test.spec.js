/**
 * Simple Test to Verify Playwright Setup
 */

const { test, expect } = require('@playwright/test');

test.describe('Basic Playwright Tests', () => {
  test('should be able to navigate to a simple page', async ({ page }) => {
    // Navigate to a simple test page
    await page.goto('data:text/html,<html><body><h1>Test Page</h1><p>Hello World</p></body></html>');
    
    // Check that the page loaded
    await expect(page.locator('h1')).toHaveText('Test Page');
    await expect(page.locator('p')).toHaveText('Hello World');
  });

  test('should be able to interact with form elements', async ({ page }) => {
    // Create a simple form page
    const htmlContent = `
      <html>
        <body>
          <h1>Test Form</h1>
          <form id="testForm">
            <input type="text" id="nameInput" placeholder="Enter name">
            <button type="submit" id="submitBtn">Submit</button>
          </form>
          <div id="result"></div>
          <script>
            document.getElementById('testForm').addEventListener('submit', function(e) {
              e.preventDefault();
              const name = document.getElementById('nameInput').value;
              document.getElementById('result').textContent = 'Hello ' + name;
            });
          </script>
        </body>
      </html>
    `;
    
    await page.goto(`data:text/html,${encodeURIComponent(htmlContent)}`);
    
    // Fill the form
    await page.locator('#nameInput').fill('Playwright');
    await page.locator('#submitBtn').click();
    
    // Check the result
    await expect(page.locator('#result')).toHaveText('Hello Playwright');
  });

  test('should be able to test API endpoints', async ({ request }) => {
    // Test a simple API endpoint (httpbin for testing)
    const response = await request.get('https://httpbin.org/json');
    expect(response.status()).toBe(200);
    
    const data = await response.json();
    expect(data).toHaveProperty('slideshow');
  });

  test('should handle network conditions', async ({ page }) => {
    // Test offline behavior
    await page.context().setOffline(true);
    
    // Try to navigate to a page
    const response = await page.goto('https://example.com').catch(() => null);
    
    // Should fail when offline
    expect(response).toBeNull();
    
    // Restore online
    await page.context().setOffline(false);
    
    // Should work when online
    const onlineResponse = await page.goto('https://example.com');
    expect(onlineResponse.status()).toBe(200);
  });

  test('should support mobile viewport', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    
    const htmlContent = `
      <html>
        <head>
          <meta name="viewport" content="width=device-width, initial-scale=1">
          <style>
            .mobile-only { display: none; }
            @media (max-width: 480px) {
              .mobile-only { display: block; }
              .desktop-only { display: none; }
            }
          </style>
        </head>
        <body>
          <div class="mobile-only">Mobile View</div>
          <div class="desktop-only">Desktop View</div>
        </body>
      </html>
    `;
    
    await page.goto(`data:text/html,${encodeURIComponent(htmlContent)}`);
    
    // Check mobile-specific content is visible
    await expect(page.locator('.mobile-only')).toBeVisible();
    await expect(page.locator('.desktop-only')).toBeHidden();
  });

  test('should handle JavaScript execution', async ({ page }) => {
    const htmlContent = `
      <html>
        <body>
          <button id="clickMe">Click Me</button>
          <div id="counter">0</div>
          <script>
            let count = 0;
            document.getElementById('clickMe').addEventListener('click', function() {
              count++;
              document.getElementById('counter').textContent = count;
            });
          </script>
        </body>
      </html>
    `;
    
    await page.goto(`data:text/html,${encodeURIComponent(htmlContent)}`);
    
    // Initial state
    await expect(page.locator('#counter')).toHaveText('0');
    
    // Click button multiple times
    await page.locator('#clickMe').click();
    await expect(page.locator('#counter')).toHaveText('1');
    
    await page.locator('#clickMe').click();
    await expect(page.locator('#counter')).toHaveText('2');
    
    await page.locator('#clickMe').click();
    await expect(page.locator('#counter')).toHaveText('3');
  });

  test('should support file downloads', async ({ page }) => {
    const htmlContent = `
      <html>
        <body>
          <a href="data:text/plain,Hello World" download="test.txt">Download File</a>
        </body>
      </html>
    `;
    
    await page.goto(`data:text/html,${encodeURIComponent(htmlContent)}`);
    
    // Start waiting for download before clicking
    const downloadPromise = page.waitForEvent('download');
    await page.locator('a').click();
    const download = await downloadPromise;
    
    // Check download properties
    expect(download.suggestedFilename()).toBe('test.txt');
  });

  test('should handle cookies and local storage', async ({ page }) => {
    const htmlContent = `
      <html>
        <body>
          <button id="setCookie">Set Cookie</button>
          <button id="setStorage">Set Local Storage</button>
          <div id="cookieValue"></div>
          <div id="storageValue"></div>
          <script>
            document.getElementById('setCookie').addEventListener('click', function() {
              document.cookie = 'testCookie=cookieValue';
              document.getElementById('cookieValue').textContent = 'Cookie Set';
            });
            
            document.getElementById('setStorage').addEventListener('click', function() {
              localStorage.setItem('testKey', 'storageValue');
              document.getElementById('storageValue').textContent = 'Storage Set';
            });
          </script>
        </body>
      </html>
    `;
    
    await page.goto(`data:text/html,${encodeURIComponent(htmlContent)}`);
    
    // Test cookie
    await page.locator('#setCookie').click();
    await expect(page.locator('#cookieValue')).toHaveText('Cookie Set');
    
    // Test local storage
    await page.locator('#setStorage').click();
    await expect(page.locator('#storageValue')).toHaveText('Storage Set');
    
    // Verify storage value
    const storageValue = await page.evaluate(() => localStorage.getItem('testKey'));
    expect(storageValue).toBe('storageValue');
  });
});
