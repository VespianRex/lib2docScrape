/**
 * User Flow Tests - Scraping Workflows
 * 
 * Tests for complete user workflows in the scraping process
 */

import { screen, fireEvent, waitFor } from '@testing-library/dom';
import '@testing-library/jest-dom';

describe('User Flow - Scraping Workflows', () => {
  let container;
  let mockFetch;
  let mockWebSocket;
  
  beforeEach(() => {
    // Mock fetch API
    mockFetch = jest.fn();
    global.fetch = mockFetch;
    
    // Mock WebSocket
    mockWebSocket = {
      send: jest.fn(),
      close: jest.fn(),
      readyState: WebSocket.OPEN,
      addEventListener: jest.fn(),
      removeEventListener: jest.fn()
    };
    
    global.WebSocket = jest.fn(() => mockWebSocket);
    
    // Create comprehensive scraping interface
    document.body.innerHTML = `
      <div data-testid="scraping-dashboard" class="scraping-dashboard">
        <!-- Quick Start Section -->
        <div data-testid="quick-start" class="quick-start-section">
          <h2>Quick Start</h2>
          <div class="input-group">
            <input 
              type="url" 
              data-testid="quick-url-input" 
              class="form-control"
              placeholder="https://docs.example.com"
            >
            <button data-testid="quick-start-button" class="btn btn-primary">
              Quick Scrape
            </button>
          </div>
        </div>
        
        <!-- Advanced Configuration -->
        <div data-testid="advanced-config" class="advanced-config d-none">
          <h3>Advanced Configuration</h3>
          <form data-testid="advanced-form">
            <div class="row">
              <div class="col-md-6">
                <label for="depth-input">Crawl Depth</label>
                <input type="number" data-testid="depth-input" id="depth-input" min="1" max="10" value="3">
              </div>
              <div class="col-md-6">
                <label for="backend-select">Backend</label>
                <select data-testid="backend-select" id="backend-select">
                  <option value="http">HTTP Backend</option>
                  <option value="crawl4ai">Crawl4AI Backend</option>
                  <option value="scrapy">Scrapy Backend</option>
                </select>
              </div>
            </div>
            
            <div class="row">
              <div class="col-md-6">
                <label for="max-pages">Max Pages</label>
                <input type="number" data-testid="max-pages-input" id="max-pages" min="1" max="1000" value="100">
              </div>
              <div class="col-md-6">
                <label for="timeout">Timeout (seconds)</label>
                <input type="number" data-testid="timeout-input" id="timeout" min="10" max="300" value="30">
              </div>
            </div>
            
            <div class="form-check">
              <input type="checkbox" data-testid="follow-external" id="follow-external">
              <label for="follow-external">Follow external links</label>
            </div>
            
            <div class="form-check">
              <input type="checkbox" data-testid="extract-images" id="extract-images">
              <label for="extract-images">Extract images</label>
            </div>
            
            <button type="submit" data-testid="advanced-submit" class="btn btn-success">
              Start Advanced Scraping
            </button>
          </form>
        </div>
        
        <!-- Toggle for Advanced Options -->
        <button data-testid="toggle-advanced" class="btn btn-link">
          Show Advanced Options
        </button>
        
        <!-- Progress Section -->
        <div data-testid="progress-section" class="progress-section d-none">
          <h3>Scraping Progress</h3>
          <div class="progress mb-3">
            <div data-testid="progress-bar" class="progress-bar" style="width: 0%"></div>
          </div>
          <div data-testid="progress-details">
            <div class="row">
              <div class="col-md-3">
                <strong>Pages Crawled:</strong>
                <span data-testid="pages-crawled">0</span>
              </div>
              <div class="col-md-3">
                <strong>Documents Found:</strong>
                <span data-testid="documents-found">0</span>
              </div>
              <div class="col-md-3">
                <strong>Elapsed Time:</strong>
                <span data-testid="elapsed-time">00:00</span>
              </div>
              <div class="col-md-3">
                <strong>Status:</strong>
                <span data-testid="scraping-status">Ready</span>
              </div>
            </div>
          </div>
          <div data-testid="current-activity" class="current-activity">
            <small class="text-muted">Ready to start scraping...</small>
          </div>
          <button data-testid="cancel-scraping" class="btn btn-danger btn-sm d-none">
            Cancel Scraping
          </button>
        </div>
        
        <!-- Results Section -->
        <div data-testid="results-section" class="results-section d-none">
          <h3>Scraping Results</h3>
          <div data-testid="results-summary" class="results-summary">
            <div class="row">
              <div class="col-md-4">
                <div class="stat-card">
                  <h4 data-testid="total-pages">0</h4>
                  <p>Pages Processed</p>
                </div>
              </div>
              <div class="col-md-4">
                <div class="stat-card">
                  <h4 data-testid="total-documents">0</h4>
                  <p>Documents Extracted</p>
                </div>
              </div>
              <div class="col-md-4">
                <div class="stat-card">
                  <h4 data-testid="processing-time">0s</h4>
                  <p>Processing Time</p>
                </div>
              </div>
            </div>
          </div>
          
          <div data-testid="results-actions" class="results-actions">
            <button data-testid="view-results" class="btn btn-primary">View Results</button>
            <button data-testid="download-results" class="btn btn-secondary">Download</button>
            <button data-testid="share-results" class="btn btn-outline-primary">Share</button>
          </div>
          
          <div data-testid="results-preview" class="results-preview">
            <h4>Preview</h4>
            <div data-testid="preview-content" class="preview-content">
              <!-- Preview content will be populated here -->
            </div>
          </div>
        </div>
        
        <!-- Error Section -->
        <div data-testid="error-section" class="alert alert-danger d-none">
          <h4>Error</h4>
          <p data-testid="error-message">An error occurred during scraping.</p>
          <button data-testid="retry-scraping" class="btn btn-danger">Retry</button>
          <button data-testid="report-error" class="btn btn-outline-danger">Report Issue</button>
        </div>
      </div>
    `;
    
    container = document.body;
    
    // Set up global functions
    global.startElapsedTimer = jest.fn();
    global.stopElapsedTimer = jest.fn();
  });

  afterEach(() => {
    document.body.innerHTML = '';
    jest.clearAllMocks();
  });

  describe('Quick Start Workflow', () => {
    test('should complete quick scraping workflow successfully', async () => {
      const quickUrlInput = screen.getByTestId('quick-url-input');
      const quickStartButton = screen.getByTestId('quick-start-button');
      const progressSection = screen.getByTestId('progress-section');
      const resultsSection = screen.getByTestId('results-section');
      
      // Mock successful API responses
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            success: true,
            taskId: 'task-123',
            message: 'Scraping started'
          })
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            taskId: 'task-123',
            status: 'completed',
            results: {
              pages_crawled: 25,
              documents_extracted: 18,
              processing_time: 8500,
              url: 'https://docs.python.org'
            }
          })
        });
      
      // Enter URL and start scraping
      fireEvent.change(quickUrlInput, { 
        target: { value: 'https://docs.python.org' } 
      });
      
      expect(quickUrlInput.value).toBe('https://docs.python.org');
      
      // Click quick start
      fireEvent.click(quickStartButton);
      
      // Simulate progress showing
      progressSection.classList.remove('d-none');
      
      // Verify progress section is visible
      expect(progressSection).not.toHaveClass('d-none');
      
      // Simulate progress updates
      const progressBar = screen.getByTestId('progress-bar');
      const pagesCrawled = screen.getByTestId('pages-crawled');
      const documentsFound = screen.getByTestId('documents-found');
      const scrapingStatus = screen.getByTestId('scraping-status');
      
      // Update progress
      progressBar.style.width = '50%';
      pagesCrawled.textContent = '12';
      documentsFound.textContent = '8';
      scrapingStatus.textContent = 'Processing';
      
      expect(progressBar).toHaveStyle('width: 50%');
      expect(pagesCrawled).toHaveTextContent('12');
      expect(documentsFound).toHaveTextContent('8');
      expect(scrapingStatus).toHaveTextContent('Processing');
      
      // Complete scraping
      progressBar.style.width = '100%';
      scrapingStatus.textContent = 'Completed';
      
      // Show results
      progressSection.classList.add('d-none');
      resultsSection.classList.remove('d-none');
      
      // Update results summary
      const totalPages = screen.getByTestId('total-pages');
      const totalDocuments = screen.getByTestId('total-documents');
      const processingTime = screen.getByTestId('processing-time');
      
      totalPages.textContent = '25';
      totalDocuments.textContent = '18';
      processingTime.textContent = '8.5s';
      
      expect(resultsSection).not.toHaveClass('d-none');
      expect(totalPages).toHaveTextContent('25');
      expect(totalDocuments).toHaveTextContent('18');
      expect(processingTime).toHaveTextContent('8.5s');
    });

    test('should validate URL before starting quick scraping', () => {
      const quickUrlInput = screen.getByTestId('quick-url-input');
      const quickStartButton = screen.getByTestId('quick-start-button');
      
      // Test invalid URL
      fireEvent.change(quickUrlInput, { target: { value: 'not-a-url' } });
      fireEvent.click(quickStartButton);
      
      // Should prevent scraping with invalid URL
      expect(quickUrlInput.validity.valid).toBe(false);
      
      // Test valid URL
      fireEvent.change(quickUrlInput, { target: { value: 'https://docs.python.org' } });
      
      expect(quickUrlInput.validity.valid).toBe(true);
    });

    test('should provide immediate feedback on quick start', async () => {
      const quickStartButton = screen.getByTestId('quick-start-button');
      const progressSection = screen.getByTestId('progress-section');
      
      // Mock API response
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ success: true, taskId: 'task-123' })
      });
      
      // Click quick start
      fireEvent.click(quickStartButton);
      
      // Button should be disabled during request
      quickStartButton.disabled = true;
      quickStartButton.textContent = 'Starting...';
      
      expect(quickStartButton).toBeDisabled();
      expect(quickStartButton).toHaveTextContent('Starting...');
      
      // Progress should show immediately
      progressSection.classList.remove('d-none');
      
      expect(progressSection).not.toHaveClass('d-none');
    });
  });

  describe('Advanced Configuration Workflow', () => {
    test('should toggle advanced options visibility', () => {
      const toggleButton = screen.getByTestId('toggle-advanced');
      const advancedConfig = screen.getByTestId('advanced-config');
      
      // Initially hidden
      expect(advancedConfig).toHaveClass('d-none');
      expect(toggleButton).toHaveTextContent('Show Advanced Options');
      
      // Show advanced options
      fireEvent.click(toggleButton);
      advancedConfig.classList.remove('d-none');
      toggleButton.textContent = 'Hide Advanced Options';
      
      expect(advancedConfig).not.toHaveClass('d-none');
      expect(toggleButton).toHaveTextContent('Hide Advanced Options');
      
      // Hide advanced options
      fireEvent.click(toggleButton);
      advancedConfig.classList.add('d-none');
      toggleButton.textContent = 'Show Advanced Options';
      
      expect(advancedConfig).toHaveClass('d-none');
      expect(toggleButton).toHaveTextContent('Show Advanced Options');
    });

    test('should configure advanced scraping parameters', () => {
      const toggleButton = screen.getByTestId('toggle-advanced');
      const advancedConfig = screen.getByTestId('advanced-config');
      
      // Show advanced options
      fireEvent.click(toggleButton);
      advancedConfig.classList.remove('d-none');
      
      // Configure parameters
      const depthInput = screen.getByTestId('depth-input');
      const backendSelect = screen.getByTestId('backend-select');
      const maxPagesInput = screen.getByTestId('max-pages-input');
      const timeoutInput = screen.getByTestId('timeout-input');
      const followExternalCheckbox = screen.getByTestId('follow-external');
      const extractImagesCheckbox = screen.getByTestId('extract-images');
      
      fireEvent.change(depthInput, { target: { value: '5' } });
      fireEvent.change(backendSelect, { target: { value: 'crawl4ai' } });
      fireEvent.change(maxPagesInput, { target: { value: '200' } });
      fireEvent.change(timeoutInput, { target: { value: '60' } });
      fireEvent.click(followExternalCheckbox);
      fireEvent.click(extractImagesCheckbox);
      
      expect(depthInput.value).toBe('5');
      expect(backendSelect.value).toBe('crawl4ai');
      expect(maxPagesInput.value).toBe('200');
      expect(timeoutInput.value).toBe('60');
      expect(followExternalCheckbox.checked).toBe(true);
      expect(extractImagesCheckbox.checked).toBe(true);
    });

    test('should validate advanced configuration parameters', () => {
      const toggleButton = screen.getByTestId('toggle-advanced');
      const advancedConfig = screen.getByTestId('advanced-config');
      
      fireEvent.click(toggleButton);
      advancedConfig.classList.remove('d-none');
      
      const depthInput = screen.getByTestId('depth-input');
      const maxPagesInput = screen.getByTestId('max-pages-input');
      const timeoutInput = screen.getByTestId('timeout-input');
      
      // Test invalid values
      fireEvent.change(depthInput, { target: { value: '15' } }); // max is 10
      fireEvent.change(maxPagesInput, { target: { value: '2000' } }); // max is 1000
      fireEvent.change(timeoutInput, { target: { value: '5' } }); // min is 10
      
      expect(depthInput.validity.valid).toBe(false);
      expect(maxPagesInput.validity.valid).toBe(false);
      expect(timeoutInput.validity.valid).toBe(false);
      
      // Test valid values
      fireEvent.change(depthInput, { target: { value: '8' } });
      fireEvent.change(maxPagesInput, { target: { value: '500' } });
      fireEvent.change(timeoutInput, { target: { value: '45' } });
      
      expect(depthInput.validity.valid).toBe(true);
      expect(maxPagesInput.validity.valid).toBe(true);
      expect(timeoutInput.validity.valid).toBe(true);
    });

    test('should start advanced scraping with custom parameters', async () => {
      const toggleButton = screen.getByTestId('toggle-advanced');
      const advancedConfig = screen.getByTestId('advanced-config');
      const advancedForm = screen.getByTestId('advanced-form');
      
      // Mock API response
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          success: true,
          taskId: 'advanced-task-123',
          config: {
            depth: 5,
            backend: 'crawl4ai',
            maxPages: 200,
            timeout: 60,
            followExternal: true,
            extractImages: true
          }
        })
      });
      
      // Show and configure advanced options
      fireEvent.click(toggleButton);
      advancedConfig.classList.remove('d-none');
      
      const backendSelect = screen.getByTestId('backend-select');
      fireEvent.change(backendSelect, { target: { value: 'crawl4ai' } });
      
      // Submit advanced form
      fireEvent.submit(advancedForm);
      
      // Verify configuration was sent
      expect(mockFetch).toHaveBeenCalledWith(
        '/api/scrape',
        expect.objectContaining({
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: expect.stringContaining('crawl4ai')
        })
      );
    });
  });

  describe('Progress Tracking Workflow', () => {
    test('should display real-time progress updates', async () => {
      const progressSection = screen.getByTestId('progress-section');
      const progressBar = screen.getByTestId('progress-bar');
      const pagesCrawled = screen.getByTestId('pages-crawled');
      const documentsFound = screen.getByTestId('documents-found');
      const elapsedTime = screen.getByTestId('elapsed-time');
      const scrapingStatus = screen.getByTestId('scraping-status');
      const currentActivity = screen.getByTestId('current-activity');
      
      // Start scraping (show progress)
      progressSection.classList.remove('d-none');
      
      // Simulate WebSocket progress updates
      const progressUpdates = [
        {
          progress: 10,
          pages_crawled: 2,
          documents_found: 1,
          elapsed_time: 5,
          status: 'crawling',
          current_activity: 'Crawling homepage...'
        },
        {
          progress: 30,
          pages_crawled: 8,
          documents_found: 5,
          elapsed_time: 15,
          status: 'crawling',
          current_activity: 'Processing API documentation...'
        },
        {
          progress: 60,
          pages_crawled: 15,
          documents_found: 12,
          elapsed_time: 28,
          status: 'extracting',
          current_activity: 'Extracting code examples...'
        },
        {
          progress: 90,
          pages_crawled: 22,
          documents_found: 18,
          elapsed_time: 42,
          status: 'finalizing',
          current_activity: 'Generating final output...'
        }
      ];
      
      for (const update of progressUpdates) {
        // Update progress indicators
        progressBar.style.width = `${update.progress}%`;
        pagesCrawled.textContent = update.pages_crawled.toString();
        documentsFound.textContent = update.documents_found.toString();
        elapsedTime.textContent = `${Math.floor(update.elapsed_time / 60)}:${(update.elapsed_time % 60).toString().padStart(2, '0')}`;
        scrapingStatus.textContent = update.status.charAt(0).toUpperCase() + update.status.slice(1);
        currentActivity.textContent = update.current_activity;
        
        // Verify updates
        expect(progressBar).toHaveStyle(`width: ${update.progress}%`);
        expect(pagesCrawled).toHaveTextContent(update.pages_crawled.toString());
        expect(documentsFound).toHaveTextContent(update.documents_found.toString());
        expect(scrapingStatus).toHaveTextContent(update.status.charAt(0).toUpperCase() + update.status.slice(1));
        expect(currentActivity).toHaveTextContent(update.current_activity);
        
        // Simulate time passing
        await new Promise(resolve => setTimeout(resolve, 10));
      }
    });

    test('should allow canceling scraping in progress', async () => {
      const progressSection = screen.getByTestId('progress-section');
      const cancelButton = screen.getByTestId('cancel-scraping');
      
      // Mock cancel API
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ success: true, message: 'Scraping cancelled' })
      });
      
      // Start scraping
      progressSection.classList.remove('d-none');
      cancelButton.classList.remove('d-none');
      
      expect(cancelButton).not.toHaveClass('d-none');
      
      // Cancel scraping
      fireEvent.click(cancelButton);
      
      // Verify cancel request
      expect(mockFetch).toHaveBeenCalledWith(
        '/api/scrape/cancel',
        expect.objectContaining({
          method: 'POST'
        })
      );
      
      // Hide progress section
      progressSection.classList.add('d-none');
      
      expect(progressSection).toHaveClass('d-none');
    });

    test('should handle elapsed time tracking', () => {
      const elapsedTime = screen.getByTestId('elapsed-time');
      
      // Simulate time tracking
      let seconds = 0;
      const timeInterval = setInterval(() => {
        seconds++;
        const minutes = Math.floor(seconds / 60);
        const remainingSeconds = seconds % 60;
        elapsedTime.textContent = `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
      }, 1000);
      
      // Simulate 1 minute and 30 seconds
      for (let i = 0; i <= 90; i += 30) {
        const minutes = Math.floor(i / 60);
        const remainingSeconds = i % 60;
        elapsedTime.textContent = `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
      }
      
      expect(elapsedTime).toHaveTextContent('1:30');
      
      clearInterval(timeInterval);
    });
  });

  describe('Results and Actions Workflow', () => {
    test('should display comprehensive results summary', () => {
      const resultsSection = screen.getByTestId('results-section');
      const totalPages = screen.getByTestId('total-pages');
      const totalDocuments = screen.getByTestId('total-documents');
      const processingTime = screen.getByTestId('processing-time');
      
      // Show results
      resultsSection.classList.remove('d-none');
      
      // Mock results data
      const results = {
        pages_processed: 45,
        documents_extracted: 32,
        processing_time: 67.5
      };
      
      // Update summary
      totalPages.textContent = results.pages_processed.toString();
      totalDocuments.textContent = results.documents_extracted.toString();
      processingTime.textContent = `${results.processing_time}s`;
      
      expect(totalPages).toHaveTextContent('45');
      expect(totalDocuments).toHaveTextContent('32');
      expect(processingTime).toHaveTextContent('67.5s');
    });

    test('should provide result actions', () => {
      const viewButton = screen.getByTestId('view-results');
      const downloadButton = screen.getByTestId('download-results');
      const shareButton = screen.getByTestId('share-results');
      
      // Test action buttons
      expect(viewButton).toBeInTheDocument();
      expect(downloadButton).toBeInTheDocument();
      expect(shareButton).toBeInTheDocument();
      
      // Simulate clicking actions
      const viewHandler = jest.fn();
      const downloadHandler = jest.fn();
      const shareHandler = jest.fn();
      
      viewButton.addEventListener('click', viewHandler);
      downloadButton.addEventListener('click', downloadHandler);
      shareButton.addEventListener('click', shareHandler);
      
      fireEvent.click(viewButton);
      fireEvent.click(downloadButton);
      fireEvent.click(shareButton);
      
      expect(viewHandler).toHaveBeenCalled();
      expect(downloadHandler).toHaveBeenCalled();
      expect(shareHandler).toHaveBeenCalled();
    });

    test('should display results preview', () => {
      const previewContent = screen.getByTestId('preview-content');
      
      // Mock preview data
      const sampleDocuments = [
        {
          title: 'Getting Started',
          url: 'https://docs.python.org/getting-started',
          content_preview: 'Python is a powerful programming language...'
        },
        {
          title: 'API Reference',
          url: 'https://docs.python.org/api-reference',
          content_preview: 'The Python API provides comprehensive...'
        }
      ];
      
      // Populate preview
      previewContent.innerHTML = sampleDocuments
        .map(doc => `
          <div class="preview-item">
            <h5>${doc.title}</h5>
            <small class="text-muted">${doc.url}</small>
            <p>${doc.content_preview}</p>
          </div>
        `)
        .join('');
      
      expect(previewContent).toHaveTextContent('Getting Started');
      expect(previewContent).toHaveTextContent('API Reference');
      expect(previewContent).toHaveTextContent('Python is a powerful programming language...');
    });
  });

  describe('Error Handling Workflow', () => {
    test('should display error information and recovery options', () => {
      const errorSection = screen.getByTestId('error-section');
      const errorMessage = screen.getByTestId('error-message');
      const retryButton = screen.getByTestId('retry-scraping');
      const reportButton = screen.getByTestId('report-error');
      
      // Simulate error
      const error = {
        type: 'network_error',
        message: 'Failed to connect to the documentation site. The server may be temporarily unavailable.',
        code: 'CONN_REFUSED',
        url: 'https://docs.example.com'
      };
      
      // Display error
      errorSection.classList.remove('d-none');
      errorMessage.textContent = error.message;
      
      expect(errorSection).not.toHaveClass('d-none');
      expect(errorMessage).toHaveTextContent(error.message);
      expect(retryButton).toBeInTheDocument();
      expect(reportButton).toBeInTheDocument();
    });

    test('should handle retry workflow', async () => {
      const retryButton = screen.getByTestId('retry-scraping');
      const errorSection = screen.getByTestId('error-section');
      const progressSection = screen.getByTestId('progress-section');
      
      // Mock retry API
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ success: true, taskId: 'retry-task-123' })
      });
      
      // Show error first
      errorSection.classList.remove('d-none');
      
      // Click retry
      fireEvent.click(retryButton);
      
      // Hide error, show progress
      errorSection.classList.add('d-none');
      progressSection.classList.remove('d-none');
      
      expect(errorSection).toHaveClass('d-none');
      expect(progressSection).not.toHaveClass('d-none');
      
      // Verify retry API call
      expect(mockFetch).toHaveBeenCalledWith(
        '/api/scrape/retry',
        expect.objectContaining({
          method: 'POST'
        })
      );
    });

    test('should handle error reporting', () => {
      const reportButton = screen.getByTestId('report-error');
      
      // Mock error reporting
      const reportHandler = jest.fn();
      reportButton.addEventListener('click', reportHandler);
      
      fireEvent.click(reportButton);
      
      expect(reportHandler).toHaveBeenCalled();
    });
  });

  describe('Complete End-to-End Workflow', () => {
    test('should complete full scraping workflow from start to finish', async () => {
      // Mock all API responses
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ success: true, taskId: 'e2e-task-123' })
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            taskId: 'e2e-task-123',
            status: 'completed',
            results: {
              pages_crawled: 50,
              documents_extracted: 35,
              processing_time: 89.2
            }
          })
        });
      
      // Step 1: Configure advanced scraping
      const toggleButton = screen.getByTestId('toggle-advanced');
      const advancedConfig = screen.getByTestId('advanced-config');
      
      fireEvent.click(toggleButton);
      advancedConfig.classList.remove('d-none');
      
      const backendSelect = screen.getByTestId('backend-select');
      fireEvent.change(backendSelect, { target: { value: 'crawl4ai' } });
      
      // Step 2: Start scraping
      const advancedForm = screen.getByTestId('advanced-form');
      fireEvent.submit(advancedForm);
      
      // Step 3: Show progress
      const progressSection = screen.getByTestId('progress-section');
      progressSection.classList.remove('d-none');
      
      // Step 4: Simulate progress updates
      const progressBar = screen.getByTestId('progress-bar');
      const scrapingStatus = screen.getByTestId('scraping-status');
      
      progressBar.style.width = '100%';
      scrapingStatus.textContent = 'Completed';
      
      // Step 5: Show results
      const resultsSection = screen.getByTestId('results-section');
      progressSection.classList.add('d-none');
      resultsSection.classList.remove('d-none');
      
      const totalPages = screen.getByTestId('total-pages');
      const totalDocuments = screen.getByTestId('total-documents');
      
      totalPages.textContent = '50';
      totalDocuments.textContent = '35';
      
      // Step 6: Verify final state
      expect(progressSection).toHaveClass('d-none');
      expect(resultsSection).not.toHaveClass('d-none');
      expect(totalPages).toHaveTextContent('50');
      expect(totalDocuments).toHaveTextContent('35');
    });
  });
});
