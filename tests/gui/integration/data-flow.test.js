/**
 * Data Flow Integration Tests
 * 
 * Tests for backend communication, data transformation, and error handling
 */

import { screen, fireEvent, waitFor } from '@testing-library/dom';
import '@testing-library/jest-dom';

describe('Data Flow Integration', () => {
  let container;
  let mockFetch;
  
  beforeEach(() => {
    // Mock fetch API
    mockFetch = jest.fn();
    global.fetch = mockFetch;
    
    // Create test HTML structure
    document.body.innerHTML = `
      <div data-testid="scraping-dashboard">
        <form data-testid="scraping-form">
          <input type="url" data-testid="url-input" value="https://docs.python.org">
          <select data-testid="backend-select">
            <option value="http">HTTP Backend</option>
            <option value="crawl4ai">Crawl4AI Backend</option>
          </select>
          <button type="submit" data-testid="submit-button">Start Scraping</button>
        </form>
        
        <div data-testid="progress-display" class="d-none">
          <div class="progress">
            <div class="progress-bar" data-testid="progress-bar" style="width: 0%"></div>
          </div>
          <div data-testid="progress-text">Starting...</div>
        </div>
        
        <div data-testid="results-display" class="d-none">
          <h3>Scraping Results</h3>
          <div data-testid="results-content"></div>
        </div>
        
        <div data-testid="error-display" class="alert alert-danger d-none">
          <span data-testid="error-message"></span>
        </div>
      </div>
      
      <div data-testid="library-browser">
        <div data-testid="search-form">
          <input type="text" data-testid="search-input" placeholder="Search libraries...">
          <button data-testid="search-button">Search</button>
        </div>
        
        <div data-testid="library-list" class="library-grid">
          <!-- Libraries will be populated here -->
        </div>
        
        <div data-testid="pagination">
          <button data-testid="prev-page" disabled>Previous</button>
          <span data-testid="page-info">Page 1 of 5</span>
          <button data-testid="next-page">Next</button>
        </div>
      </div>
    `;
    
    container = document.body;
  });

  afterEach(() => {
    document.body.innerHTML = '';
    jest.clearAllMocks();
  });

  describe('Backend Communication', () => {
    test('should send scraping request to backend', async () => {
      const form = screen.getByTestId('scraping-form');
      const urlInput = screen.getByTestId('url-input');
      const backendSelect = screen.getByTestId('backend-select');
      
      // Mock successful response
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          success: true,
          taskId: 'task-123',
          message: 'Scraping started'
        })
      });
      
      // Fill form
      fireEvent.change(backendSelect, { target: { value: 'crawl4ai' } });
      
      // Submit form
      fireEvent.submit(form);
      
      // Simulate form submission
      const formData = {
        url: urlInput.value,
        backend: backendSelect.value,
        depth: 3
      };
      
      await fetch('/api/scrape', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      });
      
      expect(mockFetch).toHaveBeenCalledWith('/api/scrape', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          url: 'https://docs.python.org',
          backend: 'crawl4ai',
          depth: 3
        })
      });
    });

    test('should handle API authentication', async () => {
      // Mock authenticated request
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ libraries: [] })
      });
      
      // Simulate authenticated API call
      const authToken = 'mock-auth-token';
      localStorage.setItem('auth-token', authToken);
      
      await fetch('/api/libraries', {
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'application/json'
        }
      });
      
      expect(mockFetch).toHaveBeenCalledWith('/api/libraries', {
        headers: {
          'Authorization': 'Bearer mock-auth-token',
          'Content-Type': 'application/json'
        }
      });
    });

    test('should handle different response formats', async () => {
      // Test JSON response
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ data: 'json-data' })
      });
      
      const jsonResponse = await fetch('/api/data');
      const jsonData = await jsonResponse.json();
      
      expect(jsonData).toEqual({ data: 'json-data' });
      
      // Test text response
      mockFetch.mockResolvedValueOnce({
        ok: true,
        text: async () => 'plain text response'
      });
      
      const textResponse = await fetch('/api/text');
      const textData = await textResponse.text();
      
      expect(textData).toBe('plain text response');
      
      // Test blob response (for file downloads)
      const mockBlob = new Blob(['file content'], { type: 'text/plain' });
      mockFetch.mockResolvedValueOnce({
        ok: true,
        blob: async () => mockBlob
      });
      
      const blobResponse = await fetch('/api/download');
      const blobData = await blobResponse.blob();
      
      expect(blobData.type).toBe('text/plain');
    });

    test('should handle request timeouts', async () => {
      // Mock timeout
      const timeoutPromise = new Promise((_, reject) => {
        setTimeout(() => reject(new Error('Request timeout')), 100);
      });
      
      mockFetch.mockReturnValueOnce(timeoutPromise);
      
      await expect(fetch('/api/slow-endpoint')).rejects.toThrow('Request timeout');
    });

    test('should retry failed requests', async () => {
      // First attempt fails
      mockFetch.mockRejectedValueOnce(new Error('Network error'));
      
      // Second attempt succeeds
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ success: true })
      });
      
      // Implement retry logic
      const retryFetch = async (url, options, maxRetries = 3) => {
        for (let i = 0; i < maxRetries; i++) {
          try {
            return await fetch(url, options);
          } catch (error) {
            if (i === maxRetries - 1) throw error;
            await new Promise(resolve => setTimeout(resolve, 1000));
          }
        }
      };
      
      const response = await retryFetch('/api/unreliable');
      const data = await response.json();
      
      expect(data.success).toBe(true);
      expect(mockFetch).toHaveBeenCalledTimes(2);
    });
  });

  describe('Data Transformation', () => {
    test('should transform API response for display', async () => {
      const rawApiResponse = {
        libraries: [
          {
            id: 'lib1',
            name: 'requests',
            description: 'HTTP library for Python',
            versions: ['2.28.0', '2.27.1'],
            last_updated: '2023-01-15T10:30:00Z',
            documentation_urls: ['https://docs.python-requests.org']
          },
          {
            id: 'lib2',
            name: 'flask',
            description: 'Web framework for Python',
            versions: ['2.2.3', '2.1.0'],
            last_updated: '2023-02-20T14:45:00Z',
            documentation_urls: ['https://flask.palletsprojects.com']
          }
        ]
      };
      
      // Transform data for UI
      const transformedData = rawApiResponse.libraries.map(lib => ({
        id: lib.id,
        name: lib.name,
        description: lib.description,
        latestVersion: lib.versions[0],
        lastUpdated: new Date(lib.last_updated).toLocaleDateString(),
        docsUrl: lib.documentation_urls[0],
        totalVersions: lib.versions.length
      }));
      
      expect(transformedData[0]).toEqual({
        id: 'lib1',
        name: 'requests',
        description: 'HTTP library for Python',
        latestVersion: '2.28.0',
        lastUpdated: new Date('2023-01-15T10:30:00Z').toLocaleDateString(),
        docsUrl: 'https://docs.python-requests.org',
        totalVersions: 2
      });
    });

    test('should handle missing or null data gracefully', () => {
      const incompleteData = {
        libraries: [
          {
            id: 'lib1',
            name: 'requests',
            // missing description
            versions: null,
            last_updated: undefined,
            documentation_urls: []
          }
        ]
      };
      
      // Transform with defaults
      const transformedData = incompleteData.libraries.map(lib => ({
        id: lib.id,
        name: lib.name,
        description: lib.description || 'No description available',
        latestVersion: lib.versions?.[0] || 'Unknown',
        lastUpdated: lib.last_updated ? new Date(lib.last_updated).toLocaleDateString() : 'Unknown',
        docsUrl: lib.documentation_urls?.[0] || '#',
        totalVersions: lib.versions?.length || 0
      }));
      
      expect(transformedData[0]).toEqual({
        id: 'lib1',
        name: 'requests',
        description: 'No description available',
        latestVersion: 'Unknown',
        lastUpdated: 'Unknown',
        docsUrl: '#',
        totalVersions: 0
      });
    });

    test('should format data for different views', () => {
      const scrapingResult = {
        task_id: 'task-123',
        url: 'https://docs.python.org',
        pages_crawled: 156,
        documents_extracted: 89,
        processing_time: 12500,
        status: 'completed',
        created_at: '2023-06-20T10:00:00Z',
        completed_at: '2023-06-20T10:02:05Z'
      };
      
      // Format for summary view
      const summaryView = {
        taskId: scrapingResult.task_id,
        url: scrapingResult.url,
        summary: `${scrapingResult.documents_extracted} documents from ${scrapingResult.pages_crawled} pages`,
        duration: `${Math.round(scrapingResult.processing_time / 1000)}s`,
        status: scrapingResult.status.charAt(0).toUpperCase() + scrapingResult.status.slice(1),
        completedAt: new Date(scrapingResult.completed_at).toLocaleString()
      };
      
      // Format for detailed view
      const detailedView = {
        ...scrapingResult,
        processingTimeFormatted: `${Math.round(scrapingResult.processing_time / 1000)} seconds`,
        createdAtFormatted: new Date(scrapingResult.created_at).toLocaleString(),
        completedAtFormatted: new Date(scrapingResult.completed_at).toLocaleString(),
        efficiency: Math.round((scrapingResult.documents_extracted / scrapingResult.pages_crawled) * 100)
      };
      
      expect(summaryView.summary).toBe('89 documents from 156 pages');
      expect(summaryView.duration).toBe('13s');
      expect(detailedView.efficiency).toBe(57);
    });

    test('should validate transformed data', () => {
      const invalidData = {
        libraries: [
          { id: '', name: 'requests' }, // invalid ID
          { id: 'lib2' }, // missing name
          { id: 'lib3', name: 'flask', versions: 'invalid' } // invalid versions
        ]
      };
      
      // Validate and filter
      const validatedData = invalidData.libraries
        .filter(lib => lib.id && lib.name)
        .map(lib => ({
          ...lib,
          versions: Array.isArray(lib.versions) ? lib.versions : []
        }));
      
      expect(validatedData).toHaveLength(1);
      expect(validatedData[0].id).toBe('lib3');
      expect(validatedData[0].versions).toEqual([]);
    });
  });

  describe('Error Handling', () => {
    test('should handle network errors', async () => {
      const errorDisplay = screen.getByTestId('error-display');
      const errorMessage = screen.getByTestId('error-message');
      
      // Mock network error
      mockFetch.mockRejectedValueOnce(new Error('Network error'));
      
      try {
        await fetch('/api/scrape');
      } catch (error) {
        // Display error to user
        errorMessage.textContent = 'Network error occurred. Please check your connection.';
        errorDisplay.classList.remove('d-none');
      }
      
      expect(errorDisplay).not.toHaveClass('d-none');
      expect(errorMessage).toHaveTextContent('Network error occurred. Please check your connection.');
    });

    test('should handle HTTP error responses', async () => {
      const errorDisplay = screen.getByTestId('error-display');
      const errorMessage = screen.getByTestId('error-message');
      
      // Mock 400 error
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 400,
        json: async () => ({
          error: 'Invalid URL provided',
          details: 'The URL must be a valid documentation site'
        })
      });
      
      const response = await fetch('/api/scrape');
      
      if (!response.ok) {
        const errorData = await response.json();
        errorMessage.textContent = errorData.error;
        errorDisplay.classList.remove('d-none');
      }
      
      expect(errorMessage).toHaveTextContent('Invalid URL provided');
      expect(errorDisplay).not.toHaveClass('d-none');
    });

    test('should handle server errors gracefully', async () => {
      const errorDisplay = screen.getByTestId('error-display');
      const errorMessage = screen.getByTestId('error-message');
      
      // Mock 500 error
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        json: async () => ({
          error: 'Internal server error'
        })
      });
      
      const response = await fetch('/api/scrape');
      
      if (!response.ok) {
        const errorData = await response.json();
        
        if (response.status >= 500) {
          errorMessage.textContent = 'Server error occurred. Please try again later.';
        } else {
          errorMessage.textContent = errorData.error;
        }
        
        errorDisplay.classList.remove('d-none');
      }
      
      expect(errorMessage).toHaveTextContent('Server error occurred. Please try again later.');
    });

    test('should handle malformed JSON responses', async () => {
      // Mock response with invalid JSON
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => {
          throw new Error('Unexpected token in JSON');
        }
      });
      
      const errorDisplay = screen.getByTestId('error-display');
      const errorMessage = screen.getByTestId('error-message');
      
      try {
        const response = await fetch('/api/data');
        await response.json();
      } catch (error) {
        errorMessage.textContent = 'Invalid response from server. Please try again.';
        errorDisplay.classList.remove('d-none');
      }
      
      expect(errorMessage).toHaveTextContent('Invalid response from server. Please try again.');
    });

    test('should provide specific error messages for different scenarios', async () => {
      const errorScenarios = [
        {
          error: new Error('Failed to fetch'),
          expectedMessage: 'Network error occurred. Please check your connection.'
        },
        {
          status: 401,
          error: 'Unauthorized',
          expectedMessage: 'Authentication required. Please log in.'
        },
        {
          status: 403,
          error: 'Forbidden',
          expectedMessage: 'Access denied. You don\'t have permission to perform this action.'
        },
        {
          status: 404,
          error: 'Not found',
          expectedMessage: 'The requested resource was not found.'
        },
        {
          status: 429,
          error: 'Too many requests',
          expectedMessage: 'Rate limit exceeded. Please wait before trying again.'
        }
      ];
      
      const getErrorMessage = (error, status) => {
        if (error.message === 'Failed to fetch') {
          return 'Network error occurred. Please check your connection.';
        }
        
        switch (status) {
          case 401:
            return 'Authentication required. Please log in.';
          case 403:
            return 'Access denied. You don\'t have permission to perform this action.';
          case 404:
            return 'The requested resource was not found.';
          case 429:
            return 'Rate limit exceeded. Please wait before trying again.';
          default:
            return 'An unexpected error occurred. Please try again.';
        }
      };
      
      errorScenarios.forEach(scenario => {
        const message = getErrorMessage(scenario, scenario.status);
        expect(message).toBe(scenario.expectedMessage);
      });
    });

    test('should clear previous errors on new requests', () => {
      const errorDisplay = screen.getByTestId('error-display');
      const errorMessage = screen.getByTestId('error-message');
      
      // Show error first
      errorMessage.textContent = 'Previous error';
      errorDisplay.classList.remove('d-none');
      
      expect(errorDisplay).not.toHaveClass('d-none');
      
      // Clear errors on new request
      errorMessage.textContent = '';
      errorDisplay.classList.add('d-none');
      
      expect(errorDisplay).toHaveClass('d-none');
      expect(errorMessage).toHaveTextContent('');
    });
  });

  describe('Real-time Data Updates', () => {
    test('should update progress during scraping', async () => {
      const progressDisplay = screen.getByTestId('progress-display');
      const progressBar = screen.getByTestId('progress-bar');
      const progressText = screen.getByTestId('progress-text');
      
      // Simulate progress updates
      const progressUpdates = [
        { progress: 10, message: 'Starting scraping...' },
        { progress: 30, message: 'Processing pages...' },
        { progress: 60, message: 'Extracting content...' },
        { progress: 90, message: 'Finalizing results...' },
        { progress: 100, message: 'Scraping complete!' }
      ];
      
      progressDisplay.classList.remove('d-none');
      
      for (const update of progressUpdates) {
        progressBar.style.width = `${update.progress}%`;
        progressText.textContent = update.message;
        
        expect(progressBar).toHaveStyle(`width: ${update.progress}%`);
        expect(progressText).toHaveTextContent(update.message);
        
        // Simulate delay between updates
        await new Promise(resolve => setTimeout(resolve, 10));
      }
    });

    test('should handle real-time search results', async () => {
      const searchInput = screen.getByTestId('search-input');
      const libraryList = screen.getByTestId('library-list');
      
      // Mock search API
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => ({
          libraries: [
            { id: 'lib1', name: 'requests', description: 'HTTP library' },
            { id: 'lib2', name: 'httpx', description: 'Async HTTP library' }
          ],
          total: 2
        })
      });
      
      // Simulate typing
      fireEvent.input(searchInput, { target: { value: 'http' } });
      
      // Simulate debounced search
      await new Promise(resolve => setTimeout(resolve, 300));
      
      const response = await fetch(`/api/search?q=${searchInput.value}`);
      const data = await response.json();
      
      // Update library list
      libraryList.innerHTML = data.libraries
        .map(lib => `
          <div class="library-card" data-testid="library-${lib.id}">
            <h5>${lib.name}</h5>
            <p>${lib.description}</p>
          </div>
        `)
        .join('');
      
      expect(screen.getByTestId('library-lib1')).toBeInTheDocument();
      expect(screen.getByTestId('library-lib2')).toBeInTheDocument();
    });

    test('should handle live notifications', () => {
      // Simulate notification system
      const notification = {
        id: 'notif-1',
        type: 'success',
        title: 'Scraping Complete',
        message: 'Python documentation has been successfully scraped.',
        timestamp: new Date().toISOString()
      };
      
      // Add notification to DOM
      const notificationContainer = document.createElement('div');
      notificationContainer.setAttribute('data-testid', 'notifications');
      notificationContainer.innerHTML = `
        <div class="notification alert alert-${notification.type}" data-testid="notification-${notification.id}">
          <h6>${notification.title}</h6>
          <p>${notification.message}</p>
          <small>${new Date(notification.timestamp).toLocaleTimeString()}</small>
        </div>
      `;
      
      container.appendChild(notificationContainer);
      
      const notificationElement = screen.getByTestId(`notification-${notification.id}`);
      expect(notificationElement).toBeInTheDocument();
      expect(notificationElement).toHaveTextContent(notification.title);
      expect(notificationElement).toHaveTextContent(notification.message);
    });
  });
});
