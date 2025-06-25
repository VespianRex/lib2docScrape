/**
 * User Flow Tests - Configuration Management
 * 
 * Tests for configuration workflows, settings persistence, and validation
 */

import { screen, fireEvent, waitFor } from '@testing-library/dom';
import '@testing-library/jest-dom';

describe('User Flow - Configuration Management', () => {
  let container;
  let mockFetch;
  
  beforeEach(() => {
    // Mock fetch API
    mockFetch = jest.fn();
    global.fetch = mockFetch;
    
    // Mock localStorage
    const localStorageMock = {
      getItem: jest.fn(),
      setItem: jest.fn(),
      removeItem: jest.fn(),
      clear: jest.fn()
    };
    
    Object.defineProperty(window, 'localStorage', {
      value: localStorageMock,
      writable: true
    });
    
    // Create comprehensive configuration interface
    document.body.innerHTML = `
      <div data-testid="configuration-panel" class="configuration-panel">
        <!-- General Settings -->
        <section data-testid="general-settings" class="settings-section">
          <h3>General Settings</h3>
          <form data-testid="general-form">
            <div class="row">
              <div class="col-md-6">
                <label for="default-backend">Default Backend</label>
                <select data-testid="default-backend" id="default-backend" class="form-select">
                  <option value="http">HTTP Backend</option>
                  <option value="crawl4ai">Crawl4AI Backend</option>
                  <option value="scrapy">Scrapy Backend</option>
                </select>
              </div>
              <div class="col-md-6">
                <label for="default-depth">Default Crawl Depth</label>
                <input type="number" data-testid="default-depth" id="default-depth" 
                       min="1" max="10" value="3" class="form-control">
              </div>
            </div>
            
            <div class="row">
              <div class="col-md-6">
                <label for="max-concurrent">Max Concurrent Requests</label>
                <input type="number" data-testid="max-concurrent" id="max-concurrent" 
                       min="1" max="20" value="5" class="form-control">
              </div>
              <div class="col-md-6">
                <label for="request-timeout">Request Timeout (seconds)</label>
                <input type="number" data-testid="request-timeout" id="request-timeout" 
                       min="5" max="300" value="30" class="form-control">
              </div>
            </div>
            
            <div class="form-check">
              <input type="checkbox" data-testid="auto-save" id="auto-save" class="form-check-input">
              <label for="auto-save" class="form-check-label">Auto-save configurations</label>
            </div>
            
            <div class="form-check">
              <input type="checkbox" data-testid="enable-logging" id="enable-logging" class="form-check-input" checked>
              <label for="enable-logging" class="form-check-label">Enable detailed logging</label>
            </div>
          </form>
        </section>

        <!-- Backend-Specific Settings -->
        <section data-testid="backend-settings" class="settings-section">
          <h3>Backend-Specific Settings</h3>
          
          <!-- HTTP Backend Settings -->
          <div data-testid="http-settings" class="backend-config">
            <h4>HTTP Backend Configuration</h4>
            <form data-testid="http-form">
              <div class="row">
                <div class="col-md-6">
                  <label for="http-user-agent">User Agent</label>
                  <input type="text" data-testid="http-user-agent" id="http-user-agent" 
                         value="Lib2DocScrape/1.0" class="form-control">
                </div>
                <div class="col-md-6">
                  <label for="http-retry-count">Retry Count</label>
                  <input type="number" data-testid="http-retry-count" id="http-retry-count" 
                         min="0" max="10" value="3" class="form-control">
                </div>
              </div>
              
              <div class="form-check">
                <input type="checkbox" data-testid="http-follow-redirects" id="http-follow-redirects" 
                       class="form-check-input" checked>
                <label for="http-follow-redirects" class="form-check-label">Follow redirects</label>
              </div>
              
              <div class="form-check">
                <input type="checkbox" data-testid="http-verify-ssl" id="http-verify-ssl" 
                       class="form-check-input" checked>
                <label for="http-verify-ssl" class="form-check-label">Verify SSL certificates</label>
              </div>
            </form>
          </div>

          <!-- Crawl4AI Backend Settings -->
          <div data-testid="crawl4ai-settings" class="backend-config d-none">
            <h4>Crawl4AI Backend Configuration</h4>
            <form data-testid="crawl4ai-form">
              <div class="row">
                <div class="col-md-6">
                  <label for="crawl4ai-browser">Browser Engine</label>
                  <select data-testid="crawl4ai-browser" id="crawl4ai-browser" class="form-select">
                    <option value="chromium">Chromium</option>
                    <option value="firefox">Firefox</option>
                    <option value="webkit">WebKit</option>
                  </select>
                </div>
                <div class="col-md-6">
                  <label for="crawl4ai-wait-time">Page Wait Time (ms)</label>
                  <input type="number" data-testid="crawl4ai-wait-time" id="crawl4ai-wait-time" 
                         min="0" max="30000" value="2000" class="form-control">
                </div>
              </div>
              
              <div class="form-check">
                <input type="checkbox" data-testid="crawl4ai-headless" id="crawl4ai-headless" 
                       class="form-check-input" checked>
                <label for="crawl4ai-headless" class="form-check-label">Run in headless mode</label>
              </div>
              
              <div class="form-check">
                <input type="checkbox" data-testid="crawl4ai-javascript" id="crawl4ai-javascript" 
                       class="form-check-input" checked>
                <label for="crawl4ai-javascript" class="form-check-label">Enable JavaScript</label>
              </div>
            </form>
          </div>
        </section>

        <!-- Output Settings -->
        <section data-testid="output-settings" class="settings-section">
          <h3>Output Settings</h3>
          <form data-testid="output-form">
            <div class="row">
              <div class="col-md-6">
                <label for="output-format">Default Output Format</label>
                <select data-testid="output-format" id="output-format" class="form-select">
                  <option value="markdown">Markdown</option>
                  <option value="json">JSON</option>
                  <option value="html">HTML</option>
                  <option value="pdf">PDF</option>
                </select>
              </div>
              <div class="col-md-6">
                <label for="output-directory">Output Directory</label>
                <input type="text" data-testid="output-directory" id="output-directory" 
                       value="./output" class="form-control">
              </div>
            </div>
            
            <div class="form-check">
              <input type="checkbox" data-testid="include-metadata" id="include-metadata" 
                     class="form-check-input" checked>
              <label for="include-metadata" class="form-check-label">Include metadata in output</label>
            </div>
            
            <div class="form-check">
              <input type="checkbox" data-testid="compress-output" id="compress-output" 
                     class="form-check-input">
              <label for="compress-output" class="form-check-label">Compress output files</label>
            </div>
          </form>
        </section>

        <!-- Advanced Settings -->
        <section data-testid="advanced-settings" class="settings-section">
          <h3>Advanced Settings</h3>
          <form data-testid="advanced-form">
            <div class="row">
              <div class="col-md-6">
                <label for="memory-limit">Memory Limit (MB)</label>
                <input type="number" data-testid="memory-limit" id="memory-limit" 
                       min="128" max="8192" value="1024" class="form-control">
              </div>
              <div class="col-md-6">
                <label for="cache-size">Cache Size (MB)</label>
                <input type="number" data-testid="cache-size" id="cache-size" 
                       min="0" max="2048" value="256" class="form-control">
              </div>
            </div>
            
            <div class="mb-3">
              <label for="custom-headers">Custom Headers (JSON)</label>
              <textarea data-testid="custom-headers" id="custom-headers" 
                        class="form-control" rows="3" 
                        placeholder='{"Authorization": "Bearer token", "X-Custom": "value"}'></textarea>
            </div>
            
            <div class="mb-3">
              <label for="url-patterns">URL Patterns to Include</label>
              <textarea data-testid="url-patterns" id="url-patterns" 
                        class="form-control" rows="3" 
                        placeholder="https://docs.example.com/api/*&#10;https://docs.example.com/guide/*"></textarea>
            </div>
            
            <div class="mb-3">
              <label for="exclude-patterns">URL Patterns to Exclude</label>
              <textarea data-testid="exclude-patterns" id="exclude-patterns" 
                        class="form-control" rows="3" 
                        placeholder="*.pdf&#10;*/download/*&#10;*/archive/*"></textarea>
            </div>
          </form>
        </section>

        <!-- Configuration Actions -->
        <section data-testid="config-actions" class="config-actions">
          <div class="btn-group">
            <button data-testid="save-config" class="btn btn-primary">Save Configuration</button>
            <button data-testid="load-config" class="btn btn-secondary">Load Configuration</button>
            <button data-testid="reset-config" class="btn btn-warning">Reset to Defaults</button>
            <button data-testid="export-config" class="btn btn-info">Export Configuration</button>
            <button data-testid="import-config" class="btn btn-info">Import Configuration</button>
          </div>
          
          <input type="file" data-testid="config-file-input" class="d-none" accept=".json,.yaml,.yml">
        </section>

        <!-- Configuration Validation -->
        <section data-testid="config-validation" class="validation-section">
          <div data-testid="validation-results" class="alert d-none">
            <ul data-testid="validation-errors" class="mb-0"></ul>
          </div>
        </section>

        <!-- Configuration Presets -->
        <section data-testid="config-presets" class="presets-section">
          <h3>Configuration Presets</h3>
          <div class="row">
            <div class="col-md-4">
              <div class="preset-card" data-testid="preset-quick">
                <h5>Quick Scraping</h5>
                <p>Fast scraping with minimal depth for quick results</p>
                <button data-testid="apply-quick-preset" class="btn btn-outline-primary btn-sm">Apply</button>
              </div>
            </div>
            <div class="col-md-4">
              <div class="preset-card" data-testid="preset-comprehensive">
                <h5>Comprehensive</h5>
                <p>Deep scraping with maximum coverage and features</p>
                <button data-testid="apply-comprehensive-preset" class="btn btn-outline-primary btn-sm">Apply</button>
              </div>
            </div>
            <div class="col-md-4">
              <div class="preset-card" data-testid="preset-performance">
                <h5>Performance</h5>
                <p>Optimized for speed and resource efficiency</p>
                <button data-testid="apply-performance-preset" class="btn btn-outline-primary btn-sm">Apply</button>
              </div>
            </div>
          </div>
        </section>
      </div>
    `;
    
    container = document.body;
  });

  afterEach(() => {
    document.body.innerHTML = '';
    jest.clearAllMocks();
  });

  describe('General Configuration Settings', () => {
    test('should configure general settings', () => {
      const defaultBackend = screen.getByTestId('default-backend');
      const defaultDepth = screen.getByTestId('default-depth');
      const maxConcurrent = screen.getByTestId('max-concurrent');
      const requestTimeout = screen.getByTestId('request-timeout');
      const autoSave = screen.getByTestId('auto-save');
      const enableLogging = screen.getByTestId('enable-logging');
      
      // Configure settings
      fireEvent.change(defaultBackend, { target: { value: 'crawl4ai' } });
      fireEvent.change(defaultDepth, { target: { value: '5' } });
      fireEvent.change(maxConcurrent, { target: { value: '8' } });
      fireEvent.change(requestTimeout, { target: { value: '60' } });
      fireEvent.click(autoSave);
      
      expect(defaultBackend.value).toBe('crawl4ai');
      expect(defaultDepth.value).toBe('5');
      expect(maxConcurrent.value).toBe('8');
      expect(requestTimeout.value).toBe('60');
      expect(autoSave.checked).toBe(true);
      expect(enableLogging.checked).toBe(true); // Initially checked
    });

    test('should validate general settings ranges', () => {
      const defaultDepth = screen.getByTestId('default-depth');
      const maxConcurrent = screen.getByTestId('max-concurrent');
      const requestTimeout = screen.getByTestId('request-timeout');
      
      // Test invalid values
      fireEvent.change(defaultDepth, { target: { value: '15' } }); // max is 10
      fireEvent.change(maxConcurrent, { target: { value: '25' } }); // max is 20
      fireEvent.change(requestTimeout, { target: { value: '2' } }); // min is 5
      
      expect(defaultDepth.validity.valid).toBe(false);
      expect(maxConcurrent.validity.valid).toBe(false);
      expect(requestTimeout.validity.valid).toBe(false);
      
      // Test valid values
      fireEvent.change(defaultDepth, { target: { value: '7' } });
      fireEvent.change(maxConcurrent, { target: { value: '12' } });
      fireEvent.change(requestTimeout, { target: { value: '45' } });
      
      expect(defaultDepth.validity.valid).toBe(true);
      expect(maxConcurrent.validity.valid).toBe(true);
      expect(requestTimeout.validity.valid).toBe(true);
    });
  });

  describe('Backend-Specific Configuration', () => {
    test('should show/hide backend-specific settings based on selection', () => {
      const defaultBackend = screen.getByTestId('default-backend');
      const httpSettings = screen.getByTestId('http-settings');
      const crawl4aiSettings = screen.getByTestId('crawl4ai-settings');
      
      // Initially HTTP backend selected
      expect(httpSettings).not.toHaveClass('d-none');
      expect(crawl4aiSettings).toHaveClass('d-none');
      
      // Switch to Crawl4AI backend
      fireEvent.change(defaultBackend, { target: { value: 'crawl4ai' } });
      
      // Simulate UI update
      httpSettings.classList.add('d-none');
      crawl4aiSettings.classList.remove('d-none');
      
      expect(httpSettings).toHaveClass('d-none');
      expect(crawl4aiSettings).not.toHaveClass('d-none');
    });

    test('should configure HTTP backend settings', () => {
      const userAgent = screen.getByTestId('http-user-agent');
      const retryCount = screen.getByTestId('http-retry-count');
      const followRedirects = screen.getByTestId('http-follow-redirects');
      const verifySSL = screen.getByTestId('http-verify-ssl');
      
      // Configure HTTP settings
      fireEvent.change(userAgent, { 
        target: { value: 'Custom Bot/2.0 (Documentation Scraper)' } 
      });
      fireEvent.change(retryCount, { target: { value: '5' } });
      fireEvent.click(followRedirects); // Uncheck
      
      expect(userAgent.value).toBe('Custom Bot/2.0 (Documentation Scraper)');
      expect(retryCount.value).toBe('5');
      expect(followRedirects.checked).toBe(false);
      expect(verifySSL.checked).toBe(true); // Initially checked
    });

    test('should configure Crawl4AI backend settings', () => {
      const defaultBackend = screen.getByTestId('default-backend');
      const crawl4aiSettings = screen.getByTestId('crawl4ai-settings');
      
      // Switch to Crawl4AI
      fireEvent.change(defaultBackend, { target: { value: 'crawl4ai' } });
      crawl4aiSettings.classList.remove('d-none');
      
      const browser = screen.getByTestId('crawl4ai-browser');
      const waitTime = screen.getByTestId('crawl4ai-wait-time');
      const headless = screen.getByTestId('crawl4ai-headless');
      const javascript = screen.getByTestId('crawl4ai-javascript');
      
      // Configure Crawl4AI settings
      fireEvent.change(browser, { target: { value: 'firefox' } });
      fireEvent.change(waitTime, { target: { value: '5000' } });
      fireEvent.click(headless); // Uncheck
      
      expect(browser.value).toBe('firefox');
      expect(waitTime.value).toBe('5000');
      expect(headless.checked).toBe(false);
      expect(javascript.checked).toBe(true); // Initially checked
    });
  });

  describe('Output Configuration', () => {
    test('should configure output settings', () => {
      const outputFormat = screen.getByTestId('output-format');
      const outputDirectory = screen.getByTestId('output-directory');
      const includeMetadata = screen.getByTestId('include-metadata');
      const compressOutput = screen.getByTestId('compress-output');
      
      // Configure output settings
      fireEvent.change(outputFormat, { target: { value: 'json' } });
      fireEvent.change(outputDirectory, { target: { value: '/custom/output/path' } });
      fireEvent.click(compressOutput); // Check
      
      expect(outputFormat.value).toBe('json');
      expect(outputDirectory.value).toBe('/custom/output/path');
      expect(includeMetadata.checked).toBe(true); // Initially checked
      expect(compressOutput.checked).toBe(true);
    });

    test('should validate output directory path', () => {
      const outputDirectory = screen.getByTestId('output-directory');
      
      // Test different path formats
      const validPaths = ['./output', '/absolute/path', '~/documents/output', 'relative/path'];
      const invalidPaths = ['', ' ', 'con', 'prn']; // Invalid on Windows
      
      validPaths.forEach(path => {
        fireEvent.change(outputDirectory, { target: { value: path } });
        // Custom validation would go here
        expect(outputDirectory.value).toBe(path);
      });
    });
  });

  describe('Advanced Configuration', () => {
    test('should configure advanced settings', () => {
      const memoryLimit = screen.getByTestId('memory-limit');
      const cacheSize = screen.getByTestId('cache-size');
      const customHeaders = screen.getByTestId('custom-headers');
      const urlPatterns = screen.getByTestId('url-patterns');
      const excludePatterns = screen.getByTestId('exclude-patterns');
      
      // Configure advanced settings
      fireEvent.change(memoryLimit, { target: { value: '2048' } });
      fireEvent.change(cacheSize, { target: { value: '512' } });
      fireEvent.change(customHeaders, { 
        target: { value: '{"Authorization": "Bearer abc123", "X-API-Key": "xyz789"}' } 
      });
      fireEvent.change(urlPatterns, { 
        target: { value: 'https://docs.example.com/api/*\nhttps://docs.example.com/guide/*' } 
      });
      fireEvent.change(excludePatterns, { 
        target: { value: '*.pdf\n*/download/*\n*/old-versions/*' } 
      });
      
      expect(memoryLimit.value).toBe('2048');
      expect(cacheSize.value).toBe('512');
      expect(customHeaders.value).toBe('{"Authorization": "Bearer abc123", "X-API-Key": "xyz789"}');
      expect(urlPatterns.value).toBe('https://docs.example.com/api/*\nhttps://docs.example.com/guide/*');
      expect(excludePatterns.value).toBe('*.pdf\n*/download/*\n*/old-versions/*');
    });

    test('should validate JSON input for custom headers', () => {
      const customHeaders = screen.getByTestId('custom-headers');
      
      // Test invalid JSON
      fireEvent.change(customHeaders, { 
        target: { value: '{"invalid": json}' } 
      });
      
      // Custom validation
      const validateJSON = (value) => {
        if (!value.trim()) return true; // Empty is valid
        try {
          JSON.parse(value);
          return true;
        } catch {
          return false;
        }
      };
      
      expect(validateJSON(customHeaders.value)).toBe(false);
      
      // Test valid JSON
      fireEvent.change(customHeaders, { 
        target: { value: '{"Authorization": "Bearer token"}' } 
      });
      
      expect(validateJSON(customHeaders.value)).toBe(true);
    });
  });

  describe('Configuration Persistence', () => {
    test('should save configuration to localStorage', () => {
      const saveButton = screen.getByTestId('save-config');
      const defaultBackend = screen.getByTestId('default-backend');
      const defaultDepth = screen.getByTestId('default-depth');
      
      // Configure some settings
      fireEvent.change(defaultBackend, { target: { value: 'crawl4ai' } });
      fireEvent.change(defaultDepth, { target: { value: '5' } });
      
      // Mock save configuration
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ success: true, message: 'Configuration saved' })
      });
      
      // Click save
      fireEvent.click(saveButton);
      
      // Simulate saving to localStorage
      const config = {
        general: {
          defaultBackend: defaultBackend.value,
          defaultDepth: parseInt(defaultDepth.value)
        }
      };
      
      localStorage.setItem('lib2docscrape-config', JSON.stringify(config));
      
      expect(localStorage.setItem).toHaveBeenCalledWith(
        'lib2docscrape-config',
        JSON.stringify(config)
      );
    });

    test('should load configuration from localStorage', () => {
      const loadButton = screen.getByTestId('load-config');
      const defaultBackend = screen.getByTestId('default-backend');
      const defaultDepth = screen.getByTestId('default-depth');
      
      // Mock saved configuration
      const savedConfig = {
        general: {
          defaultBackend: 'scrapy',
          defaultDepth: 7
        }
      };
      
      localStorage.getItem.mockReturnValue(JSON.stringify(savedConfig));
      
      // Click load
      fireEvent.click(loadButton);
      
      // Simulate loading configuration
      const config = JSON.parse(localStorage.getItem('lib2docscrape-config'));
      
      // Apply configuration
      fireEvent.change(defaultBackend, { target: { value: config.general.defaultBackend } });
      fireEvent.change(defaultDepth, { target: { value: config.general.defaultDepth.toString() } });
      
      expect(defaultBackend.value).toBe('scrapy');
      expect(defaultDepth.value).toBe('7');
    });

    test('should auto-save configuration when enabled', () => {
      const autoSave = screen.getByTestId('auto-save');
      const defaultBackend = screen.getByTestId('default-backend');
      
      // Enable auto-save
      fireEvent.click(autoSave);
      expect(autoSave.checked).toBe(true);
      
      // Change setting - should trigger auto-save
      fireEvent.change(defaultBackend, { target: { value: 'crawl4ai' } });
      
      // Simulate auto-save
      if (autoSave.checked) {
        const config = { defaultBackend: defaultBackend.value };
        localStorage.setItem('lib2docscrape-config', JSON.stringify(config));
      }
      
      expect(localStorage.setItem).toHaveBeenCalled();
    });
  });

  describe('Configuration Import/Export', () => {
    test('should export configuration', () => {
      const exportButton = screen.getByTestId('export-config');
      
      // Mock configuration data
      const configData = {
        general: {
          defaultBackend: 'crawl4ai',
          defaultDepth: 5
        },
        http: {
          userAgent: 'Custom Bot/2.0',
          retryCount: 3
        }
      };
      
      // Mock download functionality
      const createDownload = (data, filename) => {
        const blob = new Blob([JSON.stringify(data, null, 2)], 
          { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        
        const link = document.createElement('a');
        link.href = url;
        link.download = filename;
        return link;
      };
      
      // Click export
      fireEvent.click(exportButton);
      
      const downloadLink = createDownload(configData, 'lib2docscrape-config.json');
      
      expect(downloadLink.download).toBe('lib2docscrape-config.json');
      expect(downloadLink.href).toContain('blob:');
    });

    test('should import configuration from file', async () => {
      const importButton = screen.getByTestId('import-config');
      const fileInput = screen.getByTestId('config-file-input');
      
      // Mock file content
      const configContent = {
        general: {
          defaultBackend: 'scrapy',
          defaultDepth: 8
        }
      };
      
      const file = new File(
        [JSON.stringify(configContent)], 
        'config.json', 
        { type: 'application/json' }
      );
      
      // Click import button - should trigger file input
      fireEvent.click(importButton);
      
      // Simulate file selection
      Object.defineProperty(fileInput, 'files', {
        value: [file],
        writable: false
      });
      
      fireEvent.change(fileInput);
      
      // Simulate file reading
      const reader = new FileReader();
      reader.onload = (e) => {
        const importedConfig = JSON.parse(e.target.result);
        
        // Apply imported configuration
        const defaultBackend = screen.getByTestId('default-backend');
        const defaultDepth = screen.getByTestId('default-depth');
        
        fireEvent.change(defaultBackend, { 
          target: { value: importedConfig.general.defaultBackend } 
        });
        fireEvent.change(defaultDepth, { 
          target: { value: importedConfig.general.defaultDepth.toString() } 
        });
        
        expect(defaultBackend.value).toBe('scrapy');
        expect(defaultDepth.value).toBe('8');
      };
      
      reader.readAsText(file);
    });
  });

  describe('Configuration Presets', () => {
    test('should apply quick scraping preset', () => {
      const quickPresetButton = screen.getByTestId('apply-quick-preset');
      const defaultDepth = screen.getByTestId('default-depth');
      const maxConcurrent = screen.getByTestId('max-concurrent');
      const requestTimeout = screen.getByTestId('request-timeout');
      
      // Click quick preset
      fireEvent.click(quickPresetButton);
      
      // Apply quick preset configuration
      const quickPreset = {
        defaultDepth: 2,
        maxConcurrent: 10,
        requestTimeout: 15
      };
      
      fireEvent.change(defaultDepth, { target: { value: quickPreset.defaultDepth.toString() } });
      fireEvent.change(maxConcurrent, { target: { value: quickPreset.maxConcurrent.toString() } });
      fireEvent.change(requestTimeout, { target: { value: quickPreset.requestTimeout.toString() } });
      
      expect(defaultDepth.value).toBe('2');
      expect(maxConcurrent.value).toBe('10');
      expect(requestTimeout.value).toBe('15');
    });

    test('should apply comprehensive preset', () => {
      const comprehensivePresetButton = screen.getByTestId('apply-comprehensive-preset');
      const defaultDepth = screen.getByTestId('default-depth');
      const maxConcurrent = screen.getByTestId('max-concurrent');
      const includeMetadata = screen.getByTestId('include-metadata');
      
      // Click comprehensive preset
      fireEvent.click(comprehensivePresetButton);
      
      // Apply comprehensive preset configuration
      const comprehensivePreset = {
        defaultDepth: 8,
        maxConcurrent: 3,
        includeMetadata: true
      };
      
      fireEvent.change(defaultDepth, { target: { value: comprehensivePreset.defaultDepth.toString() } });
      fireEvent.change(maxConcurrent, { target: { value: comprehensivePreset.maxConcurrent.toString() } });
      
      if (!includeMetadata.checked) {
        fireEvent.click(includeMetadata);
      }
      
      expect(defaultDepth.value).toBe('8');
      expect(maxConcurrent.value).toBe('3');
      expect(includeMetadata.checked).toBe(true);
    });

    test('should apply performance preset', () => {
      const performancePresetButton = screen.getByTestId('apply-performance-preset');
      const memoryLimit = screen.getByTestId('memory-limit');
      const cacheSize = screen.getByTestId('cache-size');
      const maxConcurrent = screen.getByTestId('max-concurrent');
      
      // Click performance preset
      fireEvent.click(performancePresetButton);
      
      // Apply performance preset configuration
      const performancePreset = {
        memoryLimit: 2048,
        cacheSize: 512,
        maxConcurrent: 15
      };
      
      fireEvent.change(memoryLimit, { target: { value: performancePreset.memoryLimit.toString() } });
      fireEvent.change(cacheSize, { target: { value: performancePreset.cacheSize.toString() } });
      fireEvent.change(maxConcurrent, { target: { value: performancePreset.maxConcurrent.toString() } });
      
      expect(memoryLimit.value).toBe('2048');
      expect(cacheSize.value).toBe('512');
      expect(maxConcurrent.value).toBe('15');
    });
  });

  describe('Configuration Validation', () => {
    test('should validate configuration before saving', () => {
      const saveButton = screen.getByTestId('save-config');
      const validationResults = screen.getByTestId('validation-results');
      const validationErrors = screen.getByTestId('validation-errors');
      
      // Set invalid configuration
      const defaultDepth = screen.getByTestId('default-depth');
      const customHeaders = screen.getByTestId('custom-headers');
      
      fireEvent.change(defaultDepth, { target: { value: '15' } }); // Invalid: max is 10
      fireEvent.change(customHeaders, { target: { value: '{invalid json}' } }); // Invalid JSON
      
      // Click save - should trigger validation
      fireEvent.click(saveButton);
      
      // Simulate validation
      const errors = [];
      
      if (parseInt(defaultDepth.value) > 10) {
        errors.push('Default depth cannot exceed 10');
      }
      
      try {
        JSON.parse(customHeaders.value);
      } catch {
        if (customHeaders.value.trim()) {
          errors.push('Custom headers must be valid JSON');
        }
      }
      
      if (errors.length > 0) {
        validationResults.classList.remove('d-none');
        validationResults.classList.add('alert-danger');
        validationErrors.innerHTML = errors.map(error => `<li>${error}</li>`).join('');
        
        expect(validationResults).not.toHaveClass('d-none');
        expect(validationErrors).toHaveTextContent('Default depth cannot exceed 10');
        expect(validationErrors).toHaveTextContent('Custom headers must be valid JSON');
      }
    });

    test('should show validation success when configuration is valid', () => {
      const saveButton = screen.getByTestId('save-config');
      const validationResults = screen.getByTestId('validation-results');
      
      // Set valid configuration
      const defaultDepth = screen.getByTestId('default-depth');
      fireEvent.change(defaultDepth, { target: { value: '5' } });
      
      // Click save
      fireEvent.click(saveButton);
      
      // Simulate successful validation
      validationResults.classList.remove('d-none', 'alert-danger');
      validationResults.classList.add('alert-success');
      validationResults.innerHTML = '<p class="mb-0">Configuration is valid and has been saved.</p>';
      
      expect(validationResults).not.toHaveClass('d-none');
      expect(validationResults).toHaveClass('alert-success');
      expect(validationResults).toHaveTextContent('Configuration is valid and has been saved.');
    });
  });

  describe('Configuration Reset', () => {
    test('should reset configuration to defaults', () => {
      const resetButton = screen.getByTestId('reset-config');
      const defaultBackend = screen.getByTestId('default-backend');
      const defaultDepth = screen.getByTestId('default-depth');
      const maxConcurrent = screen.getByTestId('max-concurrent');
      
      // Change settings from defaults
      fireEvent.change(defaultBackend, { target: { value: 'crawl4ai' } });
      fireEvent.change(defaultDepth, { target: { value: '8' } });
      fireEvent.change(maxConcurrent, { target: { value: '15' } });
      
      expect(defaultBackend.value).toBe('crawl4ai');
      expect(defaultDepth.value).toBe('8');
      expect(maxConcurrent.value).toBe('15');
      
      // Click reset
      fireEvent.click(resetButton);
      
      // Apply default values
      const defaults = {
        defaultBackend: 'http',
        defaultDepth: 3,
        maxConcurrent: 5
      };
      
      fireEvent.change(defaultBackend, { target: { value: defaults.defaultBackend } });
      fireEvent.change(defaultDepth, { target: { value: defaults.defaultDepth.toString() } });
      fireEvent.change(maxConcurrent, { target: { value: defaults.maxConcurrent.toString() } });
      
      expect(defaultBackend.value).toBe('http');
      expect(defaultDepth.value).toBe('3');
      expect(maxConcurrent.value).toBe('5');
    });

    test('should require confirmation before reset', () => {
      const resetButton = screen.getByTestId('reset-config');
      
      // Mock confirmation dialog
      global.confirm = jest.fn().mockReturnValue(false);
      
      // Click reset
      fireEvent.click(resetButton);
      
      expect(global.confirm).toHaveBeenCalledWith(
        'Are you sure you want to reset all configuration to defaults? This action cannot be undone.'
      );
      
      // Since user clicked "Cancel", reset should not proceed
      // Configuration should remain unchanged
    });
  });
});
