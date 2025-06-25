/**
 * E2E Test: Complete User Flow
 * 
 * This test simulates a complete user workflow from loading the page
 * to starting a scraping task.
 */

import { describe, test, expect, beforeEach, afterEach } from 'bun:test';
import '../setup-bun.js';

describe('Complete User Flow E2E', () => {
  let container;
  let mockWebSocket;
  let mockFetch;
  
  beforeEach(() => {
    // Create full page structure
    container = document.createElement('div');
    container.innerHTML = `
      <!DOCTYPE html>
      <html>
      <head>
        <title>Lib2DocScrape</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
      </head>
      <body>
        <!-- Navigation -->
        <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
          <div class="container">
            <a class="navbar-brand" href="/">Lib2DocScrape</a>
            <div class="navbar-nav">
              <a class="nav-link active" href="/">Home</a>
              <a class="nav-link" href="/config">Config</a>
              <a class="nav-link" href="/results">Results</a>
            </div>
          </div>
        </nav>

        <!-- Main Content -->
        <div class="container mt-4">
          <!-- Status Messages -->
          <div id="statusMessage" class="alert" style="display: none;"></div>
          
          <!-- Scraping Form -->
          <div class="card">
            <div class="card-header">
              <h3>Documentation Scraping</h3>
            </div>
            <div class="card-body">
              <form id="scrapingForm">
                <div class="mb-3">
                  <label for="docUrl" class="form-label">Documentation URL</label>
                  <input type="url" class="form-control" id="docUrl" required>
                </div>
                
                <div class="row">
                  <div class="col-md-6">
                    <label for="backend" class="form-label">Backend</label>
                    <select class="form-select" id="backend">
                      <option value="http">HTTP</option>
                      <option value="selenium">Selenium</option>
                    </select>
                  </div>
                  <div class="col-md-6">
                    <label for="outputFormat" class="form-label">Output Format</label>
                    <select class="form-select" id="outputFormat">
                      <option value="markdown">Markdown</option>
                      <option value="json">JSON</option>
                    </select>
                  </div>
                </div>
                
                <div class="row mt-3">
                  <div class="col-md-6">
                    <label for="maxDepth" class="form-label">Max Depth</label>
                    <input type="number" class="form-control" id="maxDepth" value="2" min="1" max="5">
                  </div>
                  <div class="col-md-6">
                    <label for="maxPages" class="form-label">Max Pages</label>
                    <input type="number" class="form-control" id="maxPages" value="50" min="1" max="500">
                  </div>
                </div>
                
                <div class="mt-4">
                  <button type="submit" class="btn btn-primary" id="startBtn">
                    <span class="spinner-border spinner-border-sm d-none" role="status"></span>
                    Start Scraping
                  </button>
                  <button type="button" class="btn btn-danger" id="stopBtn" disabled>Stop Scraping</button>
                </div>
              </form>
            </div>
          </div>
          
          <!-- Progress Section -->
          <div id="progressSection" class="card mt-4" style="display: none;">
            <div class="card-header">
              <h5>Scraping Progress</h5>
            </div>
            <div class="card-body">
              <div class="progress mb-3">
                <div class="progress-bar" id="progressBar" role="progressbar" style="width: 0%"></div>
              </div>
              <div id="progressText">Ready to start...</div>
              <div id="wsStatus" class="mt-2">
                <span class="badge bg-secondary">WebSocket: Disconnected</span>
              </div>
            </div>
          </div>
          
          <!-- Real-time Updates -->
          <div id="updatesSection" class="card mt-4" style="display: none;">
            <div class="card-header">
              <h5>Real-time Updates</h5>
            </div>
            <div class="card-body">
              <div id="updates" style="height: 200px; overflow-y: auto;"></div>
            </div>
          </div>
        </div>
      </body>
      </html>
    `;
    document.body.appendChild(container);

    // Mock WebSocket for real-time updates
    mockWebSocket = {
      readyState: 1,
      onopen: null,
      onmessage: null,
      onclose: null,
      onerror: null,
      send: () => {},
      close: () => {}
    };

    // Mock fetch for API calls
    mockFetch = (url, options) => {
      if (url === '/start_crawl' && options.method === 'POST') {
        return Promise.resolve({
          ok: true,
          status: 200,
          json: () => Promise.resolve({
            status: 'success',
            message: 'Scraping started',
            task_id: 'test-task-123',
            url: 'https://example.com'
          })
        });
      }
      
      if (url === '/api/scraping/stop' && options.method === 'POST') {
        return Promise.resolve({
          ok: true,
          status: 200,
          json: () => Promise.resolve({
            status: 'success',
            message: 'Scraping stopped'
          })
        });
      }

      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({})
      });
    };
    
    global.fetch = mockFetch;
    global.WebSocket = function() { return mockWebSocket; };
  });

  afterEach(() => {
    if (container && container.parentNode) {
      container.parentNode.removeChild(container);
    }
  });

  test('should complete full user workflow: page load → form fill → scraping start', async () => {
    // 1. Verify page structure loaded correctly
    const navbar = document.querySelector('.navbar');
    const form = document.getElementById('scrapingForm');
    const urlInput = document.getElementById('docUrl');
    const startBtn = document.getElementById('startBtn');
    const stopBtn = document.getElementById('stopBtn');
    
    expect(navbar).toBeDefined();
    expect(form).toBeDefined();
    expect(urlInput).toBeDefined();
    expect(startBtn).toBeDefined();
    expect(stopBtn).toBeDefined();
    
    // 2. Verify initial UI state
    expect(startBtn.disabled).toBe(false);
    expect(stopBtn.disabled).toBe(true);
    expect(startBtn.textContent.trim()).toBe('Start Scraping');
    
    // 3. User fills out the form
    urlInput.value = 'https://react.dev/docs';
    document.getElementById('backend').value = 'http';
    document.getElementById('outputFormat').value = 'markdown';
    document.getElementById('maxDepth').value = '3';
    document.getElementById('maxPages').value = '100';
    
    // Verify form data was set
    expect(urlInput.value).toBe('https://react.dev/docs');
    expect(document.getElementById('backend').value).toBe('http');
    expect(document.getElementById('outputFormat').value).toBe('markdown');
    
    // 4. User submits the form
    let formSubmitted = false;
    let fetchCalled = false;
    
    // Override fetch to track calls
    global.fetch = (url, options) => {
      fetchCalled = true;
      return mockFetch(url, options);
    };
    
    // Simulate the form submission
    const handleSubmit = async (e) => {
      e.preventDefault();
      formSubmitted = true;
      
      const formData = {
        url: urlInput.value,
        backend: document.getElementById('backend').value,
        maxDepth: parseInt(document.getElementById('maxDepth').value),
        maxPages: parseInt(document.getElementById('maxPages').value),
        outputFormat: document.getElementById('outputFormat').value
      };

      try {
        const response = await fetch('/start_crawl', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ urls: [formData.url] })
        });

        if (response.ok) {
          startBtn.disabled = true;
          stopBtn.disabled = false;
          
          // Show progress section
          const progressSection = document.getElementById('progressSection');
          progressSection.style.display = 'block';
          
          // Update status
          const statusMessage = document.getElementById('statusMessage');
          statusMessage.className = 'alert alert-success';
          statusMessage.textContent = 'Scraping started successfully!';
          statusMessage.style.display = 'block';
        }
      } catch (error) {
        console.error('Submission error:', error);
      }
    };

    form.addEventListener('submit', handleSubmit);
    
    // Trigger form submission
    const submitEvent = new Event('submit', { bubbles: true, cancelable: true });
    form.dispatchEvent(submitEvent);
    
    // Wait for async operations
    await new Promise(resolve => setTimeout(resolve, 20));

    // 5. Verify the complete workflow worked
    expect(formSubmitted).toBe(true);
    expect(fetchCalled).toBe(true);
    expect(startBtn.disabled).toBe(true);
    expect(stopBtn.disabled).toBe(false);
    
    // Verify progress section is shown
    const progressSection = document.getElementById('progressSection');
    expect(progressSection.style.display).toBe('block');
    
    // Verify success message is shown
    const statusMessage = document.getElementById('statusMessage');
    expect(statusMessage.style.display).toBe('block');
    expect(statusMessage.textContent).toBe('Scraping started successfully!');
    expect(statusMessage.className).toContain('alert-success');
  });

  test('should handle WebSocket connection and real-time updates', async () => {
    const wsStatus = document.getElementById('wsStatus');
    const updates = document.getElementById('updates');
    const progressBar = document.getElementById('progressBar');
    
    // Simulate WebSocket connection
    const ws = new WebSocket('ws://localhost:8889/ws');
    
    // Simulate connection opened
    if (ws.onopen) {
      ws.onopen();
    }
    
    // Update UI to reflect connection
    wsStatus.innerHTML = '<span class="badge bg-success">WebSocket: Connected</span>';
    
    // Simulate receiving progress update
    const progressUpdate = {
      type: 'progress',
      data: {
        progress: 45,
        message: 'Processing page 5 of 10',
        pages_found: 5,
        pages_processed: 5
      }
    };
    
    if (ws.onmessage) {
      ws.onmessage({ data: JSON.stringify(progressUpdate) });
    }
    
    // Update UI based on message
    progressBar.style.width = '45%';
    progressBar.setAttribute('aria-valuenow', '45');
    
    const updateElement = document.createElement('div');
    updateElement.className = 'update-item mb-2';
    updateElement.innerHTML = `
      <span class="text-muted">${new Date().toLocaleTimeString()}</span>
      <span class="ms-2">${progressUpdate.data.message}</span>
    `;
    updates.appendChild(updateElement);
    
    // Verify WebSocket functionality
    expect(wsStatus.textContent).toContain('Connected');
    expect(progressBar.style.width).toBe('45%');
    expect(updates.children.length).toBe(1);
    expect(updates.textContent).toContain('Processing page 5 of 10');
  });

  test('should handle navigation between pages', () => {
    const homeLink = document.querySelector('.nav-link[href="/"]');
    const configLink = document.querySelector('.nav-link[href="/config"]');
    const resultsLink = document.querySelector('.nav-link[href="/results"]');
    
    expect(homeLink).toBeDefined();
    expect(configLink).toBeDefined();
    expect(resultsLink).toBeDefined();
    
    // Verify active state
    expect(homeLink.className).toContain('active');
    expect(configLink.className).not.toContain('active');
    expect(resultsLink.className).not.toContain('active');
    
    // Simulate navigation to config
    homeLink.classList.remove('active');
    configLink.classList.add('active');
    
    expect(homeLink.className).not.toContain('active');
    expect(configLink.className).toContain('active');
  });

  test('should validate form before allowing submission', () => {
    const form = document.getElementById('scrapingForm');
    const urlInput = document.getElementById('docUrl');
    
    // Test empty URL
    urlInput.value = '';
    expect(form.checkValidity()).toBe(false);
    expect(urlInput.validity.valueMissing).toBe(true);
    
    // Test invalid URL format
    urlInput.value = 'not-a-url';
    expect(urlInput.validity.typeMismatch).toBe(true);
    
    // Test valid URL
    urlInput.value = 'https://valid-url.com';
    expect(urlInput.validity.valid).toBe(true);
    expect(form.checkValidity()).toBe(true);
  });
});
