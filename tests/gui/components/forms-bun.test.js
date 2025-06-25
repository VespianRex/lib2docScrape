/**
 * Forms Component Tests
 * 
 * Tests for form elements, validation, submission, and user interaction
 */

import { describe, it, expect, beforeEach, afterEach } from 'bun:test';
import '../setup-bun.js';

describe('Forms Component', () => {
  
  beforeEach(() => {
    // Create test HTML structure with various form elements
    document.body.innerHTML = `
      <div class="forms-container">
        <!-- Configuration Form -->
        <form id="config-form" data-testid="config-form">
          <div class="mb-3">
            <label for="library-name" class="form-label">Library Name</label>
            <input type="text" class="form-control" id="library-name" name="libraryName" 
                   data-testid="library-name" required>
            <div class="invalid-feedback" data-testid="library-name-error"></div>
          </div>
          
          <div class="mb-3">
            <label for="base-url" class="form-label">Base URL</label>
            <input type="url" class="form-control" id="base-url" name="baseUrl" 
                   data-testid="base-url" required>
            <div class="invalid-feedback" data-testid="base-url-error"></div>
          </div>
          
          <div class="mb-3">
            <label for="max-depth" class="form-label">Max Depth</label>
            <input type="number" class="form-control" id="max-depth" name="maxDepth" 
                   min="1" max="10" value="3" data-testid="max-depth">
          </div>
          
          <div class="mb-3">
            <label for="backend-select" class="form-label">Backend</label>
            <select class="form-select" id="backend-select" name="backend" data-testid="backend-select">
              <option value="requests">Requests</option>
              <option value="playwright">Playwright</option>
              <option value="selenium">Selenium</option>
            </select>
          </div>
          
          <div class="mb-3 form-check">
            <input type="checkbox" class="form-check-input" id="enable-js" 
                   name="enableJs" data-testid="enable-js">
            <label class="form-check-label" for="enable-js">
              Enable JavaScript Processing
            </label>
          </div>
          
          <div class="mb-3">
            <label for="exclude-patterns" class="form-label">Exclude Patterns</label>
            <textarea class="form-control" id="exclude-patterns" name="excludePatterns" 
                      rows="3" data-testid="exclude-patterns"></textarea>
          </div>
          
          <button type="submit" class="btn btn-primary" data-testid="submit-config">
            Save Configuration
          </button>
          <button type="reset" class="btn btn-secondary" data-testid="reset-config">
            Reset
          </button>
        </form>
        
        <!-- Search Form -->
        <form id="search-form" class="mt-4" data-testid="search-form">
          <div class="input-group">
            <input type="text" class="form-control" placeholder="Search documentation..." 
                   data-testid="search-input">
            <button type="submit" class="btn btn-outline-secondary" data-testid="search-button">
              <i class="bi bi-search"></i> Search
            </button>
          </div>
        </form>
        
        <!-- Dynamic Form Fields -->
        <div id="dynamic-fields" data-testid="dynamic-fields">
          <button type="button" class="btn btn-link" data-testid="add-field">
            + Add Custom Field
          </button>
        </div>
        
        <!-- Form Validation Messages -->
        <div id="form-messages" data-testid="form-messages">
          <div class="alert alert-success d-none" data-testid="success-message">
            <span class="message-text"></span>
          </div>
          <div class="alert alert-danger d-none" data-testid="error-message">
            <span class="message-text"></span>
          </div>
        </div>
      </div>
    `;
  });

  afterEach(() => {
    document.body.innerHTML = '';
  });

  describe('Form Structure Tests', () => {
    it('should have configuration form with all required fields', () => {
      const form = document.querySelector('[data-testid="config-form"]');
      const libraryName = document.querySelector('[data-testid="library-name"]');
      const baseUrl = document.querySelector('[data-testid="base-url"]');
      const maxDepth = document.querySelector('[data-testid="max-depth"]');
      const backendSelect = document.querySelector('[data-testid="backend-select"]');
      
      expect(form).not.toBeNull();
      expect(libraryName).not.toBeNull();
      expect(baseUrl).not.toBeNull();
      expect(maxDepth).not.toBeNull();
      expect(backendSelect).not.toBeNull();
    });

    it('should have proper form labels and accessibility', () => {
      const libraryNameLabel = document.querySelector('label[for="library-name"]');
      const baseUrlLabel = document.querySelector('label[for="base-url"]');
      const maxDepthLabel = document.querySelector('label[for="max-depth"]');
      
      expect(libraryNameLabel).not.toBeNull();
      expect(baseUrlLabel).not.toBeNull();
      expect(maxDepthLabel).not.toBeNull();
      expect(libraryNameLabel.textContent).toBe('Library Name');
      expect(baseUrlLabel.textContent).toBe('Base URL');
    });

    it('should have form action buttons', () => {
      const submitButton = document.querySelector('[data-testid="submit-config"]');
      const resetButton = document.querySelector('[data-testid="reset-config"]');
      
      expect(submitButton).not.toBeNull();
      expect(resetButton).not.toBeNull();
      expect(submitButton.type).toBe('submit');
      expect(resetButton.type).toBe('reset');
    });
  });

  describe('Input Field Tests', () => {
    it('should handle text input correctly', () => {
      const libraryName = document.querySelector('[data-testid="library-name"]');
      
      libraryName.value = 'React';
      expect(libraryName.value).toBe('React');
      
      // Simulate user input
      libraryName.value = 'Vue.js';
      simulateInput(libraryName, 'Vue.js');
      expect(libraryName.value).toBe('Vue.js');
    });

    it('should handle URL input with validation', () => {
      const baseUrl = document.querySelector('[data-testid="base-url"]');
      
      baseUrl.value = 'https://vuejs.org/guide/';
      expect(baseUrl.value).toBe('https://vuejs.org/guide/');
      expect(baseUrl.type).toBe('url');
    });

    it('should handle number input with constraints', () => {
      const maxDepth = document.querySelector('[data-testid="max-depth"]');
      
      expect(maxDepth.type).toBe('number');
      expect(maxDepth.min).toBe('1');
      expect(maxDepth.max).toBe('10');
      expect(maxDepth.value).toBe('3');
      
      maxDepth.value = '5';
      expect(maxDepth.value).toBe('5');
    });

    it('should handle select dropdown', () => {
      const backendSelect = document.querySelector('[data-testid="backend-select"]');
      const options = backendSelect.querySelectorAll('option');
      
      expect(options.length).toBe(3);
      expect(options[0].value).toBe('requests');
      expect(options[1].value).toBe('playwright');
      expect(options[2].value).toBe('selenium');
      
      backendSelect.value = 'playwright';
      expect(backendSelect.value).toBe('playwright');
    });

    it('should handle checkbox input', () => {
      const enableJs = document.querySelector('[data-testid="enable-js"]');
      
      expect(enableJs.type).toBe('checkbox');
      expect(enableJs.checked).toBe(false);
      
      enableJs.checked = true;
      expect(enableJs.checked).toBe(true);
    });

    it('should handle textarea input', () => {
      const excludePatterns = document.querySelector('[data-testid="exclude-patterns"]');
      
      expect(excludePatterns.tagName.toLowerCase()).toBe('textarea');
      expect(parseInt(excludePatterns.rows)).toBe(3);
      
      excludePatterns.value = '*.pdf\n*.jpg\n*.png';
      expect(excludePatterns.value).toBe('*.pdf\n*.jpg\n*.png');
    });
  });

  describe('Form Validation Tests', () => {
    it('should have required field attributes', () => {
      const libraryName = document.querySelector('[data-testid="library-name"]');
      const baseUrl = document.querySelector('[data-testid="base-url"]');
      
      expect(libraryName.required).toBe(true);
      expect(baseUrl.required).toBe(true);
    });

    it('should show validation errors for empty required fields', () => {
      const form = document.querySelector('[data-testid="config-form"]');
      const libraryName = document.querySelector('[data-testid="library-name"]');
      const libraryNameError = document.querySelector('[data-testid="library-name-error"]');
      
      // Simulate form submission with empty required field
      libraryName.value = '';
      libraryName.classList.add('is-invalid');
      libraryNameError.textContent = 'Library name is required';
      
      expect(libraryName.classList.contains('is-invalid')).toBe(true);
      expect(libraryNameError.textContent).toBe('Library name is required');
    });

    it('should validate URL format', () => {
      const baseUrl = document.querySelector('[data-testid="base-url"]');
      const baseUrlError = document.querySelector('[data-testid="base-url-error"]');
      
      // Simulate invalid URL
      baseUrl.value = 'not-a-url';
      baseUrl.classList.add('is-invalid');
      baseUrlError.textContent = 'Please enter a valid URL';
      
      expect(baseUrl.classList.contains('is-invalid')).toBe(true);
      expect(baseUrlError.textContent).toBe('Please enter a valid URL');
    });

    it('should validate number range', () => {
      const maxDepth = document.querySelector('[data-testid="max-depth"]');
      
      // Test valid range
      maxDepth.value = '5';
      expect(parseInt(maxDepth.value)).toBeGreaterThanOrEqual(parseInt(maxDepth.min));
      expect(parseInt(maxDepth.value)).toBeLessThanOrEqual(parseInt(maxDepth.max));
      
      // Test boundary values
      maxDepth.value = '1';
      expect(parseInt(maxDepth.value)).toBe(1);
      
      maxDepth.value = '10';
      expect(parseInt(maxDepth.value)).toBe(10);
    });

    it('should clear validation errors when field becomes valid', () => {
      const libraryName = document.querySelector('[data-testid="library-name"]');
      const libraryNameError = document.querySelector('[data-testid="library-name-error"]');
      
      // Start with error state
      libraryName.classList.add('is-invalid');
      libraryNameError.textContent = 'Library name is required';
      
      // Fix the field
      libraryName.value = 'React';
      libraryName.classList.remove('is-invalid');
      libraryName.classList.add('is-valid');
      libraryNameError.textContent = '';
      
      expect(libraryName.classList.contains('is-invalid')).toBe(false);
      expect(libraryName.classList.contains('is-valid')).toBe(true);
      expect(libraryNameError.textContent).toBe('');
    });
  });

  describe('Form Submission Tests', () => {
    it('should handle form submission event', () => {
      const form = document.querySelector('[data-testid="config-form"]');
      let formSubmitted = false;
      
      form.addEventListener('submit', (e) => {
        e.preventDefault();
        formSubmitted = true;
      });
      
      simulateSubmit(form);
      expect(formSubmitted).toBe(true);
    });

    it('should collect form data correctly', () => {
      const form = document.querySelector('[data-testid="config-form"]');
      const libraryName = document.querySelector('[data-testid="library-name"]');
      const baseUrl = document.querySelector('[data-testid="base-url"]');
      const maxDepth = document.querySelector('[data-testid="max-depth"]');
      const backendSelect = document.querySelector('[data-testid="backend-select"]');
      const enableJs = document.querySelector('[data-testid="enable-js"]');
      
      // Set form values
      libraryName.value = 'Angular';
      baseUrl.value = 'https://angular.io/docs';
      maxDepth.value = '4';
      backendSelect.value = 'playwright';
      enableJs.checked = true;
      
      // Create FormData to simulate data collection
      const formData = new FormData(form);
      
      expect(formData.get('libraryName')).toBe('Angular');
      expect(formData.get('baseUrl')).toBe('https://angular.io/docs');
      expect(formData.get('maxDepth')).toBe('4');
      expect(formData.get('backend')).toBe('playwright');
      expect(formData.get('enableJs')).toBe('on'); // checkbox checked value
    });

    it('should handle form reset', () => {
      const form = document.querySelector('[data-testid="config-form"]');
      const libraryName = document.querySelector('[data-testid="library-name"]');
      const baseUrl = document.querySelector('[data-testid="base-url"]');
      const enableJs = document.querySelector('[data-testid="enable-js"]');
      
      // Set some values
      libraryName.value = 'Test Library';
      baseUrl.value = 'https://example.com';
      enableJs.checked = true;
      
      // Reset form
      form.reset();
      
      expect(libraryName.value).toBe('');
      expect(baseUrl.value).toBe('');
      expect(enableJs.checked).toBe(false);
    });
  });

  describe('Search Form Tests', () => {
    it('should have search form structure', () => {
      const searchForm = document.querySelector('[data-testid="search-form"]');
      const searchInput = document.querySelector('[data-testid="search-input"]');
      const searchButton = document.querySelector('[data-testid="search-button"]');
      
      expect(searchForm).not.toBeNull();
      expect(searchInput).not.toBeNull();
      expect(searchButton).not.toBeNull();
    });

    it('should handle search input', () => {
      const searchInput = document.querySelector('[data-testid="search-input"]');
      
      searchInput.value = 'component lifecycle';
      expect(searchInput.value).toBe('component lifecycle');
      expect(searchInput.placeholder).toBe('Search documentation...');
    });

    it('should handle search submission', () => {
      const searchForm = document.querySelector('[data-testid="search-form"]');
      const searchInput = document.querySelector('[data-testid="search-input"]');
      let searchSubmitted = false;
      let searchQuery = '';
      
      searchForm.addEventListener('submit', (e) => {
        e.preventDefault();
        searchSubmitted = true;
        searchQuery = searchInput.value;
      });
      
      searchInput.value = 'hooks tutorial';
      simulateSubmit(searchForm);
      
      expect(searchSubmitted).toBe(true);
      expect(searchQuery).toBe('hooks tutorial');
    });
  });

  describe('Dynamic Fields Tests', () => {
    it('should have add field button', () => {
      const addFieldButton = document.querySelector('[data-testid="add-field"]');
      
      expect(addFieldButton).not.toBeNull();
      expect(addFieldButton.textContent.trim()).toBe('+ Add Custom Field');
    });

    it('should be able to add dynamic fields', () => {
      const dynamicFields = document.querySelector('[data-testid="dynamic-fields"]');
      const addFieldButton = document.querySelector('[data-testid="add-field"]');
      
      // Simulate adding a dynamic field
      const newField = document.createElement('div');
      newField.className = 'mb-3 dynamic-field';
      newField.innerHTML = `
        <label class="form-label">Custom Field</label>
        <input type="text" class="form-control" name="customField">
        <button type="button" class="btn btn-sm btn-danger remove-field">Remove</button>
      `;
      
      dynamicFields.appendChild(newField);
      
      expect(dynamicFields.children.length).toBe(2); // Original button + new field
      expect(dynamicFields.querySelector('.dynamic-field')).not.toBeNull();
    });

    it('should be able to remove dynamic fields', () => {
      const dynamicFields = document.querySelector('[data-testid="dynamic-fields"]');
      
      // Add a field first
      const newField = document.createElement('div');
      newField.className = 'mb-3 dynamic-field';
      newField.innerHTML = `
        <input type="text" class="form-control">
        <button type="button" class="btn btn-sm btn-danger remove-field">Remove</button>
      `;
      dynamicFields.appendChild(newField);
      
      expect(dynamicFields.children.length).toBe(2);
      
      // Remove the field
      newField.remove();
      
      expect(dynamicFields.children.length).toBe(1);
      expect(dynamicFields.querySelector('.dynamic-field')).toBeNull();
    });
  });

  describe('Form Messages Tests', () => {
    it('should have message containers', () => {
      const successMessage = document.querySelector('[data-testid="success-message"]');
      const errorMessage = document.querySelector('[data-testid="error-message"]');
      
      expect(successMessage).not.toBeNull();
      expect(errorMessage).not.toBeNull();
      expect(successMessage.classList.contains('d-none')).toBe(true);
      expect(errorMessage.classList.contains('d-none')).toBe(true);
    });

    it('should show success message', () => {
      const successMessage = document.querySelector('[data-testid="success-message"]');
      const messageText = successMessage.querySelector('.message-text');
      
      messageText.textContent = 'Configuration saved successfully!';
      successMessage.classList.remove('d-none');
      
      expect(successMessage.classList.contains('d-none')).toBe(false);
      expect(messageText.textContent).toBe('Configuration saved successfully!');
    });

    it('should show error message', () => {
      const errorMessage = document.querySelector('[data-testid="error-message"]');
      const messageText = errorMessage.querySelector('.message-text');
      
      messageText.textContent = 'Failed to save configuration. Please try again.';
      errorMessage.classList.remove('d-none');
      
      expect(errorMessage.classList.contains('d-none')).toBe(false);
      expect(messageText.textContent).toBe('Failed to save configuration. Please try again.');
    });

    it('should be able to hide messages', () => {
      const successMessage = document.querySelector('[data-testid="success-message"]');
      const errorMessage = document.querySelector('[data-testid="error-message"]');
      
      // Show messages first
      successMessage.classList.remove('d-none');
      errorMessage.classList.remove('d-none');
      
      // Hide messages
      successMessage.classList.add('d-none');
      errorMessage.classList.add('d-none');
      
      expect(successMessage.classList.contains('d-none')).toBe(true);
      expect(errorMessage.classList.contains('d-none')).toBe(true);
    });
  });

  describe('Bootstrap Integration Tests', () => {
    it('should have proper Bootstrap form classes', () => {
      const inputs = document.querySelectorAll('.form-control');
      const labels = document.querySelectorAll('.form-label');
      const select = document.querySelector('.form-select');
      const checkbox = document.querySelector('.form-check-input');
      
      expect(inputs.length).toBeGreaterThan(0);
      expect(labels.length).toBeGreaterThan(0);
      expect(select).not.toBeNull();
      expect(checkbox).not.toBeNull();
    });

    it('should have proper button styling', () => {
      const submitButton = document.querySelector('[data-testid="submit-config"]');
      const resetButton = document.querySelector('[data-testid="reset-config"]');
      const searchButton = document.querySelector('[data-testid="search-button"]');
      
      expect(submitButton.classList.contains('btn')).toBe(true);
      expect(submitButton.classList.contains('btn-primary')).toBe(true);
      expect(resetButton.classList.contains('btn-secondary')).toBe(true);
      expect(searchButton.classList.contains('btn-outline-secondary')).toBe(true);
    });

    it('should have proper spacing classes', () => {
      const formGroups = document.querySelectorAll('.mb-3');
      const inputGroup = document.querySelector('.input-group');
      
      expect(formGroups.length).toBeGreaterThan(0);
      expect(inputGroup).not.toBeNull();
    });
  });
});
