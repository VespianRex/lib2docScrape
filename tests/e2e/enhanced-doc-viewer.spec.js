/**
 * Enhanced Document Viewer Tests
 * 
 * Comprehensive tests for the document viewer functionality
 */

const { test, expect } = require('@playwright/test');

test.describe('Enhanced Document Viewer Tests', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to the document viewer page with a sample document
    await page.goto('/doc_viewer.html?doc=sample');
    await expect(page).toHaveTitle(/Document Viewer/i);
  });

  test('should load document content correctly', async ({ page }) => {
    // Verify document title is displayed
    await expect(page.locator('#documentTitle')).toBeVisible();
    
    // Verify document content is displayed
    await expect(page.locator('#documentContent')).toBeVisible();
    
    // Verify document metadata is displayed
    await expect(page.locator('#documentMetadata')).toBeVisible();
  });

  test('should navigate between document sections', async ({ page }) => {
    // Get initial section title
    const initialSectionTitle = await page.locator('#currentSection').textContent();
    
    // Click next section button
    await page.locator('#nextSectionBtn').click();
    
    // Verify section changed
    const newSectionTitle = await page.locator('#currentSection').textContent();
    expect(newSectionTitle).not.toEqual(initialSectionTitle);
  });

  test('should highlight code blocks correctly', async ({ page }) => {
    // Find a code block
    const codeBlock = page.locator('pre code').first();
    
    // Verify code block is visible
    await expect(codeBlock).toBeVisible();
    
    // Verify syntax highlighting is applied
    const hasHighlightClass = await codeBlock.evaluate(el => {
      return el.classList.contains('hljs') || 
             el.querySelector('.hljs') !== null ||
             el.parentElement.classList.contains('hljs');
    });
    
    expect(hasHighlightClass).toBeTruthy();
  });

  test('should toggle dark mode', async ({ page }) => {
    // Get initial theme
    const initialTheme = await page.evaluate(() => {
      return document.body.classList.contains('dark-mode') ? 'dark' : 'light';
    });
    
    // Toggle theme
    await page.locator('#toggleThemeBtn').click();
    
    // Verify theme changed
    const newTheme = await page.evaluate(() => {
      return document.body.classList.contains('dark-mode') ? 'dark' : 'light';
    });
    
    expect(newTheme).not.toEqual(initialTheme);
  });

  test('should search within document', async ({ page }) => {
    // Enter search term
    await page.locator('#documentSearchInput').fill('example');
    await page.locator('#documentSearchBtn').click();
    
    // Verify search results are highlighted
    const highlightedElements = await page.locator('.search-highlight').count();
    expect(highlightedElements).toBeGreaterThan(0);
  });

  test('should display document table of contents', async ({ page }) => {
    // Verify TOC is visible
    await expect(page.locator('#tableOfContents')).toBeVisible();
    
    // Verify TOC has items
    const tocItemCount = await page.locator('#tableOfContents li').count();
    expect(tocItemCount).toBeGreaterThan(0);
    
    // Click a TOC item
    await page.locator('#tableOfContents li').first().click();
    
    // Verify navigation occurred
    await expect(page.locator('.section.active')).toBeVisible();
  });

  test('should allow copying code snippets', async ({ page }) => {
    // Find a code block
    const codeBlock = page.locator('pre code').first();
    
    // Hover over code block to reveal copy button
    await codeBlock.hover();
    
    // Click copy button
    await page.locator('.copy-code-btn').first().click();
    
    // Verify copy confirmation appears
    await expect(page.locator('.copy-confirmation')).toBeVisible();
    
    // Verify clipboard contains the code (this requires permissions)
    // This is a simplified check that just verifies the UI feedback
    await expect(page.locator('.copy-confirmation')).toContainText('Copied');
  });

  test('should handle document not found gracefully', async ({ page }) => {
    // Navigate to non-existent document
    await page.goto('/doc_viewer.html?doc=nonexistent');
    
    // Verify error message is displayed
    await expect(page.locator('#errorMessage')).toBeVisible();
    await expect(page.locator('#errorMessage')).toContainText('Document not found');
  });

  test('should render diagrams correctly', async ({ page }) => {
    // Navigate to a page with diagrams
    await page.goto('/doc_viewer.html?doc=with_diagrams');
    
    // Verify diagram is rendered
    await expect(page.locator('.diagram-container')).toBeVisible();
    
    // Verify diagram elements are present
    const diagramElements = await page.locator('.diagram-container svg').count();
    expect(diagramElements).toBeGreaterThan(0);
  });
});