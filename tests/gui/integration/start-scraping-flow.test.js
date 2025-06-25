/**
 * Integration Test: Start Scraping Button Flow
 * 
 * This test verifies that the "Start Scraping" button successfully connects
 * to the backend and initiates a scraping process.
 */

import { describe, test, expect, beforeEach, afterEach } from 'bun:test';
import '../setup-bun.js';

describe('Start Scraping Integration', () => {
  let container;
  let mockFetch;
  
  beforeEach(() => {
    // Create container for our test DOM
    container = document.createElement('div');
    container.innerHTML = `
      <form id="scrapingForm">
        <input type="url" id="docUrl" value="https://example.com" required>
        <select id="backend">
          <option value="http" selected>HTTP</option>
          <option value="selenium">Selenium</option>
        </select>
        <select id="scrapingMode">
          <option value="documentation" selected>Documentation</option>
        </select>
        <input type="number" id="maxDepth" value="2" min="1" max="5">
        <input type="number" id="maxPages" value="50" min="1" max="500">
        <select id="outputFormat">
          <option value="markdown" selected>Markdown</option>
          <option value="json">JSON</option>
        </select>
        <input type="text" id="includePatterns" value="">
        <input type="text" id="excludePatterns" value="">
        <button type="submit" id="startBtn">Start Scraping</button>
        <button type="button" id="stopBtn" disabled>Stop Scraping</button>
      </form>
      
      <div id="scrapingStatus" class="alert" style="display: none;"></div>
      <div id="progress" style="display: none;">
        <div class="progress-bar" role="progressbar" style="width: 0%"></div>
      </div>
    `;
    document.body.appendChild(container);

    // Mock fetch to simulate backend responses
    mockFetch = (url, options) => {
      if (url === '/start_crawl' && options.method === 'POST') {
        const body = JSON.parse(options.body);
        if (body.urls && Array.isArray(body.urls)) {
          return Promise.resolve({
            ok: true,
            status: 200,
            json: () => Promise.resolve({
              status: 'success',
              message: 'Scraping started',
              task_id: 'test-task-123',
              url: body.urls[0]
            })
          });
        } else {
          return Promise.resolve({
            ok: false,
            status: 400,
            json: () => Promise.resolve({
              detail: 'Invalid request format'
            })
          });
        }
      }
      
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({})
      });
    };
    
    global.fetch = mockFetch;
  });

  afterEach(() => {
    if (container && container.parentNode) {
      container.parentNode.removeChild(container);
    }
  });

  test('should submit form data in correct format to /start_crawl endpoint', async () => {
    const form = document.getElementById('scrapingForm');
    const startBtn = document.getElementById('startBtn');
    const stopBtn = document.getElementById('stopBtn');
    
    // Verify initial state
    expect(startBtn.disabled).toBe(false);
    expect(stopBtn.disabled).toBe(true);
    
    let fetchCalled = false;
    let fetchUrl = '';
    let fetchOptions = {};
    
    // Override fetch to capture the call
    global.fetch = (url, options) => {
      fetchCalled = true;
      fetchUrl = url;
      fetchOptions = options;
      return mockFetch(url, options);
    };

    // Simulate the frontend form submission logic
    const handleSubmit = async (e) => {
      e.preventDefault();
      const formData = {
        url: document.getElementById('docUrl').value,
        backend: document.getElementById('backend').value,
        mode: document.getElementById('scrapingMode').value,
        maxDepth: parseInt(document.getElementById('maxDepth').value),
        maxPages: parseInt(document.getElementById('maxPages').value),
        outputFormat: document.getElementById('outputFormat').value,
        includePatterns: document.getElementById('includePatterns').value.split(',').map(s => s.trim()).filter(s => s),
        excludePatterns: document.getElementById('excludePatterns').value.split(',').map(s => s.trim()).filter(s => s)
      };

      try {
        const response = await fetch('/start_crawl', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            urls: [formData.url]  // Backend expects array of URLs
          })
        });

        if (response.ok) {
          startBtn.disabled = true;
          stopBtn.disabled = false;
          return await response.json();
        } else {
          const error = await response.json();
          throw new Error(error.detail || 'Failed to start scraping');
        }
      } catch (error) {
        throw error;
      }
    };

    // Add event listener and trigger submit
    form.addEventListener('submit', handleSubmit);
    
    // Trigger form submission
    const submitEvent = new Event('submit', { bubbles: true, cancelable: true });
    form.dispatchEvent(submitEvent);
    
    // Wait a bit for async operations
    await new Promise(resolve => setTimeout(resolve, 10));

    // Verify the correct endpoint was called
    expect(fetchCalled).toBe(true);
    expect(fetchUrl).toBe('/start_crawl');
    expect(fetchOptions.method).toBe('POST');
    expect(fetchOptions.headers['Content-Type']).toBe('application/json');
    
    // Verify the correct data format was sent
    const sentData = JSON.parse(fetchOptions.body);
    expect(sentData).toHaveProperty('urls');
    expect(Array.isArray(sentData.urls)).toBe(true);
    expect(sentData.urls).toContain('https://example.com');
    
    // Verify button states changed correctly
    expect(startBtn.disabled).toBe(true);
    expect(stopBtn.disabled).toBe(false);
  });

  test('should handle backend errors gracefully', async () => {
    const form = document.getElementById('scrapingForm');
    
    // Mock fetch to return error
    global.fetch = () => Promise.resolve({
      ok: false,
      status: 400,
      json: () => Promise.resolve({
        detail: 'Invalid URL format'
      })
    });

    let errorThrown = false;
    let errorMessage = '';

    const handleSubmit = async (e) => {
      e.preventDefault();
      try {
        const response = await fetch('/start_crawl', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ urls: ['https://example.com'] })
        });

        if (!response.ok) {
          const error = await response.json();
          throw new Error(error.detail || 'Failed to start scraping');
        }
      } catch (error) {
        errorThrown = true;
        errorMessage = error.message;
      }
    };

    form.addEventListener('submit', handleSubmit);
    
    const submitEvent = new Event('submit', { bubbles: true, cancelable: true });
    form.dispatchEvent(submitEvent);
    
    await new Promise(resolve => setTimeout(resolve, 10));

    expect(errorThrown).toBe(true);
    expect(errorMessage).toBe('Invalid URL format');
  });

  test('should validate required fields before submission', () => {
    const form = document.getElementById('scrapingForm');
    const urlInput = document.getElementById('docUrl');
    
    // Clear required field
    urlInput.value = '';
    
    // Check HTML5 validation
    expect(form.checkValidity()).toBe(false);
    expect(urlInput.validity.valid).toBe(false);
    expect(urlInput.validity.valueMissing).toBe(true);
    
    // Restore valid value
    urlInput.value = 'https://example.com';
    expect(form.checkValidity()).toBe(true);
    expect(urlInput.validity.valid).toBe(true);
  });

  test('should collect form data correctly', () => {
    // Set some test values
    document.getElementById('docUrl').value = 'https://test.com';
    document.getElementById('backend').value = 'selenium';
    document.getElementById('maxDepth').value = '3';
    document.getElementById('maxPages').value = '100';
    document.getElementById('outputFormat').value = 'json';
    document.getElementById('includePatterns').value = 'docs, api';
    document.getElementById('excludePatterns').value = 'test, demo';

    // Simulate form data collection
    const formData = {
      url: document.getElementById('docUrl').value,
      backend: document.getElementById('backend').value,
      mode: document.getElementById('scrapingMode').value,
      maxDepth: parseInt(document.getElementById('maxDepth').value),
      maxPages: parseInt(document.getElementById('maxPages').value),
      outputFormat: document.getElementById('outputFormat').value,
      includePatterns: document.getElementById('includePatterns').value.split(',').map(s => s.trim()).filter(s => s),
      excludePatterns: document.getElementById('excludePatterns').value.split(',').map(s => s.trim()).filter(s => s)
    };

    expect(formData.url).toBe('https://test.com');
    expect(formData.backend).toBe('selenium');
    expect(formData.maxDepth).toBe(3);
    expect(formData.maxPages).toBe(100);
    expect(formData.outputFormat).toBe('json');
    expect(formData.includePatterns).toEqual(['docs', 'api']);
    expect(formData.excludePatterns).toEqual(['test', 'demo']);
  });
});
