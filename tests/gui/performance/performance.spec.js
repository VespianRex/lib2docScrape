/**
 * Performance Tests
 * 
 * Tests for measuring and validating GUI performance metrics
 */

const { test, expect } = require('@playwright/test');

test.describe('GUI Performance Tests', () => {
  
  test.describe('Page Load Performance', () => {
    
    test('should load homepage within performance targets', async ({ page }) => {
      // Start timing
      const startTime = Date.now();
      
      // Navigate to homepage
      await page.goto('/', { waitUntil: 'networkidle' });
      
      // Measure load time
      const loadTime = Date.now() - startTime;
      
      // Performance target: < 3 seconds
      expect(loadTime).toBeLessThan(3000);
      
      // Measure Core Web Vitals
      const webVitals = await page.evaluate(() => {
        return new Promise((resolve) => {
          const observer = new PerformanceObserver((list) => {
            const entries = list.getEntries();
            const vitals = {};
            
            entries.forEach((entry) => {
              if (entry.entryType === 'navigation') {
                vitals.navigationTiming = {
                  domContentLoaded: entry.domContentLoadedEventEnd - entry.domContentLoadedEventStart,
                  loadComplete: entry.loadEventEnd - entry.loadEventStart,
                  totalTime: entry.loadEventEnd - entry.fetchStart
                };
              }
              
              if (entry.entryType === 'paint') {
                if (entry.name === 'first-contentful-paint') {
                  vitals.fcp = entry.startTime;
                }
                if (entry.name === 'largest-contentful-paint') {
                  vitals.lcp = entry.startTime;
                }
              }
              
              if (entry.entryType === 'layout-shift') {
                vitals.cls = (vitals.cls || 0) + entry.value;
              }
            });
            
            resolve(vitals);
          });
          
          observer.observe({ entryTypes: ['navigation', 'paint', 'layout-shift'] });
          
          // Fallback timeout
          setTimeout(() => resolve({}), 5000);
        });
      });
      
      // Validate Core Web Vitals
      if (webVitals.fcp) {
        expect(webVitals.fcp).toBeLessThan(2500); // First Contentful Paint < 2.5s
      }
      
      if (webVitals.lcp) {
        expect(webVitals.lcp).toBeLessThan(4000); // Largest Contentful Paint < 4s
      }
      
      if (webVitals.cls !== undefined) {
        expect(webVitals.cls).toBeLessThan(0.25); // Cumulative Layout Shift < 0.25
      }
    });

    test('should load configuration page efficiently', async ({ page }) => {
      const startTime = Date.now();
      
      await page.goto('/config', { waitUntil: 'networkidle' });
      
      const loadTime = Date.now() - startTime;
      expect(loadTime).toBeLessThan(3000);
      
      // Check that form elements are interactive quickly
      const firstInput = page.locator('input, select').first();
      if (await firstInput.isVisible()) {
        const interactionStart = Date.now();
        await firstInput.focus();
        const interactionTime = Date.now() - interactionStart;
        
        // Should be interactive within 100ms
        expect(interactionTime).toBeLessThan(100);
      }
    });

    test('should load results page efficiently', async ({ page }) => {
      const startTime = Date.now();
      
      await page.goto('/results', { waitUntil: 'networkidle' });
      
      const loadTime = Date.now() - startTime;
      expect(loadTime).toBeLessThan(3000);
      
      // Check that the page is scrollable efficiently
      const scrollStart = Date.now();
      await page.evaluate(() => window.scrollTo(0, 500));
      const scrollTime = Date.now() - scrollStart;
      
      // Scrolling should be smooth (< 50ms)
      expect(scrollTime).toBeLessThan(50);
    });

  });

  test.describe('Interaction Performance', () => {
    
    test('should handle form interactions efficiently', async ({ page }) => {
      await page.goto('/');
      
      // Test input responsiveness
      const urlInput = page.locator('input[type="url"]').first();
      if (await urlInput.isVisible()) {
        const inputStart = Date.now();
        
        // Type URL
        await urlInput.fill('https://docs.python.org');
        
        const inputTime = Date.now() - inputStart;
        
        // Input should be responsive (< 200ms for typical typing)
        expect(inputTime).toBeLessThan(200);
        
        // Test form validation performance
        const validationStart = Date.now();
        await urlInput.blur(); // Trigger validation
        const validationTime = Date.now() - validationStart;
        
        // Validation should be fast (< 100ms)
        expect(validationTime).toBeLessThan(100);
      }
    });

    test('should handle navigation clicks efficiently', async ({ page }) => {
      await page.goto('/');
      
      // Test navigation performance
      const navLinks = page.locator('.nav-link');
      const linkCount = await navLinks.count();
      
      if (linkCount > 0) {
        const clickStart = Date.now();
        
        // Click first navigation link
        await navLinks.first().click();
        
        // Wait for navigation to complete
        await page.waitForLoadState('networkidle');
        
        const navigationTime = Date.now() - clickStart;
        
        // Navigation should complete within 2 seconds
        expect(navigationTime).toBeLessThan(2000);
      }
    });

    test('should handle button clicks without delay', async ({ page }) => {
      await page.goto('/');
      
      const buttons = page.locator('button');
      const buttonCount = await buttons.count();
      
      if (buttonCount > 0) {
        const button = buttons.first();
        
        if (await button.isVisible() && await button.isEnabled()) {
          const clickStart = Date.now();
          
          // Click button
          await button.click();
          
          const clickTime = Date.now() - clickStart;
          
          // Button click should be immediate (< 50ms)
          expect(clickTime).toBeLessThan(50);
        }
      }
    });

  });

  test.describe('Memory and Resource Performance', () => {
    
    test('should not have memory leaks during navigation', async ({ page }) => {
      // Get initial memory usage
      const initialMemory = await page.evaluate(() => {
        if (performance.memory) {
          return {
            used: performance.memory.usedJSHeapSize,
            total: performance.memory.totalJSHeapSize,
            limit: performance.memory.jsHeapSizeLimit
          };
        }
        return null;
      });
      
      // Navigate through multiple pages
      const pages = ['/', '/config', '/results', '/'];
      
      for (const pagePath of pages) {
        await page.goto(pagePath, { waitUntil: 'networkidle' });
        await page.waitForTimeout(100); // Small delay to let page settle
      }
      
      // Get final memory usage
      const finalMemory = await page.evaluate(() => {
        if (performance.memory) {
          return {
            used: performance.memory.usedJSHeapSize,
            total: performance.memory.totalJSHeapSize,
            limit: performance.memory.jsHeapSizeLimit
          };
        }
        return null;
      });
      
      if (initialMemory && finalMemory) {
        // Memory usage shouldn't grow excessively (< 50MB increase)
        const memoryIncrease = finalMemory.used - initialMemory.used;
        expect(memoryIncrease).toBeLessThan(50 * 1024 * 1024); // 50MB
        
        // Memory usage should be reasonable (< 100MB total)
        expect(finalMemory.used).toBeLessThan(100 * 1024 * 1024); // 100MB
      }
    });

    test('should load external resources efficiently', async ({ page }) => {
      // Monitor network requests
      const requests = [];
      page.on('request', request => {
        requests.push({
          url: request.url(),
          method: request.method(),
          size: request.postData()?.length || 0,
          startTime: Date.now()
        });
      });
      
      const responses = [];
      page.on('response', response => {
        responses.push({
          url: response.url(),
          status: response.status(),
          size: response.headers()['content-length'] || 0,
          endTime: Date.now()
        });
      });
      
      await page.goto('/', { waitUntil: 'networkidle' });
      
      // Analyze resource loading
      const slowResources = responses.filter(response => {
        const request = requests.find(req => req.url === response.url);
        if (request) {
          const loadTime = response.endTime - request.startTime;
          return loadTime > 3000; // Resources taking > 3 seconds
        }
        return false;
      });
      
      // Should have minimal slow-loading resources
      expect(slowResources.length).toBeLessThan(2);
      
      // Check for failed resources
      const failedResources = responses.filter(response => 
        response.status >= 400
      );
      
      // Should have no failed critical resources
      expect(failedResources.length).toBeLessThan(3);
    });

  });

  test.describe('Rendering Performance', () => {
    
    test('should maintain smooth frame rate', async ({ page }) => {
      await page.goto('/');
      
      // Measure frame rate during scrolling
      const frameData = await page.evaluate(() => {
        return new Promise((resolve) => {
          const frames = [];
          let lastTime = performance.now();
          
          const measureFrame = (currentTime) => {
            const delta = currentTime - lastTime;
            frames.push(delta);
            lastTime = currentTime;
            
            if (frames.length < 60) { // Measure 60 frames
              requestAnimationFrame(measureFrame);
            } else {
              resolve(frames);
            }
          };
          
          // Start scrolling to trigger repaints
          let scrollPos = 0;
          const scrollInterval = setInterval(() => {
            scrollPos += 10;
            window.scrollTo(0, scrollPos);
            
            if (scrollPos > 500) {
              clearInterval(scrollInterval);
            }
          }, 16); // ~60fps
          
          requestAnimationFrame(measureFrame);
        });
      });
      
      // Calculate average FPS
      const averageFrameTime = frameData.reduce((a, b) => a + b) / frameData.length;
      const averageFPS = 1000 / averageFrameTime;
      
      // Should maintain at least 30 FPS
      expect(averageFPS).toBeGreaterThan(30);
      
      // Should ideally maintain 60 FPS
      if (averageFPS >= 55) {
        console.log(`Excellent frame rate: ${averageFPS.toFixed(1)} FPS`);
      } else if (averageFPS >= 30) {
        console.log(`Acceptable frame rate: ${averageFPS.toFixed(1)} FPS`);
      }
    });

    test('should render large lists efficiently', async ({ page }) => {
      // This test would be relevant if the app displays large lists of results
      await page.goto('/results');
      
      // Check if there are any large lists or tables
      const largeContainers = page.locator('[data-testid*="list"], .table, .grid');
      const containerCount = await largeContainers.count();
      
      if (containerCount > 0) {
        const renderStart = Date.now();
        
        // Scroll through the list to test rendering performance
        await page.evaluate(() => {
          const container = document.querySelector('[data-testid*="list"], .table, .grid');
          if (container) {
            for (let i = 0; i < 10; i++) {
              container.scrollTop = i * 100;
            }
          }
        });
        
        const renderTime = Date.now() - renderStart;
        
        // Large list scrolling should be smooth (< 500ms)
        expect(renderTime).toBeLessThan(500);
      }
    });

  });

  test.describe('Network Performance', () => {
    
    test('should handle slow network conditions gracefully', async ({ page, context }) => {
      // Simulate slow 3G network
      await context.route('**/*', (route) => {
        // Add artificial delay for non-critical resources
        if (route.request().url().includes('.css') || route.request().url().includes('.js')) {
          setTimeout(() => route.continue(), 500);
        } else {
          route.continue();
        }
      });
      
      const startTime = Date.now();
      await page.goto('/', { waitUntil: 'domcontentloaded' });
      const loadTime = Date.now() - startTime;
      
      // Page should still be usable within reasonable time on slow network
      expect(loadTime).toBeLessThan(10000); // 10 seconds max
      
      // Check that critical content is visible
      const mainContent = page.locator('main');
      await expect(mainContent).toBeVisible();
    });

    test('should handle offline conditions', async ({ page, context }) => {
      // First load the page normally
      await page.goto('/');
      
      // Then simulate offline condition
      await context.setOffline(true);
      
      // Try to navigate - should handle gracefully
      const navigationPromise = page.goto('/config').catch(() => {
        // Navigation failure is expected when offline
        return null;
      });
      
      await navigationPromise;
      
      // Re-enable network
      await context.setOffline(false);
      
      // Should be able to navigate again
      await page.goto('/config', { waitUntil: 'networkidle' });
      
      const configPage = page.locator('main');
      await expect(configPage).toBeVisible();
    });

  });

  test.describe('Performance Benchmarks', () => {
    
    test('should meet time to interactive target', async ({ page }) => {
      const startTime = Date.now();
      
      await page.goto('/', { waitUntil: 'load' });
      
      // Test if page is interactive
      const interactive = await page.evaluate(() => {
        // Check if main interactive elements are ready
        const inputs = document.querySelectorAll('input, button, select');
        let interactiveCount = 0;
        
        inputs.forEach(element => {
          if (!element.disabled && element.offsetParent !== null) {
            interactiveCount++;
          }
        });
        
        return interactiveCount > 0;
      });
      
      const timeToInteractive = Date.now() - startTime;
      
      expect(interactive).toBe(true);
      expect(timeToInteractive).toBeLessThan(5000); // 5 seconds TTI target
    });

    test('should have reasonable bundle sizes', async ({ page }) => {
      const resourceSizes = [];
      
      page.on('response', async (response) => {
        if (response.url().includes('.js') || response.url().includes('.css')) {
          try {
            const buffer = await response.body();
            resourceSizes.push({
              url: response.url(),
              size: buffer.length,
              type: response.url().includes('.js') ? 'javascript' : 'css'
            });
          } catch (error) {
            // Ignore errors getting resource size
          }
        }
      });
      
      await page.goto('/', { waitUntil: 'networkidle' });
      
      // Calculate total bundle sizes
      const jsSize = resourceSizes
        .filter(r => r.type === 'javascript')
        .reduce((total, r) => total + r.size, 0);
        
      const cssSize = resourceSizes
        .filter(r => r.type === 'css')
        .reduce((total, r) => total + r.size, 0);
      
      // JavaScript bundle should be reasonable (< 1MB)
      expect(jsSize).toBeLessThan(1024 * 1024);
      
      // CSS bundle should be reasonable (< 500KB)
      expect(cssSize).toBeLessThan(512 * 1024);
      
      console.log(`JavaScript bundle size: ${(jsSize / 1024).toFixed(1)}KB`);
      console.log(`CSS bundle size: ${(cssSize / 1024).toFixed(1)}KB`);
    });

  });

});
