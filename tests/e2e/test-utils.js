/**
 * Test Utilities
 * 
 * Helper functions for Playwright tests
 */

/**
 * Fills a form with the given data
 * @param {import('@playwright/test').Page} page - Playwright page object
 * @param {Object} formData - Object containing form field selectors and values
 */
async function fillForm(page, formData) {
  for (const [selector, value] of Object.entries(formData)) {
    const element = await page.locator(selector);
    
    // Check if element is a select
    const tagName = await element.evaluate(el => el.tagName.toLowerCase());
    
    if (tagName === 'select') {
      await element.selectOption(value);
    } else {
      await element.fill(value);
    }
  }
}

/**
 * Waits for network requests to complete
 * @param {import('@playwright/test').Page} page - Playwright page object
 */
async function waitForNetworkIdle(page) {
  await page.waitForLoadState('networkidle', { timeout: 10000 });
}

/**
 * Checks if an element contains specific text
 * @param {import('@playwright/test').Page} page - Playwright page object
 * @param {string} selector - Element selector
 * @param {string} text - Text to check for
 * @returns {Promise<boolean>} - Whether the element contains the text
 */
async function elementContainsText(page, selector, text) {
  const content = await page.locator(selector).textContent();
  return content.includes(text);
}

/**
 * Takes a screenshot and saves it with a timestamp
 * @param {import('@playwright/test').Page} page - Playwright page object
 * @param {string} name - Screenshot name
 */
async function takeScreenshot(page, name) {
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
  await page.screenshot({ path: `./test-results/screenshots/${name}-${timestamp}.png` });
}

/**
 * Mocks a successful API response
 * @param {import('@playwright/test').Page} page - Playwright page object
 * @param {string} url - URL to mock
 * @param {Object} responseData - Response data
 */
async function mockSuccessResponse(page, url, responseData) {
  await page.route(url, route => {
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(responseData),
    });
  });
}

/**
 * Mocks an error API response
 * @param {import('@playwright/test').Page} page - Playwright page object
 * @param {string} url - URL to mock
 * @param {number} status - HTTP status code
 * @param {Object} errorData - Error data
 */
async function mockErrorResponse(page, url, status, errorData) {
  await page.route(url, route => {
    route.fulfill({
      status,
      contentType: 'application/json',
      body: JSON.stringify(errorData),
    });
  });
}

/**
 * Checks if an element is visible in the viewport
 * @param {import('@playwright/test').Page} page - Playwright page object
 * @param {string} selector - Element selector
 * @returns {Promise<boolean>} - Whether the element is visible in the viewport
 */
async function isElementInViewport(page, selector) {
  return page.evaluate(selector => {
    const element = document.querySelector(selector);
    if (!element) return false;
    
    const rect = element.getBoundingClientRect();
    return (
      rect.top >= 0 &&
      rect.left >= 0 &&
      rect.bottom <= window.innerHeight &&
      rect.right <= window.innerWidth
    );
  }, selector);
}

/**
 * Waits for an element to be stable (no movement)
 * @param {import('@playwright/test').Page} page - Playwright page object
 * @param {string} selector - Element selector
 * @param {number} timeout - Timeout in milliseconds
 */
async function waitForElementStable(page, selector, timeout = 5000) {
  await page.waitForFunction(
    (selector) => {
      const element = document.querySelector(selector);
      if (!element) return false;
      
      let lastRect = element.getBoundingClientRect();
      
      return new Promise(resolve => {
        let checkCount = 0;
        const interval = setInterval(() => {
          const currentRect = element.getBoundingClientRect();
          const isStable = (
            lastRect.top === currentRect.top &&
            lastRect.left === currentRect.left &&
            lastRect.width === currentRect.width &&
            lastRect.height === currentRect.height
          );
          
          lastRect = currentRect;
          checkCount++;
          
          if (isStable || checkCount > 10) {
            clearInterval(interval);
            resolve(true);
          }
        }, 100);
      });
    },
    selector,
    { timeout }
  );
}

module.exports = {
  fillForm,
  waitForNetworkIdle,
  elementContainsText,
  takeScreenshot,
  mockSuccessResponse,
  mockErrorResponse,
  isElementInViewport,
  waitForElementStable,
};