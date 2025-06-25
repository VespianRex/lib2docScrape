/**
 * Enhanced Visualizations Tests
 * 
 * Comprehensive tests for the visualization functionality
 */

const { test, expect } = require('@playwright/test');

test.describe('Enhanced Visualizations Tests', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to the visualizations page
    await page.goto('/visualizations.html');
    await expect(page).toHaveTitle(/Visualizations/i);
  });

  test('should load all visualization components', async ({ page }) => {
    // Verify chart containers are present
    await expect(page.locator('#coverageChart')).toBeVisible();
    await expect(page.locator('#dependencyGraph')).toBeVisible();
    await expect(page.locator('#timelineChart')).toBeVisible();
    await expect(page.locator('#heatmapChart')).toBeVisible();
  });

  test('should render coverage chart correctly', async ({ page }) => {
    // Verify chart is rendered
    await expect(page.locator('#coverageChart canvas')).toBeVisible();
    
    // Verify chart has data
    const hasData = await page.evaluate(() => {
      // This assumes the chart is using a library like Chart.js
      const chartElement = document.querySelector('#coverageChart canvas');
      return chartElement && chartElement.__chart && chartElement.__chart.data.datasets.length > 0;
    });
    
    expect(hasData).toBeTruthy();
  });

  test('should render dependency graph correctly', async ({ page }) => {
    // Verify graph is rendered
    await expect(page.locator('#dependencyGraph svg')).toBeVisible();
    
    // Verify graph has nodes
    const nodeCount = await page.locator('#dependencyGraph .node').count();
    expect(nodeCount).toBeGreaterThan(0);
    
    // Verify graph has edges
    const edgeCount = await page.locator('#dependencyGraph .edge').count();
    expect(edgeCount).toBeGreaterThan(0);
  });

  test('should update charts when filters are applied', async ({ page }) => {
    // Get initial chart data
    const initialData = await page.evaluate(() => {
      const chartElement = document.querySelector('#coverageChart canvas');
      return chartElement && chartElement.__chart ? 
        chartElement.__chart.data.datasets[0].data.slice() : [];
    });
    
    // Apply filter
    await page.locator('#timeRangeFilter').selectOption('last-month');
    await page.locator('#applyFiltersBtn').click();
    
    // Wait for chart to update
    await page.waitForTimeout(1000);
    
    // Get updated chart data
    const updatedData = await page.evaluate(() => {
      const chartElement = document.querySelector('#coverageChart canvas');
      return chartElement && chartElement.__chart ? 
        chartElement.__chart.data.datasets[0].data.slice() : [];
    });
    
    // Verify data changed
    expect(updatedData).not.toEqual(initialData);
  });

  test('should allow zooming in charts', async ({ page }) => {
    // Get initial zoom level
    const initialZoom = await page.evaluate(() => {
      const chartElement = document.querySelector('#coverageChart canvas');
      return chartElement && chartElement.__chart ? 
        chartElement.__chart.options.scales.x.min : null;
    });
    
    // Zoom in (simulate wheel event)
    await page.locator('#coverageChart canvas').hover();
    await page.mouse.wheel(0, -100);
    
    // Wait for zoom to apply
    await page.waitForTimeout(1000);
    
    // Get new zoom level
    const newZoom = await page.evaluate(() => {
      const chartElement = document.querySelector('#coverageChart canvas');
      return chartElement && chartElement.__chart ? 
        chartElement.__chart.options.scales.x.min : null;
    });
    
    // Verify zoom changed
    expect(newZoom).not.toEqual(initialZoom);
  });

  test('should export chart as image', async ({ page }) => {
    // Click export button
    await page.locator('#exportChartBtn').click();
    
    // Verify download started
    const download = await page.waitForEvent('download');
    expect(download.suggestedFilename()).toContain('.png');
  });

  test('should toggle between chart types', async ({ page }) => {
    // Get initial chart type
    const initialChartType = await page.evaluate(() => {
      const chartElement = document.querySelector('#coverageChart canvas');
      return chartElement && chartElement.__chart ? 
        chartElement.__chart.config.type : null;
    });
    
    // Change chart type
    await page.locator('#chartTypeSelector').selectOption('bar');
    
    // Wait for chart to update
    await page.waitForTimeout(1000);
    
    // Get new chart type
    const newChartType = await page.evaluate(() => {
      const chartElement = document.querySelector('#coverageChart canvas');
      return chartElement && chartElement.__chart ? 
        chartElement.__chart.config.type : null;
    });
    
    // Verify chart type changed
    expect(newChartType).not.toEqual(initialChartType);
  });

  test('should show tooltips on hover', async ({ page }) => {
    // Hover over a data point
    await page.locator('#coverageChart canvas').hover({ position: { x: 100, y: 100 } });
    
    // Verify tooltip appears
    await expect(page.locator('.chartjs-tooltip')).toBeVisible();
  });

  test('should update timeline when date range is changed', async ({ page }) => {
    // Get initial timeline data
    const initialData = await page.evaluate(() => {
      const chartElement = document.querySelector('#timelineChart canvas');
      return chartElement && chartElement.__chart ? 
        chartElement.__chart.data.datasets[0].data.length : 0;
    });
    
    // Change date range
    await page.locator('#startDate').fill('2023-01-01');
    await page.locator('#endDate').fill('2023-01-31');
    await page.locator('#updateTimelineBtn').click();
    
    // Wait for chart to update
    await page.waitForTimeout(1000);
    
    // Get new timeline data
    const newData = await page.evaluate(() => {
      const chartElement = document.querySelector('#timelineChart canvas');
      return chartElement && chartElement.__chart ? 
        chartElement.__chart.data.datasets[0].data.length : 0;
    });
    
    // Verify data changed
    expect(newData).not.toEqual(initialData);
  });

  test('should handle empty data gracefully', async ({ page }) => {
    // Apply filter that results in no data
    await page.locator('#libraryFilter').selectOption('nonexistent-library');
    await page.locator('#applyFiltersBtn').click();
    
    // Wait for UI update
    await page.waitForTimeout(1000);
    
    // Verify empty state message is displayed
    await expect(page.locator('#noDataMessage')).toBeVisible();
  });
});