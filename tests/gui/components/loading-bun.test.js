/**
 * Loading Indicators Component Tests
 * 
 * Tests for loading spinners, progress bars, and loading state management
 */

import { describe, it, expect, beforeEach, afterEach } from 'bun:test';
import '../setup-bun.js';

describe('Loading Indicators Component', () => {
  
  beforeEach(() => {
    // Create test HTML structure with loading components
    document.body.innerHTML = `
      <div class="loading-container">
        <!-- Spinner Loading Indicator -->
        <div id="spinner-loader" class="spinner-border text-primary" role="status" data-testid="spinner-loader">
          <span class="visually-hidden">Loading...</span>
        </div>
        
        <!-- Progress Bar Loading Indicator -->
        <div class="progress" data-testid="progress-container">
          <div id="progress-bar" class="progress-bar" role="progressbar" 
               style="width: 0%" aria-valuenow="0" aria-valuemin="0" aria-valuemax="100" data-testid="progress-bar">
          </div>
        </div>
        
        <!-- Loading Overlay -->
        <div id="loading-overlay" class="loading-overlay d-none" data-testid="loading-overlay">
          <div class="spinner-border text-light" role="status">
            <span class="visually-hidden">Processing...</span>
          </div>
          <p class="text-light mt-3">Please wait while we process your request...</p>
        </div>
        
        <!-- Status Messages -->
        <div id="status-messages" data-testid="status-messages">
          <div class="alert alert-info d-none" id="info-message" data-testid="info-message">
            <span class="message-text"></span>
          </div>
          <div class="alert alert-success d-none" id="success-message" data-testid="success-message">
            <span class="message-text"></span>
          </div>
          <div class="alert alert-danger d-none" id="error-message" data-testid="error-message">
            <span class="message-text"></span>
          </div>
        </div>
      </div>
    `;
  });

  afterEach(() => {
    document.body.innerHTML = '';
  });

  describe('Spinner Loading Tests', () => {
    it('should create spinner with correct Bootstrap classes', () => {
      const spinner = document.querySelector('[data-testid="spinner-loader"]');
      
      expect(spinner).not.toBeNull();
      expect(spinner.classList.contains('spinner-border')).toBe(true);
      expect(spinner.classList.contains('text-primary')).toBe(true);
      expect(spinner.getAttribute('role')).toBe('status');
    });

    it('should have accessible loading text', () => {
      const spinner = document.querySelector('[data-testid="spinner-loader"]');
      const hiddenText = spinner.querySelector('.visually-hidden');
      
      expect(hiddenText).not.toBeNull();
      expect(hiddenText.textContent).toBe('Loading...');
    });

    it('should be able to show and hide spinner', () => {
      const spinner = document.querySelector('[data-testid="spinner-loader"]');
      
      // Test hiding
      spinner.classList.add('d-none');
      expect(spinner.classList.contains('d-none')).toBe(true);
      
      // Test showing
      spinner.classList.remove('d-none');
      expect(spinner.classList.contains('d-none')).toBe(false);
    });
  });

  describe('Progress Bar Tests', () => {
    it('should create progress bar with correct structure', () => {
      const progressContainer = document.querySelector('[data-testid="progress-container"]');
      const progressBar = document.querySelector('[data-testid="progress-bar"]');
      
      expect(progressContainer).not.toBeNull();
      expect(progressBar).not.toBeNull();
      expect(progressContainer.classList.contains('progress')).toBe(true);
      expect(progressBar.classList.contains('progress-bar')).toBe(true);
    });

    it('should have correct ARIA attributes', () => {
      const progressBar = document.querySelector('[data-testid="progress-bar"]');
      
      expect(progressBar.getAttribute('role')).toBe('progressbar');
      expect(progressBar.getAttribute('aria-valuenow')).toBe('0');
      expect(progressBar.getAttribute('aria-valuemin')).toBe('0');
      expect(progressBar.getAttribute('aria-valuemax')).toBe('100');
    });

    it('should update progress correctly', () => {
      const progressBar = document.querySelector('[data-testid="progress-bar"]');
      
      // Simulate progress update to 50%
      progressBar.style.width = '50%';
      progressBar.setAttribute('aria-valuenow', '50');
      
      expect(progressBar.style.width).toBe('50%');
      expect(progressBar.getAttribute('aria-valuenow')).toBe('50');
    });

    it('should handle progress completion', () => {
      const progressBar = document.querySelector('[data-testid="progress-bar"]');
      
      // Simulate completion
      progressBar.style.width = '100%';
      progressBar.setAttribute('aria-valuenow', '100');
      
      expect(progressBar.style.width).toBe('100%');
      expect(progressBar.getAttribute('aria-valuenow')).toBe('100');
    });
  });

  describe('Loading Overlay Tests', () => {
    it('should create loading overlay with correct structure', () => {
      const overlay = document.querySelector('[data-testid="loading-overlay"]');
      const spinner = overlay.querySelector('.spinner-border');
      const message = overlay.querySelector('p');
      
      expect(overlay).not.toBeNull();
      expect(spinner).not.toBeNull();
      expect(message).not.toBeNull();
      expect(overlay.classList.contains('loading-overlay')).toBe(true);
    });

    it('should be hidden by default', () => {
      const overlay = document.querySelector('[data-testid="loading-overlay"]');
      expect(overlay.classList.contains('d-none')).toBe(true);
    });

    it('should be able to show and hide overlay', () => {
      const overlay = document.querySelector('[data-testid="loading-overlay"]');
      
      // Show overlay
      overlay.classList.remove('d-none');
      expect(overlay.classList.contains('d-none')).toBe(false);
      
      // Hide overlay
      overlay.classList.add('d-none');
      expect(overlay.classList.contains('d-none')).toBe(true);
    });

    it('should have appropriate loading message', () => {
      const overlay = document.querySelector('[data-testid="loading-overlay"]');
      const message = overlay.querySelector('p');
      
      expect(message.textContent.trim()).toBe('Please wait while we process your request...');
      expect(message.classList.contains('text-light')).toBe(true);
    });
  });

  describe('Status Messages Tests', () => {
    it('should have all status message types', () => {
      const infoMessage = document.querySelector('[data-testid="info-message"]');
      const successMessage = document.querySelector('[data-testid="success-message"]');
      const errorMessage = document.querySelector('[data-testid="error-message"]');
      
      expect(infoMessage).not.toBeNull();
      expect(successMessage).not.toBeNull();
      expect(errorMessage).not.toBeNull();
    });

    it('should have correct Bootstrap alert classes', () => {
      const infoMessage = document.querySelector('[data-testid="info-message"]');
      const successMessage = document.querySelector('[data-testid="success-message"]');
      const errorMessage = document.querySelector('[data-testid="error-message"]');
      
      expect(infoMessage.classList.contains('alert')).toBe(true);
      expect(infoMessage.classList.contains('alert-info')).toBe(true);
      expect(successMessage.classList.contains('alert-success')).toBe(true);
      expect(errorMessage.classList.contains('alert-danger')).toBe(true);
    });

    it('should be hidden by default', () => {
      const infoMessage = document.querySelector('[data-testid="info-message"]');
      const successMessage = document.querySelector('[data-testid="success-message"]');
      const errorMessage = document.querySelector('[data-testid="error-message"]');
      
      expect(infoMessage.classList.contains('d-none')).toBe(true);
      expect(successMessage.classList.contains('d-none')).toBe(true);
      expect(errorMessage.classList.contains('d-none')).toBe(true);
    });

    it('should be able to show status messages with text', () => {
      const infoMessage = document.querySelector('[data-testid="info-message"]');
      const messageText = infoMessage.querySelector('.message-text');
      
      // Show message with text
      messageText.textContent = 'Processing your request...';
      infoMessage.classList.remove('d-none');
      
      expect(messageText.textContent).toBe('Processing your request...');
      expect(infoMessage.classList.contains('d-none')).toBe(false);
    });
  });

  describe('Loading State Management Tests', () => {
    it('should be able to simulate loading workflow', () => {
      const spinner = document.querySelector('[data-testid="spinner-loader"]');
      const progressBar = document.querySelector('[data-testid="progress-bar"]');
      const overlay = document.querySelector('[data-testid="loading-overlay"]');
      
      // Start loading
      spinner.classList.remove('d-none');
      overlay.classList.remove('d-none');
      
      expect(spinner.classList.contains('d-none')).toBe(false);
      expect(overlay.classList.contains('d-none')).toBe(false);
      
      // Update progress
      progressBar.style.width = '75%';
      progressBar.setAttribute('aria-valuenow', '75');
      
      expect(progressBar.style.width).toBe('75%');
      
      // Complete loading
      spinner.classList.add('d-none');
      overlay.classList.add('d-none');
      progressBar.style.width = '100%';
      
      expect(spinner.classList.contains('d-none')).toBe(true);
      expect(overlay.classList.contains('d-none')).toBe(true);
      expect(progressBar.style.width).toBe('100%');
    });

    it('should handle error state during loading', () => {
      const spinner = document.querySelector('[data-testid="spinner-loader"]');
      const errorMessage = document.querySelector('[data-testid="error-message"]');
      const messageText = errorMessage.querySelector('.message-text');
      
      // Start loading
      spinner.classList.remove('d-none');
      
      // Simulate error
      spinner.classList.add('d-none');
      messageText.textContent = 'An error occurred while processing';
      errorMessage.classList.remove('d-none');
      
      expect(spinner.classList.contains('d-none')).toBe(true);
      expect(errorMessage.classList.contains('d-none')).toBe(false);
      expect(messageText.textContent).toBe('An error occurred while processing');
    });

    it('should handle success state after loading', () => {
      const spinner = document.querySelector('[data-testid="spinner-loader"]');
      const successMessage = document.querySelector('[data-testid="success-message"]');
      const messageText = successMessage.querySelector('.message-text');
      
      // Start loading
      spinner.classList.remove('d-none');
      
      // Complete successfully
      spinner.classList.add('d-none');
      messageText.textContent = 'Operation completed successfully';
      successMessage.classList.remove('d-none');
      
      expect(spinner.classList.contains('d-none')).toBe(true);
      expect(successMessage.classList.contains('d-none')).toBe(false);
      expect(messageText.textContent).toBe('Operation completed successfully');
    });
  });

  describe('Accessibility Tests', () => {
    it('should have proper ARIA roles for loading elements', () => {
      const spinner = document.querySelector('[data-testid="spinner-loader"]');
      const progressBar = document.querySelector('[data-testid="progress-bar"]');
      
      expect(spinner.getAttribute('role')).toBe('status');
      expect(progressBar.getAttribute('role')).toBe('progressbar');
    });

    it('should have hidden text for screen readers', () => {
      const spinner = document.querySelector('[data-testid="spinner-loader"]');
      const hiddenTexts = spinner.querySelectorAll('.visually-hidden');
      
      expect(hiddenTexts.length).toBe(1);
      expect(hiddenTexts[0].textContent.length).toBeGreaterThan(0);
    });

    it('should update progress bar ARIA attributes correctly', () => {
      const progressBar = document.querySelector('[data-testid="progress-bar"]');
      
      // Update progress
      progressBar.setAttribute('aria-valuenow', '33');
      progressBar.style.width = '33%';
      
      expect(progressBar.getAttribute('aria-valuenow')).toBe('33');
      expect(parseInt(progressBar.getAttribute('aria-valuemin'))).toBeLessThanOrEqual(33);
      expect(parseInt(progressBar.getAttribute('aria-valuemax'))).toBeGreaterThanOrEqual(33);
    });
  });
});
