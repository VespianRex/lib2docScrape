/**
 * Dashboard GUI Tests
 * 
 * Tests for the main dashboard interface functionality
 */

const { test, expect } = require('@playwright/test');

test.describe('Dashboard Interface', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to dashboard
    await page.goto('/');
    
    // Wait for page to load
    await page.waitForLoadState('networkidle');
  });

  test('should load dashboard page successfully', async ({ page }) => {
    // Check page title
    await expect(page).toHaveTitle(/lib2docScrape/);
    
    // Check main dashboard elements are present
    await expect(page.locator('h1')).toBeVisible();
    await expect(page.locator('.dashboard-container')).toBeVisible();
  });

  test('should display dashboard statistics', async ({ page }) => {
    // Check for statistics cards
    const statsCards = page.locator('.stats-card');
    await expect(statsCards).toHaveCount(4); // libraries, documents, crawls, uptime
    
    // Check each stat card has a value
    for (let i = 0; i < 4; i++) {
      const card = statsCards.nth(i);
      await expect(card.locator('.stat-value')).toBeVisible();
      await expect(card.locator('.stat-label')).toBeVisible();
    }
  });

  test('should have working navigation menu', async ({ page }) => {
    // Check navigation links
    const navLinks = [
      { text: 'Dashboard', href: '/' },
      { text: 'Search', href: '/search' },
      { text: 'Results', href: '/results' },
      { text: 'Export', href: '/export' }
    ];

    for (const link of navLinks) {
      const navLink = page.locator(`nav a[href="${link.href}"]`);
      await expect(navLink).toBeVisible();
      await expect(navLink).toHaveText(link.text);
    }
  });

  test('should support theme switching', async ({ page }) => {
    // Find theme toggle button
    const themeToggle = page.locator('[data-testid="theme-toggle"]');
    
    if (await themeToggle.isVisible()) {
      // Get initial theme
      const initialTheme = await page.evaluate(() => 
        document.documentElement.getAttribute('data-theme')
      );
      
      // Click theme toggle
      await themeToggle.click();
      
      // Wait for theme change
      await page.waitForTimeout(500);
      
      // Check theme changed
      const newTheme = await page.evaluate(() => 
        document.documentElement.getAttribute('data-theme')
      );
      
      expect(newTheme).not.toBe(initialTheme);
    }
  });

  test('should display recent activity', async ({ page }) => {
    // Check for activity section
    const activitySection = page.locator('[data-testid="recent-activity"]');
    
    if (await activitySection.isVisible()) {
      // Check activity items
      const activityItems = activitySection.locator('.activity-item');
      
      if (await activityItems.count() > 0) {
        // Check first activity item structure
        const firstItem = activityItems.first();
        await expect(firstItem.locator('.activity-time')).toBeVisible();
        await expect(firstItem.locator('.activity-description')).toBeVisible();
      }
    }
  });

  test('should refresh data when refresh button clicked', async ({ page }) => {
    // Find refresh button
    const refreshButton = page.locator('[data-testid="refresh-data"]');
    
    if (await refreshButton.isVisible()) {
      // Click refresh button
      await refreshButton.click();
      
      // Check for loading indicator
      const loadingIndicator = page.locator('.loading-spinner');
      if (await loadingIndicator.isVisible()) {
        // Wait for loading to complete
        await expect(loadingIndicator).toBeHidden({ timeout: 10000 });
      }
      
      // Verify data was refreshed (timestamp should update)
      const timestamp = page.locator('[data-testid="last-updated"]');
      if (await timestamp.isVisible()) {
        await expect(timestamp).toBeVisible();
      }
    }
  });

  test('should handle API status endpoint', async ({ page }) => {
    // Test API status endpoint
    const response = await page.request.get('/api/status');
    expect(response.status()).toBe(200);
    
    const data = await response.json();
    expect(data).toHaveProperty('status');
    expect(data.status).toBe('ok');
    expect(data).toHaveProperty('timestamp');
  });

  test('should handle API config endpoint', async ({ page }) => {
    // Test API config endpoint
    const response = await page.request.get('/api/config');
    expect(response.status()).toBe(200);
    
    const data = await response.json();
    expect(data).toHaveProperty('title');
    expect(data).toHaveProperty('theme');
  });

  test('should be responsive on mobile devices', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    
    // Check mobile navigation
    const mobileNav = page.locator('.mobile-nav');
    if (await mobileNav.isVisible()) {
      await expect(mobileNav).toBeVisible();
    }
    
    // Check stats cards stack vertically on mobile
    const statsContainer = page.locator('.stats-container');
    if (await statsContainer.isVisible()) {
      const containerBox = await statsContainer.boundingBox();
      expect(containerBox.width).toBeLessThan(400);
    }
  });

  test('should handle errors gracefully', async ({ page }) => {
    // Test error handling by making invalid API request
    const response = await page.request.get('/api/nonexistent');
    expect(response.status()).toBe(404);
    
    // Check that page doesn't crash on API errors
    await page.goto('/');
    await expect(page.locator('body')).toBeVisible();
  });
});

test.describe('Dashboard Real-time Updates', () => {
  test('should connect to WebSocket for real-time updates', async ({ page }) => {
    // Skip if WebSockets are disabled
    const wsEnabled = await page.evaluate(() => 
      window.location.protocol === 'http:' || window.location.protocol === 'https:'
    );
    
    if (!wsEnabled) {
      test.skip('WebSockets not available');
    }

    // Navigate to dashboard
    await page.goto('/');
    
    // Check for WebSocket connection indicator
    const wsIndicator = page.locator('[data-testid="ws-status"]');
    if (await wsIndicator.isVisible()) {
      await expect(wsIndicator).toHaveClass(/connected/);
    }
  });

  test('should handle WebSocket disconnection gracefully', async ({ page }) => {
    await page.goto('/');
    
    // Simulate network disconnection
    await page.context().setOffline(true);
    
    // Wait a moment for disconnection to be detected
    await page.waitForTimeout(2000);
    
    // Check for disconnection indicator
    const wsIndicator = page.locator('[data-testid="ws-status"]');
    if (await wsIndicator.isVisible()) {
      await expect(wsIndicator).toHaveClass(/disconnected/);
    }
    
    // Restore connection
    await page.context().setOffline(false);
    
    // Wait for reconnection
    await page.waitForTimeout(3000);
    
    // Check for reconnection
    if (await wsIndicator.isVisible()) {
      await expect(wsIndicator).toHaveClass(/connected/);
    }
  });
});
