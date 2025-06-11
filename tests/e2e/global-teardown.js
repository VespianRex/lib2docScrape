/**
 * Global Teardown for E2E Tests
 * 
 * Cleans up the testing environment after running Playwright tests
 */

const { chromium } = require('@playwright/test');
const fs = require('fs').promises;
const path = require('path');

async function globalTeardown() {
  console.log('🧹 Starting global teardown for GUI tests...');
  
  try {
    // Clean up test data
    console.log('📝 Cleaning up test data...');
    
    const browser = await chromium.launch();
    const page = await browser.newPage();
    
    try {
      await page.goto('http://localhost:60643', { timeout: 5000 });
      
      // Clear localStorage and sessionStorage
      await page.evaluate(() => {
        localStorage.clear();
        sessionStorage.clear();
      });
      
      console.log('✅ Browser storage cleared');
    } catch (error) {
      console.warn('⚠️  Could not clear browser storage:', error.message);
    } finally {
      await browser.close();
    }
    
    // Generate test report summary
    console.log('📊 Generating test report summary...');
    
    try {
      const reportDir = path.join(process.cwd(), 'playwright-report');
      const resultsFile = path.join(process.cwd(), 'test-results.json');
      
      // Check if results file exists
      try {
        await fs.access(resultsFile);
        const results = JSON.parse(await fs.readFile(resultsFile, 'utf8'));
        
        const summary = {
          totalTests: results.suites?.reduce((total, suite) => {
            return total + (suite.specs?.length || 0);
          }, 0) || 0,
          passed: 0,
          failed: 0,
          skipped: 0,
          duration: results.stats?.duration || 0
        };
        
        // Count test results
        results.suites?.forEach(suite => {
          suite.specs?.forEach(spec => {
            spec.tests?.forEach(test => {
              switch (test.status) {
                case 'passed':
                  summary.passed++;
                  break;
                case 'failed':
                  summary.failed++;
                  break;
                case 'skipped':
                  summary.skipped++;
                  break;
              }
            });
          });
        });
        
        console.log('📊 Test Summary:');
        console.log(`   Total Tests: ${summary.totalTests}`);
        console.log(`   ✅ Passed: ${summary.passed}`);
        console.log(`   ❌ Failed: ${summary.failed}`);
        console.log(`   ⏭️  Skipped: ${summary.skipped}`);
        console.log(`   ⏱️  Duration: ${Math.round(summary.duration / 1000)}s`);
        
        // Write summary to file
        const summaryFile = path.join(process.cwd(), 'test-summary.json');
        await fs.writeFile(summaryFile, JSON.stringify(summary, null, 2));
        console.log(`✅ Test summary written to ${summaryFile}`);
        
      } catch (error) {
        console.warn('⚠️  Could not generate test summary:', error.message);
      }
      
    } catch (error) {
      console.warn('⚠️  Could not access test results:', error.message);
    }
    
    // Clean up temporary files
    console.log('🗑️  Cleaning up temporary files...');
    
    const tempDirs = [
      'test-results',
      '.playwright'
    ];
    
    for (const dir of tempDirs) {
      try {
        const dirPath = path.join(process.cwd(), dir);
        await fs.access(dirPath);
        // Don't actually delete these as they contain useful artifacts
        console.log(`📁 Keeping ${dir} for inspection`);
      } catch (error) {
        // Directory doesn't exist, which is fine
      }
    }
    
    // Log final status
    console.log('📋 Test artifacts available:');
    
    const artifacts = [
      { name: 'HTML Report', path: 'playwright-report/index.html' },
      { name: 'Test Results', path: 'test-results.json' },
      { name: 'JUnit Results', path: 'test-results.xml' },
      { name: 'Test Summary', path: 'test-summary.json' }
    ];
    
    for (const artifact of artifacts) {
      try {
        await fs.access(path.join(process.cwd(), artifact.path));
        console.log(`   ✅ ${artifact.name}: ${artifact.path}`);
      } catch (error) {
        console.log(`   ❌ ${artifact.name}: Not found`);
      }
    }
    
    // Performance recommendations
    console.log('💡 Performance Recommendations:');
    console.log('   - Review failed tests in the HTML report');
    console.log('   - Check screenshots and videos for failed tests');
    console.log('   - Monitor console errors in browser logs');
    console.log('   - Verify responsive design across different viewports');
    
    console.log('🎉 Global teardown completed successfully');
    
  } catch (error) {
    console.error('❌ Global teardown failed:', error.message);
    // Don't throw error in teardown to avoid masking test failures
  }
}

module.exports = globalTeardown;
