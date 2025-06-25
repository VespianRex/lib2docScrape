/**
 * Cross-Browser Compatibility Tests
 * 
 * Playwright tests for browser compatibility and responsive design
 */

const { test, expect, devices } = require('@playwright/test');

// Define test configurations for different browsers and devices
const testConfigs = [
  { name: 'Desktop Chrome', browserName: 'chromium', viewport: { width: 1920, height: 1080 } },
  { name: 'Desktop Firefox', browserName: 'firefox', viewport: { width: 1920, height: 1080 } },
  { name: 'Desktop Safari', browserName: 'webkit', viewport: { width: 1920, height: 1080 } },
  { name: 'Tablet iPad', ...devices['iPad'] },
  { name: 'Mobile iPhone', ...devices['iPhone 12'] },
  { name: 'Mobile Android', ...devices['Pixel 5'] }
];

test.describe('Cross-Browser Compatibility', () => {
  
  testConfigs.forEach(config => {
    test.describe(`${config.name}`, () => {
      
      test.beforeEach(async ({ page, context }) => {
        // Set viewport if specified
        if (config.viewport) {
          await page.setViewportSize(config.viewport);
        }
        
        // Navigate to the application
        await page.goto('/');
        
        // Wait for the page to be fully loaded
        await page.waitForLoadState('networkidle');
      });

      test('should load homepage correctly', async ({ page }) => {
        // Check page title
        await expect(page).toHaveTitle(/Lib2DocScrape/);
        
        // Check main navigation is visible
        const navbar = page.locator('nav.navbar');
        await expect(navbar).toBeVisible();
        
        // Check main content area
        const mainContent = page.locator('main.container');
        await expect(mainContent).toBeVisible();
        
        // Check that essential elements are present
        const brandLink = page.locator('.navbar-brand');
        await expect(brandLink).toBeVisible();
        await expect(brandLink).toHaveText('Lib2DocScrape');
      });

      test('should have responsive navigation', async ({ page }) => {
        const navbar = page.locator('nav.navbar');
        const navToggler = page.locator('.navbar-toggler');
        const navCollapse = page.locator('.navbar-collapse');
        
        await expect(navbar).toBeVisible();
        
        // Check if we're in mobile viewport
        const viewportSize = page.viewportSize();
        if (viewportSize.width < 992) { // Bootstrap lg breakpoint
          // Mobile: toggler should be visible
          await expect(navToggler).toBeVisible();
          
          // Navigation should be collapsed initially
          await expect(navCollapse).not.toHaveClass(/show/);
          
          // Click toggler to expand navigation
          await navToggler.click();
          await expect(navCollapse).toHaveClass(/show/);
          
          // Navigation links should be visible
          const navLinks = page.locator('.nav-link');
          await expect(navLinks.first()).toBeVisible();
        } else {
          // Desktop: toggler should be hidden, navigation expanded
          await expect(navToggler).toBeHidden();
          await expect(navCollapse).toBeVisible();
          
          // Navigation links should be visible
          const navLinks = page.locator('.nav-link');
          await expect(navLinks.first()).toBeVisible();
        }
      });

      test('should navigate between pages', async ({ page }) => {
        // Test navigation to different pages
        const testRoutes = [
          { selector: 'a[href="/config"]', expectedUrl: '/config', expectedContent: 'Configuration' },
          { selector: 'a[href="/results"]', expectedUrl: '/results', expectedContent: 'Results' },
          { selector: 'a[href="/home"]', expectedUrl: '/home', expectedContent: 'Welcome' }
        ];

        for (const route of testRoutes) {
          // Click navigation link
          await page.click(route.selector);
          
          // Wait for navigation
          await page.waitForURL(`**${route.expectedUrl}`);
          
          // Verify we're on the correct page
          expect(page.url()).toContain(route.expectedUrl);
          
          // Check that the page content loaded
          const pageContent = page.locator('main');
          await expect(pageContent).toBeVisible();
          
          // Go back to home for next iteration
          await page.goto('/');
          await page.waitForLoadState('networkidle');
        }
      });

      test('should display forms correctly', async ({ page }) => {
        // Navigate to a page with forms (assuming home page has quick start form)
        await page.goto('/');
        
        // Check for form elements
        const urlInput = page.locator('input[type="url"]').first();
        if (await urlInput.isVisible()) {
          await expect(urlInput).toBeVisible();
          await expect(urlInput).toBeEditable();
          
          // Test form interaction
          await urlInput.fill('https://docs.python.org');
          await expect(urlInput).toHaveValue('https://docs.python.org');
          
          // Check for submit button
          const submitButton = page.locator('button').filter({ hasText: /start|scrape/i }).first();
          if (await submitButton.isVisible()) {
            await expect(submitButton).toBeVisible();
            await expect(submitButton).toBeEnabled();
          }
        }
      });

      test('should handle loading states', async ({ page }) => {
        // Check for loading indicator element
        const loadingIndicator = page.locator('.loading-indicator');
        
        // Loading indicator should be hidden initially
        await expect(loadingIndicator).toBeHidden();
        
        // Test loading state (would be triggered by form submission or navigation)
        // This is a visual test to ensure the loading indicator works across browsers
        await page.evaluate(() => {
          const indicator = document.querySelector('.loading-indicator');
          if (indicator) {
            indicator.style.display = 'block';
          }
        });
        
        await expect(loadingIndicator).toBeVisible();
        
        // Hide loading indicator
        await page.evaluate(() => {
          const indicator = document.querySelector('.loading-indicator');
          if (indicator) {
            indicator.style.display = 'none';
          }
        });
        
        await expect(loadingIndicator).toBeHidden();
      });

      test('should display content readably', async ({ page }) => {
        // Check text contrast and readability
        const headings = page.locator('h1, h2, h3, h4, h5, h6');
        const paragraphs = page.locator('p');
        
        // Ensure headings are visible and have content
        const headingCount = await headings.count();
        if (headingCount > 0) {
          await expect(headings.first()).toBeVisible();
          await expect(headings.first()).not.toBeEmpty();
        }
        
        // Ensure paragraphs are visible and readable
        const paragraphCount = await paragraphs.count();
        if (paragraphCount > 0) {
          await expect(paragraphs.first()).toBeVisible();
        }
        
        // Check that links are distinguishable
        const links = page.locator('a');
        const linkCount = await links.count();
        if (linkCount > 0) {
          await expect(links.first()).toBeVisible();
        }
      });

      test('should handle different viewport sizes', async ({ page }) => {
        const viewportSize = page.viewportSize();
        
        // Test specific responsive behaviors based on viewport
        if (viewportSize.width <= 576) {
          // Extra small devices
          await test.step('Extra small viewport behavior', async () => {
            // Cards should stack vertically
            const cards = page.locator('.card, .col-md-6, .col-lg-4');
            if (await cards.count() > 0) {
              // Check that cards are not displayed side by side
              const firstCard = cards.first();
              if (await firstCard.isVisible()) {
                const cardBox = await firstCard.boundingBox();
                expect(cardBox.width).toBeGreaterThan(viewportSize.width * 0.8);
              }
            }
          });
        } else if (viewportSize.width <= 768) {
          // Small devices
          await test.step('Small viewport behavior', async () => {
            // Navigation should be collapsible
            const navToggler = page.locator('.navbar-toggler');
            await expect(navToggler).toBeVisible();
          });
        } else if (viewportSize.width <= 992) {
          // Medium devices
          await test.step('Medium viewport behavior', async () => {
            // Some elements may start to show side by side
            const containers = page.locator('.container, .container-fluid');
            await expect(containers.first()).toBeVisible();
          });
        } else {
          // Large devices
          await test.step('Large viewport behavior', async () => {
            // Full navigation should be visible
            const navCollapse = page.locator('.navbar-collapse');
            await expect(navCollapse).toBeVisible();
            
            // Navigation toggler should be hidden
            const navToggler = page.locator('.navbar-toggler');
            await expect(navToggler).toBeHidden();
          });
        }
      });

      test('should support keyboard navigation', async ({ page }) => {
        // Test keyboard accessibility
        await page.keyboard.press('Tab');
        
        // Check that focus is visible
        const focusedElement = page.locator(':focus');
        await expect(focusedElement).toBeVisible();
        
        // Tab through several elements
        for (let i = 0; i < 5; i++) {
          await page.keyboard.press('Tab');
          const newFocusedElement = page.locator(':focus');
          await expect(newFocusedElement).toBeVisible();
        }
        
        // Test Enter key on buttons
        const buttons = page.locator('button, a[role="button"]');
        if (await buttons.count() > 0) {
          await buttons.first().focus();
          // Note: We don't actually press Enter to avoid triggering actions
          // but we verify the button can receive focus
          await expect(buttons.first()).toBeFocused();
        }
      });

      test('should handle JavaScript interactions', async ({ page }) => {
        // Test that JavaScript-dependent features work
        
        // Test click interactions
        const clickableElements = page.locator('button, a, .btn');
        const elementCount = await clickableElements.count();
        
        if (elementCount > 0) {
          const firstElement = clickableElements.first();
          await expect(firstElement).toBeVisible();
          
          // Test hover effects (visual verification)
          await firstElement.hover();
          
          // Test that the element is clickable
          await expect(firstElement).toBeEnabled();
        }
        
        // Test form interactions
        const inputs = page.locator('input, select, textarea');
        const inputCount = await inputs.count();
        
        if (inputCount > 0) {
          const firstInput = inputs.first();
          if (await firstInput.isVisible() && await firstInput.isEditable()) {
            await firstInput.focus();
            await expect(firstInput).toBeFocused();
          }
        }
      });

      test('should load external resources', async ({ page }) => {
        // Check that external CSS and JS resources load correctly
        
        // Wait for all resources to load
        await page.waitForLoadState('networkidle');
        
        // Check for Bootstrap CSS (should be loaded from CDN)
        const bootstrapStyles = await page.evaluate(() => {
          const stylesheets = Array.from(document.styleSheets);
          return stylesheets.some(sheet => 
            sheet.href && sheet.href.includes('bootstrap')
          );
        });
        
        expect(bootstrapStyles).toBe(true);
        
        // Check that Bootstrap JavaScript is available
        const bootstrapJS = await page.evaluate(() => {
          return typeof window.bootstrap !== 'undefined';
        });
        
        expect(bootstrapJS).toBe(true);
        
        // Check that custom styles are applied
        const navbar = page.locator('nav.navbar');
        if (await navbar.isVisible()) {
          // Bootstrap navbar should have proper styling
          await expect(navbar).toHaveClass(/navbar/);
        }
      });

      test('should maintain performance standards', async ({ page }) => {
        // Performance testing (basic metrics)
        
        // Measure page load time
        const startTime = Date.now();
        await page.goto('/', { waitUntil: 'networkidle' });
        const loadTime = Date.now() - startTime;
        
        // Page should load within reasonable time (5 seconds)
        expect(loadTime).toBeLessThan(5000);
        
        // Check that there are no JavaScript errors
        const errors = [];
        page.on('pageerror', error => errors.push(error));
        
        // Navigate around the app to trigger any potential errors
        await page.click('a[href="/config"]').catch(() => {}); // Ignore if link doesn't exist
        await page.goto('/');
        
        // Should have minimal JavaScript errors
        expect(errors.length).toBeLessThan(3);
      });

      test('should handle print styles', async ({ page }) => {
        // Test print media styles
        await page.emulateMedia({ media: 'print' });
        
        // Page should still be readable in print mode
        const body = page.locator('body');
        await expect(body).toBeVisible();
        
        // Navigation might be hidden in print mode
        // Main content should still be visible
        const mainContent = page.locator('main');
        await expect(mainContent).toBeVisible();
        
        // Reset to screen media
        await page.emulateMedia({ media: 'screen' });
      });

    });
  });

  // Browser-specific tests
  test.describe('Browser-Specific Features', () => {
    
    test('Chrome - DevTools and Extensions', async ({ page, browserName }) => {
      test.skip(browserName !== 'chromium', 'Chrome-specific test');
      
      // Test Chrome-specific features
      await page.goto('/');
      
      // Check that the page works with Chrome's aggressive JavaScript optimizations
      const jsFeatures = await page.evaluate(() => {
        return {
          fetch: typeof fetch !== 'undefined',
          promises: typeof Promise !== 'undefined',
          arrows: (() => true)(), // Arrow function test
          modules: typeof importScripts !== 'undefined' // Web Workers import support
        };
      });
      
      expect(jsFeatures.fetch).toBe(true);
      expect(jsFeatures.promises).toBe(true);
      expect(jsFeatures.arrows).toBe(true);
    });

    test('Firefox - Enhanced Privacy Features', async ({ page, browserName }) => {
      test.skip(browserName !== 'firefox', 'Firefox-specific test');
      
      await page.goto('/');
      
      // Test features that might be affected by Firefox's privacy settings
      const storageAccess = await page.evaluate(() => {
        try {
          localStorage.setItem('test', 'value');
          const value = localStorage.getItem('test');
          localStorage.removeItem('test');
          return value === 'value';
        } catch {
          return false;
        }
      });
      
      expect(storageAccess).toBe(true);
    });

    test('Safari - WebKit Specific Behaviors', async ({ page, browserName }) => {
      test.skip(browserName !== 'webkit', 'Safari-specific test');
      
      await page.goto('/');
      
      // Test WebKit-specific behaviors
      const webkitFeatures = await page.evaluate(() => {
        return {
          flexbox: CSS.supports('display', 'flex'),
          grid: CSS.supports('display', 'grid'),
          transforms: CSS.supports('transform', 'translateX(0)')
        };
      });
      
      expect(webkitFeatures.flexbox).toBe(true);
      expect(webkitFeatures.grid).toBe(true);
      expect(webkitFeatures.transforms).toBe(true);
    });

  });

  // Responsive design tests
  test.describe('Responsive Design Verification', () => {
    
    const breakpoints = [
      { name: 'Mobile Small', width: 320, height: 568 },
      { name: 'Mobile Large', width: 414, height: 896 },
      { name: 'Tablet Portrait', width: 768, height: 1024 },
      { name: 'Tablet Landscape', width: 1024, height: 768 },
      { name: 'Desktop Small', width: 1366, height: 768 },
      { name: 'Desktop Large', width: 1920, height: 1080 }
    ];

    breakpoints.forEach(breakpoint => {
      test(`Responsive layout at ${breakpoint.name} (${breakpoint.width}x${breakpoint.height})`, async ({ page }) => {
        await page.setViewportSize({ width: breakpoint.width, height: breakpoint.height });
        await page.goto('/');
        
        // Check that content is not overflowing
        const body = page.locator('body');
        const bodyBox = await body.boundingBox();
        
        expect(bodyBox.width).toBeLessThanOrEqual(breakpoint.width);
        
        // Check that navigation is accessible
        const navbar = page.locator('nav.navbar');
        await expect(navbar).toBeVisible();
        
        // Check that main content is visible
        const mainContent = page.locator('main');
        await expect(mainContent).toBeVisible();
        
        // Test horizontal scrolling (should not be necessary)
        const horizontalScroll = await page.evaluate(() => {
          return document.documentElement.scrollWidth > document.documentElement.clientWidth;
        });
        
        expect(horizontalScroll).toBe(false);
      });
    });

  });

  // Accessibility tests across browsers
  test.describe('Cross-Browser Accessibility', () => {
    
    test('should have proper ARIA labels and roles', async ({ page }) => {
      await page.goto('/');
      
      // Check for proper landmark roles
      const main = page.locator('main');
      const nav = page.locator('nav');
      
      await expect(main).toBeVisible();
      await expect(nav).toBeVisible();
      
      // Check for form labels
      const inputs = page.locator('input');
      const inputCount = await inputs.count();
      
      for (let i = 0; i < inputCount; i++) {
        const input = inputs.nth(i);
        if (await input.isVisible()) {
          // Input should have associated label or aria-label
          const hasLabel = await input.evaluate(el => {
            return el.hasAttribute('aria-label') || 
                   el.hasAttribute('aria-labelledby') ||
                   document.querySelector(`label[for="${el.id}"]`) !== null;
          });
          
          expect(hasLabel).toBe(true);
        }
      }
    });

    test('should support screen reader navigation', async ({ page }) => {
      await page.goto('/');
      
      // Check for proper heading hierarchy
      const headings = page.locator('h1, h2, h3, h4, h5, h6');
      const headingTexts = await headings.allTextContents();
      
      // Should have at least one h1
      const h1Elements = page.locator('h1');
      const h1Count = await h1Elements.count();
      expect(h1Count).toBeGreaterThanOrEqual(1);
      
      // Check for skip links (accessibility best practice)
      const skipLinks = page.locator('a[href^="#"]').filter({ hasText: /skip/i });
      // Skip links are optional but good to have
    });

  });

});
