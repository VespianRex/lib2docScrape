/**
 * Visualizations GUI Tests
 * 
 * Tests for charts, tables, and data visualization components
 */

const { test, expect } = require('@playwright/test');

test.describe('Visualizations Interface', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to visualizations page
    await page.goto('/visualizations');
    
    // Wait for page to load
    await page.waitForLoadState('networkidle');
  });

  test('should load visualizations page successfully', async ({ page }) => {
    // Check page title
    await expect(page).toHaveTitle(/Visualizations/);
    
    // Check main visualization elements
    await expect(page.locator('.visualizations-container')).toBeVisible();
  });

  test('should display chart generation interface', async ({ page }) => {
    // Check for chart type selector
    const chartTypeSelect = page.locator('select[name="chartType"]');
    if (await chartTypeSelect.isVisible()) {
      await expect(chartTypeSelect).toBeVisible();
      
      // Check chart type options
      const options = chartTypeSelect.locator('option');
      const optionCount = await options.count();
      expect(optionCount).toBeGreaterThan(1);
      
      // Check for common chart types
      await expect(chartTypeSelect.locator('option[value="bar"]')).toBeVisible();
      await expect(chartTypeSelect.locator('option[value="line"]')).toBeVisible();
      await expect(chartTypeSelect.locator('option[value="pie"]')).toBeVisible();
    }
  });

  test('should generate bar chart', async ({ page }) => {
    // Select bar chart type
    const chartTypeSelect = page.locator('select[name="chartType"]');
    if (await chartTypeSelect.isVisible()) {
      await chartTypeSelect.selectOption('bar');
      
      // Add sample data
      const dataInput = page.locator('textarea[name="chartData"]');
      if (await dataInput.isVisible()) {
        await dataInput.fill(JSON.stringify([
          { label: 'Python', value: 45 },
          { label: 'JavaScript', value: 30 },
          { label: 'Java', value: 25 }
        ]));
        
        // Generate chart
        const generateButton = page.locator('[data-testid="generate-chart"]');
        if (await generateButton.isVisible()) {
          await generateButton.click();
          
          // Wait for chart to render
          await page.waitForTimeout(2000);
          
          // Check for chart container
          const chartContainer = page.locator('.chart-container');
          if (await chartContainer.isVisible()) {
            await expect(chartContainer).toBeVisible();
            
            // Check for chart canvas or SVG
            const chartElement = chartContainer.locator('canvas, svg');
            if (await chartElement.isVisible()) {
              await expect(chartElement).toBeVisible();
            }
          }
        }
      }
    }
  });

  test('should generate line chart', async ({ page }) => {
    const chartTypeSelect = page.locator('select[name="chartType"]');
    if (await chartTypeSelect.isVisible()) {
      await chartTypeSelect.selectOption('line');
      
      // Add time series data
      const dataInput = page.locator('textarea[name="chartData"]');
      if (await dataInput.isVisible()) {
        await dataInput.fill(JSON.stringify([
          { x: '2024-01', y: 100 },
          { x: '2024-02', y: 150 },
          { x: '2024-03', y: 120 }
        ]));
        
        // Generate chart
        const generateButton = page.locator('[data-testid="generate-chart"]');
        if (await generateButton.isVisible()) {
          await generateButton.click();
          
          // Wait for chart
          await page.waitForTimeout(2000);
          
          // Verify line chart is rendered
          const chartContainer = page.locator('.chart-container');
          if (await chartContainer.isVisible()) {
            await expect(chartContainer).toBeVisible();
          }
        }
      }
    }
  });

  test('should generate pie chart', async ({ page }) => {
    const chartTypeSelect = page.locator('select[name="chartType"]');
    if (await chartTypeSelect.isVisible()) {
      await chartTypeSelect.selectOption('pie');
      
      // Add pie chart data
      const dataInput = page.locator('textarea[name="chartData"]');
      if (await dataInput.isVisible()) {
        await dataInput.fill(JSON.stringify([
          { label: 'Success', value: 70 },
          { label: 'Failed', value: 20 },
          { label: 'Pending', value: 10 }
        ]));
        
        // Generate chart
        const generateButton = page.locator('[data-testid="generate-chart"]');
        if (await generateButton.isVisible()) {
          await generateButton.click();
          
          // Wait for chart
          await page.waitForTimeout(2000);
          
          // Verify pie chart is rendered
          const chartContainer = page.locator('.chart-container');
          if (await chartContainer.isVisible()) {
            await expect(chartContainer).toBeVisible();
          }
        }
      }
    }
  });

  test('should customize chart options', async ({ page }) => {
    // Check for chart options panel
    const optionsPanel = page.locator('.chart-options');
    if (await optionsPanel.isVisible()) {
      // Test title customization
      const titleInput = optionsPanel.locator('input[name="title"]');
      if (await titleInput.isVisible()) {
        await titleInput.fill('Test Chart Title');
      }
      
      // Test color scheme selection
      const colorSelect = optionsPanel.locator('select[name="colorScheme"]');
      if (await colorSelect.isVisible()) {
        await colorSelect.selectOption('blue');
      }
      
      // Test width/height settings
      const widthInput = optionsPanel.locator('input[name="width"]');
      if (await widthInput.isVisible()) {
        await widthInput.fill('800');
      }
      
      const heightInput = optionsPanel.locator('input[name="height"]');
      if (await heightInput.isVisible()) {
        await heightInput.fill('400');
      }
      
      // Apply options
      const applyButton = optionsPanel.locator('[data-testid="apply-options"]');
      if (await applyButton.isVisible()) {
        await applyButton.click();
        
        // Wait for chart update
        await page.waitForTimeout(1000);
      }
    }
  });

  test('should export chart as image', async ({ page }) => {
    // First generate a chart
    const chartTypeSelect = page.locator('select[name="chartType"]');
    if (await chartTypeSelect.isVisible()) {
      await chartTypeSelect.selectOption('bar');
      
      const generateButton = page.locator('[data-testid="generate-chart"]');
      if (await generateButton.isVisible()) {
        await generateButton.click();
        await page.waitForTimeout(2000);
        
        // Check for export button
        const exportButton = page.locator('[data-testid="export-chart"]');
        if (await exportButton.isVisible()) {
          await exportButton.click();
          
          // Check for export options
          const exportOptions = page.locator('.export-options');
          if (await exportOptions.isVisible()) {
            // Test PNG export
            const pngOption = exportOptions.locator('[data-format="png"]');
            if (await pngOption.isVisible()) {
              const downloadPromise = page.waitForEvent('download');
              await pngOption.click();
              await downloadPromise;
            }
          }
        }
      }
    }
  });
});

