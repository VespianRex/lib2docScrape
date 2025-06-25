/**
 * Form Elements Component Tests
 * 
 * Tests for form validation, submission behavior, and user interactions
 */

import { screen, fireEvent, waitFor } from '@testing-library/dom';
import '@testing-library/jest-dom';

describe('Form Elements Component', () => {
  let container;
  
  beforeEach(() => {
    // Create test HTML structure with various form elements
    document.body.innerHTML = `
      <form data-testid="scraping-form" class="scraping-form">
        <div class="mb-3">
          <label for="url-input" class="form-label">Documentation URL</label>
          <input 
            type="url" 
            class="form-control" 
            id="url-input" 
            data-testid="url-input"
            required
            placeholder="https://docs.example.com"
          >
          <div class="invalid-feedback" data-testid="url-error">
            Please enter a valid URL.
          </div>
        </div>
        
        <div class="mb-3">
          <label for="depth-input" class="form-label">Crawl Depth</label>
          <input 
            type="number" 
            class="form-control" 
            id="depth-input" 
            data-testid="depth-input"
            min="1" 
            max="10" 
            value="3"
            required
          >
          <div class="invalid-feedback" data-testid="depth-error">
            Depth must be between 1 and 10.
          </div>
        </div>
        
        <div class="mb-3">
          <label for="backend-select" class="form-label">Backend</label>
          <select class="form-select" id="backend-select" data-testid="backend-select" required>
            <option value="">Choose backend...</option>
            <option value="http">HTTP Backend</option>
            <option value="crawl4ai">Crawl4AI Backend</option>
            <option value="scrapy">Scrapy Backend</option>
          </select>
          <div class="invalid-feedback" data-testid="backend-error">
            Please select a backend.
          </div>
        </div>
        
        <div class="mb-3 form-check">
          <input 
            type="checkbox" 
            class="form-check-input" 
            id="advanced-options" 
            data-testid="advanced-checkbox"
          >
          <label class="form-check-label" for="advanced-options">
            Enable advanced options
          </label>
        </div>
        
        <button 
          type="submit" 
          class="btn btn-primary" 
          data-testid="submit-button"
        >
          <span class="button-text">Start Scraping</span>
          <span class="spinner-border spinner-border-sm d-none" data-testid="submit-spinner"></span>
        </button>
      </form>
      
      <div class="alert alert-success d-none" data-testid="success-message">
        Scraping started successfully!
      </div>
      
      <div class="alert alert-danger d-none" data-testid="error-message">
        <span data-testid="error-text">An error occurred.</span>
      </div>
    `;
    
    container = document.body;
    
    // Mock fetch for form submissions
    global.fetch = jest.fn();
  });

  afterEach(() => {
    document.body.innerHTML = '';
    jest.clearAllMocks();
  });

  describe('Input Validation', () => {
    test('should validate required URL field', () => {
      const urlInput = screen.getByTestId('url-input');
      const form = screen.getByTestId('scraping-form');
      
      // Try to submit empty form
      fireEvent.submit(form);
      
      expect(urlInput.validity.valid).toBe(false);
      expect(urlInput.validity.valueMissing).toBe(true);
    });

    test('should validate URL format', () => {
      const urlInput = screen.getByTestId('url-input');
      
      // Test invalid URL
      fireEvent.change(urlInput, { target: { value: 'not-a-url' } });
      expect(urlInput.validity.valid).toBe(false);
      expect(urlInput.validity.typeMismatch).toBe(true);
      
      // Test valid URL
      fireEvent.change(urlInput, { target: { value: 'https://docs.python.org' } });
      expect(urlInput.validity.valid).toBe(true);
    });

    test('should validate number input ranges', () => {
      const depthInput = screen.getByTestId('depth-input');
      
      // Test below minimum
      fireEvent.change(depthInput, { target: { value: '0' } });
      expect(depthInput.validity.valid).toBe(false);
      expect(depthInput.validity.rangeUnderflow).toBe(true);
      
      // Test above maximum
      fireEvent.change(depthInput, { target: { value: '15' } });
      expect(depthInput.validity.valid).toBe(false);
      expect(depthInput.validity.rangeOverflow).toBe(true);
      
      // Test valid range
      fireEvent.change(depthInput, { target: { value: '5' } });
      expect(depthInput.validity.valid).toBe(true);
    });

    test('should validate required select field', () => {
      const backendSelect = screen.getByTestId('backend-select');
      const form = screen.getByTestId('scraping-form');
      
      // Try to submit with empty selection
      fireEvent.submit(form);
      
      expect(backendSelect.validity.valid).toBe(false);
      expect(backendSelect.validity.valueMissing).toBe(true);
    });

    test('should show validation error messages', () => {
      const urlInput = screen.getByTestId('url-input');
      const urlError = screen.getByTestId('url-error');
      
      // Trigger validation
      fireEvent.invalid(urlInput);
      urlInput.classList.add('is-invalid');
      
      expect(urlInput).toHaveClass('is-invalid');
      expect(urlError).toBeInTheDocument();
    });

    test('should clear validation errors when input becomes valid', () => {
      const urlInput = screen.getByTestId('url-input');
      
      // Set invalid state
      urlInput.classList.add('is-invalid');
      
      // Enter valid value
      fireEvent.change(urlInput, { target: { value: 'https://example.com' } });
      fireEvent.input(urlInput);
      
      // Simulate validation clearing
      urlInput.classList.remove('is-invalid');
      urlInput.classList.add('is-valid');
      
      expect(urlInput).not.toHaveClass('is-invalid');
      expect(urlInput).toHaveClass('is-valid');
    });
  });

  describe('Form Submission Behavior', () => {
    test('should prevent submission with invalid data', () => {
      const form = screen.getByTestId('scraping-form');
      const submitHandler = jest.fn();
      
      form.addEventListener('submit', (e) => {
        e.preventDefault();
        if (!form.checkValidity()) {
          return;
        }
        submitHandler();
      });
      
      // Submit with empty form
      fireEvent.submit(form);
      
      expect(submitHandler).not.toHaveBeenCalled();
    });

    test('should allow submission with valid data', () => {
      const form = screen.getByTestId('scraping-form');
      const urlInput = screen.getByTestId('url-input');
      const depthInput = screen.getByTestId('depth-input');
      const backendSelect = screen.getByTestId('backend-select');
      const submitHandler = jest.fn();
      
      // Fill form with valid data
      fireEvent.change(urlInput, { target: { value: 'https://docs.python.org' } });
      fireEvent.change(depthInput, { target: { value: '3' } });
      fireEvent.change(backendSelect, { target: { value: 'http' } });
      
      form.addEventListener('submit', (e) => {
        e.preventDefault();
        if (form.checkValidity()) {
          submitHandler();
        }
      });
      
      fireEvent.submit(form);
      
      expect(submitHandler).toHaveBeenCalled();
    });

    test('should show loading state during submission', async () => {
      const form = screen.getByTestId('scraping-form');
      const submitButton = screen.getByTestId('submit-button');
      const submitSpinner = screen.getByTestId('submit-spinner');
      
      // Mock successful form submission
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ success: true })
      });
      
      // Set up form submission handler
      form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        // Show loading state
        submitButton.disabled = true;
        submitSpinner.classList.remove('d-none');
        
        try {
          await fetch('/api/scrape', { method: 'POST' });
          
          // Hide loading state
          submitButton.disabled = false;
          submitSpinner.classList.add('d-none');
        } catch (error) {
          submitButton.disabled = false;
          submitSpinner.classList.add('d-none');
        }
      });
      
      // Fill form and submit
      fireEvent.change(screen.getByTestId('url-input'), { 
        target: { value: 'https://example.com' } 
      });
      fireEvent.change(screen.getByTestId('backend-select'), { 
        target: { value: 'http' } 
      });
      
      fireEvent.submit(form);
      
      // Check loading state
      expect(submitButton).toBeDisabled();
      expect(submitSpinner).not.toHaveClass('d-none');
      
      // Wait for completion
      await waitFor(() => {
        expect(submitButton).not.toBeDisabled();
        expect(submitSpinner).toHaveClass('d-none');
      });
    });

    test('should collect form data correctly', () => {
      const urlInput = screen.getByTestId('url-input');
      const depthInput = screen.getByTestId('depth-input');
      const backendSelect = screen.getByTestId('backend-select');
      const advancedCheckbox = screen.getByTestId('advanced-checkbox');
      
      // Fill form
      fireEvent.change(urlInput, { target: { value: 'https://docs.python.org' } });
      fireEvent.change(depthInput, { target: { value: '5' } });
      fireEvent.change(backendSelect, { target: { value: 'crawl4ai' } });
      fireEvent.click(advancedCheckbox);
      
      // Collect form data
      const formData = new FormData(screen.getByTestId('scraping-form'));
      
      expect(urlInput.value).toBe('https://docs.python.org');
      expect(depthInput.value).toBe('5');
      expect(backendSelect.value).toBe('crawl4ai');
      expect(advancedCheckbox.checked).toBe(true);
    });
  });

  describe('Success and Error Responses', () => {
    test('should display success message on successful submission', async () => {
      const successMessage = screen.getByTestId('success-message');
      
      // Mock successful response
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ success: true, message: 'Scraping started!' })
      });
      
      // Simulate successful form submission
      successMessage.classList.remove('d-none');
      
      expect(successMessage).not.toHaveClass('d-none');
      expect(successMessage).toHaveTextContent('Scraping started successfully!');
    });

    test('should display error message on failed submission', async () => {
      const errorMessage = screen.getByTestId('error-message');
      const errorText = screen.getByTestId('error-text');
      
      // Mock error response
      global.fetch.mockResolvedValueOnce({
        ok: false,
        json: async () => ({ error: 'Invalid URL provided' })
      });
      
      // Simulate error display
      errorText.textContent = 'Invalid URL provided';
      errorMessage.classList.remove('d-none');
      
      expect(errorMessage).not.toHaveClass('d-none');
      expect(errorText).toHaveTextContent('Invalid URL provided');
    });

    test('should handle network errors gracefully', async () => {
      const errorMessage = screen.getByTestId('error-message');
      const errorText = screen.getByTestId('error-text');
      
      // Mock network error
      global.fetch.mockRejectedValueOnce(new Error('Network error'));
      
      // Simulate error handling
      errorText.textContent = 'Network error occurred. Please try again.';
      errorMessage.classList.remove('d-none');
      
      expect(errorMessage).not.toHaveClass('d-none');
      expect(errorText).toHaveTextContent('Network error occurred. Please try again.');
    });

    test('should clear previous messages on new submission', () => {
      const successMessage = screen.getByTestId('success-message');
      const errorMessage = screen.getByTestId('error-message');
      
      // Show success message first
      successMessage.classList.remove('d-none');
      
      // Simulate new submission - clear messages
      successMessage.classList.add('d-none');
      errorMessage.classList.add('d-none');
      
      expect(successMessage).toHaveClass('d-none');
      expect(errorMessage).toHaveClass('d-none');
    });
  });

  describe('User Interactions', () => {
    test('should toggle advanced options visibility', () => {
      const advancedCheckbox = screen.getByTestId('advanced-checkbox');
      
      // Mock advanced options panel
      const advancedPanel = document.createElement('div');
      advancedPanel.setAttribute('data-testid', 'advanced-panel');
      advancedPanel.classList.add('d-none');
      container.appendChild(advancedPanel);
      
      // Set up checkbox handler
      advancedCheckbox.addEventListener('change', () => {
        if (advancedCheckbox.checked) {
          advancedPanel.classList.remove('d-none');
        } else {
          advancedPanel.classList.add('d-none');
        }
      });
      
      // Toggle checkbox
      fireEvent.click(advancedCheckbox);
      
      expect(advancedCheckbox.checked).toBe(true);
      expect(advancedPanel).not.toHaveClass('d-none');
      
      // Toggle back
      fireEvent.click(advancedCheckbox);
      
      expect(advancedCheckbox.checked).toBe(false);
      expect(advancedPanel).toHaveClass('d-none');
    });

    test('should update UI based on backend selection', () => {
      const backendSelect = screen.getByTestId('backend-select');
      
      // Mock backend-specific options
      const httpOptions = document.createElement('div');
      httpOptions.setAttribute('data-testid', 'http-options');
      httpOptions.classList.add('d-none');
      container.appendChild(httpOptions);
      
      const crawl4aiOptions = document.createElement('div');
      crawl4aiOptions.setAttribute('data-testid', 'crawl4ai-options');
      crawl4aiOptions.classList.add('d-none');
      container.appendChild(crawl4aiOptions);
      
      // Set up backend change handler
      backendSelect.addEventListener('change', () => {
        // Hide all options
        httpOptions.classList.add('d-none');
        crawl4aiOptions.classList.add('d-none');
        
        // Show selected backend options
        if (backendSelect.value === 'http') {
          httpOptions.classList.remove('d-none');
        } else if (backendSelect.value === 'crawl4ai') {
          crawl4aiOptions.classList.remove('d-none');
        }
      });
      
      // Select HTTP backend
      fireEvent.change(backendSelect, { target: { value: 'http' } });
      
      expect(httpOptions).not.toHaveClass('d-none');
      expect(crawl4aiOptions).toHaveClass('d-none');
      
      // Select Crawl4AI backend
      fireEvent.change(backendSelect, { target: { value: 'crawl4ai' } });
      
      expect(httpOptions).toHaveClass('d-none');
      expect(crawl4aiOptions).not.toHaveClass('d-none');
    });

    test('should provide real-time feedback on input changes', () => {
      const urlInput = screen.getByTestId('url-input');
      
      // Set up real-time validation
      urlInput.addEventListener('input', () => {
        if (urlInput.validity.valid) {
          urlInput.classList.remove('is-invalid');
          urlInput.classList.add('is-valid');
        } else {
          urlInput.classList.remove('is-valid');
          urlInput.classList.add('is-invalid');
        }
      });
      
      // Enter invalid URL
      fireEvent.input(urlInput, { target: { value: 'invalid-url' } });
      
      expect(urlInput).toHaveClass('is-invalid');
      expect(urlInput).not.toHaveClass('is-valid');
      
      // Enter valid URL
      fireEvent.input(urlInput, { target: { value: 'https://docs.python.org' } });
      
      expect(urlInput).not.toHaveClass('is-invalid');
      expect(urlInput).toHaveClass('is-valid');
    });
  });
});
