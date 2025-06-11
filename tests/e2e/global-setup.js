/**
 * Global Setup for E2E Tests
 * 
 * Prepares the testing environment before running Playwright tests
 */

const { chromium } = require('@playwright/test');

async function globalSetup() {
  console.log('🚀 Starting global setup for GUI tests...');
  
  // Launch browser for setup
  const browser = await chromium.launch();
  const page = await browser.newPage();
  
  try {
    // Wait for the GUI server to be ready
    console.log('⏳ Waiting for GUI server to be ready...');
    
    let retries = 30;
    let serverReady = false;
    
    while (retries > 0 && !serverReady) {
      try {
        await page.goto('http://localhost:60643', { timeout: 5000 });
        await page.waitForLoadState('networkidle', { timeout: 5000 });
        serverReady = true;
        console.log('✅ GUI server is ready');
      } catch (error) {
        retries--;
        console.log(`⏳ Server not ready, retrying... (${retries} attempts left)`);
        await new Promise(resolve => setTimeout(resolve, 2000));
      }
    }
    
    if (!serverReady) {
      throw new Error('GUI server failed to start within timeout period');
    }
    
    // Verify critical pages are accessible
    console.log('🔍 Verifying critical pages...');
    
    const criticalPages = [
      '/',
      '/scraping',
      '/results'
    ];
    
    for (const path of criticalPages) {
      try {
        await page.goto(`http://localhost:60643${path}`, { timeout: 10000 });
        await page.waitForLoadState('networkidle', { timeout: 10000 });
        console.log(`✅ Page ${path} is accessible`);
      } catch (error) {
        console.warn(`⚠️  Warning: Page ${path} may not be accessible: ${error.message}`);
      }
    }
    
    // Check if essential DOM elements exist
    console.log('🔍 Verifying essential DOM elements...');
    
    await page.goto('http://localhost:60643/scraping');
    
    const essentialElements = [
      '#scrapingForm',
      '#docUrl',
      '#configPreset',
      '#backend'
    ];
    
    for (const selector of essentialElements) {
      try {
        await page.waitForSelector(selector, { timeout: 5000 });
        console.log(`✅ Element ${selector} found`);
      } catch (error) {
        console.warn(`⚠️  Warning: Essential element ${selector} not found`);
      }
    }
    
    // Set up test data if needed
    console.log('📝 Setting up test data...');
    
    // Clear any existing localStorage data
    await page.evaluate(() => {
      localStorage.clear();
      sessionStorage.clear();
    });
    
    // Set up mock data for testing
    await page.evaluate(() => {
      // Mock configuration presets
      const mockPresets = {
        'test-preset': {
          maxDepth: 3,
          maxPages: 25,
          outputFormat: 'markdown',
          description: 'Test preset for automated testing'
        }
      };
      localStorage.setItem('customPresets', JSON.stringify(mockPresets));
      
      // Mock app configuration
      const mockConfig = {
        resultsPerPage: 10,
        autoRefresh: false,
        refreshInterval: 30
      };
      localStorage.setItem('appConfig', JSON.stringify(mockConfig));
    });
    
    console.log('✅ Test data setup complete');
    
    // Verify JavaScript functionality
    console.log('🔍 Verifying JavaScript functionality...');
    
    try {
      // Test form interaction
      await page.fill('#docUrl', 'https://test.example.com');
      await page.selectOption('#configPreset', 'default');
      
      const urlValue = await page.inputValue('#docUrl');
      const presetValue = await page.inputValue('#configPreset');
      
      if (urlValue === 'https://test.example.com' && presetValue === 'default') {
        console.log('✅ Basic form functionality working');
      } else {
        console.warn('⚠️  Warning: Form functionality may have issues');
      }
    } catch (error) {
      console.warn(`⚠️  Warning: JavaScript functionality test failed: ${error.message}`);
    }
    
    // Check for console errors
    const consoleErrors = [];
    page.on('console', msg => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });
    
    await page.reload();
    await page.waitForLoadState('networkidle');
    
    if (consoleErrors.length > 0) {
      console.warn('⚠️  Console errors detected:');
      consoleErrors.forEach(error => console.warn(`   - ${error}`));
    } else {
      console.log('✅ No console errors detected');
    }
    
    console.log('🎉 Global setup completed successfully');
    
  } catch (error) {
    console.error('❌ Global setup failed:', error.message);
    throw error;
  } finally {
    await browser.close();
  }
}

module.exports = globalSetup;