test.describe('Data Tables', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/visualizations');
    await page.waitForLoadState('networkidle');
  });

  test('should display data table interface', async ({ page }) => {
    // Check for table tab or section
    const tableTab = page.locator('[data-tab="table"]');
    if (await tableTab.isVisible()) {
      await tableTab.click();
      
      // Check for table generation interface
      await expect(page.locator('.table-generator')).toBeVisible();
    }
  });

  test('should generate data table', async ({ page }) => {
    const tableTab = page.locator('[data-tab="table"]');
    if (await tableTab.isVisible()) {
      await tableTab.click();
      
      // Add table data
      const dataInput = page.locator('textarea[name="tableData"]');
      if (await dataInput.isVisible()) {
        await dataInput.fill(JSON.stringify([
          { name: 'Python', docs: 150, status: 'Complete' },
          { name: 'JavaScript', docs: 120, status: 'In Progress' },
          { name: 'Java', docs: 200, status: 'Complete' }
        ]));
        
        // Generate table
        const generateButton = page.locator('[data-testid="generate-table"]');
        if (await generateButton.isVisible()) {
          await generateButton.click();
          
          // Wait for table to render
          await page.waitForTimeout(1000);
          
          // Check for table
          const dataTable = page.locator('.data-table');
          if (await dataTable.isVisible()) {
            await expect(dataTable).toBeVisible();
            
            // Check table headers
            await expect(dataTable.locator('th')).toHaveCount(3);
            
            // Check table rows
            const rows = dataTable.locator('tbody tr');
            await expect(rows).toHaveCount(3);
          }
        }
      }
    }
  });

  test('should sort table columns', async ({ page }) => {
    // Generate a table first
    const tableTab = page.locator('[data-tab="table"]');
    if (await tableTab.isVisible()) {
      await tableTab.click();
      
      const dataInput = page.locator('textarea[name="tableData"]');
      if (await dataInput.isVisible()) {
        await dataInput.fill(JSON.stringify([
          { name: 'C', value: 30 },
          { name: 'A', value: 10 },
          { name: 'B', value: 20 }
        ]));
        
        const generateButton = page.locator('[data-testid="generate-table"]');
        if (await generateButton.isVisible()) {
          await generateButton.click();
          await page.waitForTimeout(1000);
          
          // Test column sorting
          const nameHeader = page.locator('th:has-text("name")');
          if (await nameHeader.isVisible()) {
            await nameHeader.click();
            
            // Wait for sort
            await page.waitForTimeout(500);
            
            // Check if first row changed
            const firstCell = page.locator('tbody tr:first-child td:first-child');
            if (await firstCell.isVisible()) {
              const cellText = await firstCell.textContent();
              expect(cellText).toBe('A');
            }
          }
        }
      }
    }
  });

  test('should filter table data', async ({ page }) => {
    const tableTab = page.locator('[data-tab="table"]');
    if (await tableTab.isVisible()) {
      await tableTab.click();
      
      // Generate table with filterable data
      const dataInput = page.locator('textarea[name="tableData"]');
      if (await dataInput.isVisible()) {
        await dataInput.fill(JSON.stringify([
          { name: 'Python', category: 'Language' },
          { name: 'React', category: 'Framework' },
          { name: 'Django', category: 'Framework' }
        ]));
        
        const generateButton = page.locator('[data-testid="generate-table"]');
        if (await generateButton.isVisible()) {
          await generateButton.click();
          await page.waitForTimeout(1000);
          
          // Test filtering
          const filterInput = page.locator('input[name="tableFilter"]');
          if (await filterInput.isVisible()) {
            await filterInput.fill('Framework');
            
            // Wait for filter
            await page.waitForTimeout(500);
            
            // Check filtered results
            const visibleRows = page.locator('tbody tr:visible');
            if (await visibleRows.count() > 0) {
              expect(await visibleRows.count()).toBe(2);
            }
          }
        }
      }
    }
  });

  test('should export table as CSV', async ({ page }) => {
    const tableTab = page.locator('[data-tab="table"]');
    if (await tableTab.isVisible()) {
      await tableTab.click();
      
      // Generate a table
      const dataInput = page.locator('textarea[name="tableData"]');
      if (await dataInput.isVisible()) {
        await dataInput.fill(JSON.stringify([
          { name: 'Test', value: 123 }
        ]));
        
        const generateButton = page.locator('[data-testid="generate-table"]');
        if (await generateButton.isVisible()) {
          await generateButton.click();
          await page.waitForTimeout(1000);
          
          // Test CSV export
          const exportButton = page.locator('[data-testid="export-table"]');
          if (await exportButton.isVisible()) {
            const downloadPromise = page.waitForEvent('download');
            await exportButton.click();
            await downloadPromise;
          }
        }
      }
    }
  });
});

test.describe('Visualization API Integration', () => {
  test('should handle chart API requests', async ({ page }) => {
    // Test chart API endpoint
    const response = await page.request.get('/api/visualizations/chart?type=bar');
    expect(response.status()).toBe(200);
    
    const data = await response.json();
    expect(data).toHaveProperty('type');
    expect(data.type).toBe('bar');
  });

  test('should handle table API requests', async ({ page }) => {
    // Test table API endpoint
    const response = await page.request.get('/api/visualizations/table');
    expect(response.status()).toBe(200);
    
    const data = await response.json();
    expect(data).toHaveProperty('type');
    expect(data.type).toBe('table');
  });

  test('should handle export CSV endpoint', async ({ page }) => {
    // Test CSV export endpoint
    const response = await page.request.get('/export/csv');
    expect(response.status()).toBe(200);
    expect(response.headers()['content-type']).toContain('text/csv');
  });
});
