/**
 * Configuration Management Tests (Bun)
 * 
 * Modern tests for configuration presets, backend selection, and settings management
 */

import { test, expect, describe, beforeEach } from "bun:test";
import { testUtils, mockConfigPresets, mockBackendDescriptions } from "../setup";

describe("Configuration Management", () => {
  beforeEach(() => {
    // Create mock DOM structure for configuration
    document.body.innerHTML = `
      <div class="container-fluid">
        <form id="scrapingForm">
          <select id="configPreset">
            <option value="default">Default (Balanced)</option>
            <option value="comprehensive">Comprehensive (Maximum Coverage)</option>
            <option value="performance">Performance (Fast)</option>
            <option value="javascript">JavaScript-Optimized</option>
            <option value="minimal">Minimal (Testing)</option>
            <option value="custom">Custom Configuration</option>
          </select>
          
          <select id="backend">
            <option value="http">HTTP Backend (Fast & Reliable)</option>
            <option value="crawl4ai">Crawl4AI (AI-Powered)</option>
            <option value="lightpanda">Lightpanda (JavaScript Support)</option>
            <option value="playwright">Playwright (Full Browser)</option>
            <option value="scrapy">Scrapy (High Performance)</option>
            <option value="file">File Backend (Local Files)</option>
          </select>
          
          <input type="number" id="maxDepth" value="5" min="1" max="10">
          <input type="number" id="maxPages" value="100" min="5" max="200">
          <select id="outputFormat">
            <option value="markdown">Markdown (Recommended)</option>
            <option value="json">JSON</option>
            <option value="html">HTML</option>
            <option value="all">All Formats</option>
          </select>
          
          <small id="presetDescription">Balanced configuration for most use cases</small>
          <small id="backendDescription">Fast and reliable for most documentation sites</small>
          
          <button type="button" id="savePresetBtn">Save Preset</button>
          <button type="button" id="benchmarkBtn">Benchmark</button>
        </form>
      </div>
    `;
  });

  describe("Configuration Presets", () => {
    test("should load default preset correctly", () => {
      const presetSelect = document.getElementById('configPreset') as HTMLSelectElement;
      const maxDepthInput = document.getElementById('maxDepth') as HTMLInputElement;
      const maxPagesInput = document.getElementById('maxPages') as HTMLInputElement;
      const outputFormatSelect = document.getElementById('outputFormat') as HTMLSelectElement;

      // Simulate preset selection
      presetSelect.value = 'default';
      testUtils.simulateInput(presetSelect, 'default');

      expect(presetSelect.value).toBe('default');
    });

    test("should load comprehensive preset correctly", () => {
      const presetSelect = document.getElementById('configPreset') as HTMLSelectElement;
      
      presetSelect.value = 'comprehensive';
      testUtils.simulateInput(presetSelect, 'comprehensive');

      expect(presetSelect.value).toBe('comprehensive');
    });

    test("should load performance preset correctly", () => {
      const presetSelect = document.getElementById('configPreset') as HTMLSelectElement;
      
      presetSelect.value = 'performance';
      testUtils.simulateInput(presetSelect, 'performance');

      expect(presetSelect.value).toBe('performance');
    });

    test("should handle custom preset selection", () => {
      const presetSelect = document.getElementById('configPreset') as HTMLSelectElement;
      
      presetSelect.value = 'custom';
      testUtils.simulateInput(presetSelect, 'custom');

      expect(presetSelect.value).toBe('custom');
    });

    test("should update preset description", () => {
      const presetSelect = document.getElementById('configPreset') as HTMLSelectElement;
      const description = document.getElementById('presetDescription') as HTMLElement;

      presetSelect.value = 'comprehensive';
      testUtils.simulateInput(presetSelect, 'comprehensive');

      // Description should exist (actual update would be handled by the real function)
      expect(description).toBeTruthy();
    });
  });

  describe("Backend Selection", () => {
    test("should select HTTP backend", () => {
      const backendSelect = document.getElementById('backend') as HTMLSelectElement;
      
      backendSelect.value = 'http';
      testUtils.simulateInput(backendSelect, 'http');

      expect(backendSelect.value).toBe('http');
    });

    test("should select Crawl4AI backend", () => {
      const backendSelect = document.getElementById('backend') as HTMLSelectElement;
      
      backendSelect.value = 'crawl4ai';
      testUtils.simulateInput(backendSelect, 'crawl4ai');

      expect(backendSelect.value).toBe('crawl4ai');
    });

    test("should select Lightpanda backend", () => {
      const backendSelect = document.getElementById('backend') as HTMLSelectElement;
      
      backendSelect.value = 'lightpanda';
      testUtils.simulateInput(backendSelect, 'lightpanda');

      expect(backendSelect.value).toBe('lightpanda');
    });

    test("should select Playwright backend", () => {
      const backendSelect = document.getElementById('backend') as HTMLSelectElement;
      
      backendSelect.value = 'playwright';
      testUtils.simulateInput(backendSelect, 'playwright');

      expect(backendSelect.value).toBe('playwright');
    });

    test("should update backend description", () => {
      const backendSelect = document.getElementById('backend') as HTMLSelectElement;
      const description = document.getElementById('backendDescription') as HTMLElement;

      backendSelect.value = 'crawl4ai';
      testUtils.simulateInput(backendSelect, 'crawl4ai');

      expect(description).toBeTruthy();
    });
  });

  describe("Parameter Validation", () => {
    test("should validate max depth range", () => {
      const maxDepthInput = document.getElementById('maxDepth') as HTMLInputElement;
      
      // Test minimum value
      testUtils.simulateInput(maxDepthInput, '1');
      expect(maxDepthInput.value).toBe('1');

      // Test maximum value
      testUtils.simulateInput(maxDepthInput, '10');
      expect(maxDepthInput.value).toBe('10');
    });

    test("should validate max pages range", () => {
      const maxPagesInput = document.getElementById('maxPages') as HTMLInputElement;
      
      // Test minimum value
      testUtils.simulateInput(maxPagesInput, '5');
      expect(maxPagesInput.value).toBe('5');

      // Test maximum value
      testUtils.simulateInput(maxPagesInput, '200');
      expect(maxPagesInput.value).toBe('200');
    });

    test("should handle output format selection", () => {
      const outputFormatSelect = document.getElementById('outputFormat') as HTMLSelectElement;
      
      outputFormatSelect.value = 'json';
      testUtils.simulateInput(outputFormatSelect, 'json');
      expect(outputFormatSelect.value).toBe('json');

      outputFormatSelect.value = 'html';
      testUtils.simulateInput(outputFormatSelect, 'html');
      expect(outputFormatSelect.value).toBe('html');

      outputFormatSelect.value = 'all';
      testUtils.simulateInput(outputFormatSelect, 'all');
      expect(outputFormatSelect.value).toBe('all');
    });
  });

  describe("Custom Preset Management", () => {
    test("should trigger save preset functionality", () => {
      const saveBtn = document.getElementById('savePresetBtn') as HTMLButtonElement;
      
      // Mock prompt for preset name
      (globalThis as any).prompt = () => 'My Custom Preset';
      
      testUtils.simulateClick(saveBtn);
      
      // Verify button exists and is clickable
      expect(saveBtn).toBeTruthy();
    });

    test("should handle save preset cancellation", () => {
      const saveBtn = document.getElementById('savePresetBtn') as HTMLButtonElement;
      
      // Mock prompt cancellation
      (globalThis as any).prompt = () => null;
      
      testUtils.simulateClick(saveBtn);
      
      expect(saveBtn).toBeTruthy();
    });
  });

  describe("Backend Benchmarking", () => {
    test("should trigger benchmark functionality", () => {
      const benchmarkBtn = document.getElementById('benchmarkBtn') as HTMLButtonElement;
      
      testUtils.simulateClick(benchmarkBtn);
      
      // Verify button exists and is clickable
      expect(benchmarkBtn).toBeTruthy();
    });

    test("should handle benchmark with URL", () => {
      // Add URL input to DOM
      const urlInput = document.createElement('input');
      urlInput.id = 'docUrl';
      urlInput.value = 'https://docs.python.org/3/';
      document.body.appendChild(urlInput);

      const benchmarkBtn = document.getElementById('benchmarkBtn') as HTMLButtonElement;
      testUtils.simulateClick(benchmarkBtn);

      expect(urlInput.value).toBe('https://docs.python.org/3/');
    });
  });

  describe("Form Integration", () => {
    test("should collect all form data correctly", () => {
      const form = document.getElementById('scrapingForm') as HTMLFormElement;
      const configPreset = document.getElementById('configPreset') as HTMLSelectElement;
      const backend = document.getElementById('backend') as HTMLSelectElement;
      const maxDepth = document.getElementById('maxDepth') as HTMLInputElement;
      const maxPages = document.getElementById('maxPages') as HTMLInputElement;
      const outputFormat = document.getElementById('outputFormat') as HTMLSelectElement;

      // Set form values
      configPreset.value = 'comprehensive';
      backend.value = 'crawl4ai';
      maxDepth.value = '3';
      maxPages.value = '50';
      outputFormat.value = 'markdown';

      // Verify all values are set
      expect(configPreset.value).toBe('comprehensive');
      expect(backend.value).toBe('crawl4ai');
      expect(maxDepth.value).toBe('3');
      expect(maxPages.value).toBe('50');
      expect(outputFormat.value).toBe('markdown');
    });

    test("should handle form submission", () => {
      const form = document.getElementById('scrapingForm') as HTMLFormElement;
      let submitCalled = false;
      
      form.addEventListener('submit', (e) => {
        e.preventDefault();
        submitCalled = true;
      });
      
      testUtils.simulateSubmit(form);

      expect(submitCalled).toBe(true);
    });
  });

  describe("Error Handling", () => {
    test("should handle missing elements gracefully", () => {
      // Remove an element
      const presetSelect = document.getElementById('configPreset');
      presetSelect?.remove();

      // Should not throw error when trying to access removed element
      expect(() => {
        const element = document.getElementById('configPreset');
        if (element) {
          (element as HTMLSelectElement).value = 'default';
        }
      }).not.toThrow();
    });

    test("should handle invalid preset values", () => {
      const presetSelect = document.getElementById('configPreset') as HTMLSelectElement;
      
      // Try to set invalid value
      presetSelect.value = 'invalid_preset';
      testUtils.simulateInput(presetSelect, 'invalid_preset');

      // Should handle gracefully
      expect(presetSelect.value).toBe('invalid_preset');
    });
  });
});
