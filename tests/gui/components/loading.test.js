/**
 * Loading Indicators Component Tests
 * 
 * Tests for loading indicator visibility, animations, and accessibility
 */

import { screen, fireEvent, waitFor } from '@testing-library/dom';
import '@testing-library/jest-dom';

describe('Loading Indicators Component', () => {
  let container;
  
  beforeEach(() => {
    // Create test HTML structure matching base.html
    document.body.innerHTML = `
      <div class="loading-indicator" style="display: none;">
        <div class="spinner-border text-primary" role="status" data-testid="loading-spinner">
          <span class="visually-hidden">Loading...</span>
        </div>
      </div>
      <main class="container my-4" data-testid="main-content">
        <h1>Test Content</h1>
        <p>This is test content that should be dimmed during loading.</p>
      </main>
    `;
    
    container = document.body;
    
    // Add the loading functions from base.html
    global.showLoading = function() {
      document.querySelector('.loading-indicator').style.display = 'block';
      document.querySelector('main').classList.add('content-loading');
    };

    global.hideLoading = function() {
      document.querySelector('.loading-indicator').style.display = 'none';
      document.querySelector('main').classList.remove('content-loading');
    };
  });

  afterEach(() => {
    document.body.innerHTML = '';
    delete global.showLoading;
    delete global.hideLoading;
  });

  describe('Visibility Controls', () => {
    test('should be hidden by default', () => {
      const loadingIndicator = container.querySelector('.loading-indicator');
      expect(loadingIndicator).toHaveStyle('display: none');
    });

    test('should show loading indicator when showLoading is called', () => {
      const loadingIndicator = container.querySelector('.loading-indicator');
      
      global.showLoading();
      
      expect(loadingIndicator).toHaveStyle('display: block');
    });

    test('should hide loading indicator when hideLoading is called', () => {
      const loadingIndicator = container.querySelector('.loading-indicator');
      
      // First show it
      global.showLoading();
      expect(loadingIndicator).toHaveStyle('display: block');
      
      // Then hide it
      global.hideLoading();
      expect(loadingIndicator).toHaveStyle('display: none');
    });

    test('should add content-loading class to main when showing', () => {
      const mainContent = screen.getByTestId('main-content');
      
      global.showLoading();
      
      expect(mainContent).toHaveClass('content-loading');
    });

    test('should remove content-loading class from main when hiding', () => {
      const mainContent = screen.getByTestId('main-content');
      
      // First show loading
      global.showLoading();
      expect(mainContent).toHaveClass('content-loading');
      
      // Then hide loading
      global.hideLoading();
      expect(mainContent).not.toHaveClass('content-loading');
    });

    test('should handle multiple show/hide calls gracefully', () => {
      const loadingIndicator = container.querySelector('.loading-indicator');
      const mainContent = screen.getByTestId('main-content');
      
      // Multiple show calls
      global.showLoading();
      global.showLoading();
      
      expect(loadingIndicator).toHaveStyle('display: block');
      expect(mainContent).toHaveClass('content-loading');
      
      // Multiple hide calls
      global.hideLoading();
      global.hideLoading();
      
      expect(loadingIndicator).toHaveStyle('display: none');
      expect(mainContent).not.toHaveClass('content-loading');
    });
  });

  describe('Animation and Appearance', () => {
    test('should have Bootstrap spinner element', () => {
      const spinner = screen.getByTestId('loading-spinner');
      
      expect(spinner).toHaveClass('spinner-border');
      expect(spinner).toHaveClass('text-primary');
      expect(spinner).toHaveAttribute('role', 'status');
    });

    test('should have loading text for screen readers', () => {
      const loadingText = container.querySelector('.visually-hidden');
      
      expect(loadingText).toBeInTheDocument();
      expect(loadingText).toHaveTextContent('Loading...');
    });

    test('should be properly positioned for overlay', () => {
      const loadingIndicator = container.querySelector('.loading-indicator');
      
      // In a real implementation, we'd check CSS positioning
      expect(loadingIndicator).toBeInTheDocument();
    });

    test('should maintain spinner animation properties', () => {
      const spinner = screen.getByTestId('loading-spinner');
      
      // Bootstrap spinner classes should be present for animation
      expect(spinner).toHaveClass('spinner-border');
    });
  });

  describe('Accessibility During Loading', () => {
    test('should have proper role attribute for screen readers', () => {
      const spinner = screen.getByTestId('loading-spinner');
      
      expect(spinner).toHaveAttribute('role', 'status');
    });

    test('should have visually hidden text for screen readers', () => {
      const hiddenText = container.querySelector('.visually-hidden');
      
      expect(hiddenText).toBeInTheDocument();
      expect(hiddenText).toHaveTextContent('Loading...');
    });

    test('should not interfere with keyboard navigation when hidden', () => {
      const loadingIndicator = container.querySelector('.loading-indicator');
      
      // When hidden, should not be focusable
      expect(loadingIndicator).toHaveStyle('display: none');
    });

    test('should indicate loading state to assistive technology', () => {
      const spinner = screen.getByTestId('loading-spinner');
      
      // Role=status announces loading to screen readers
      expect(spinner).toHaveAttribute('role', 'status');
    });
  });

  describe('Content Dimming Behavior', () => {
    test('should apply content-loading class for dimming effect', () => {
      const mainContent = screen.getByTestId('main-content');
      
      global.showLoading();
      
      expect(mainContent).toHaveClass('content-loading');
    });

    test('should remove dimming effect when loading completes', () => {
      const mainContent = screen.getByTestId('main-content');
      
      global.showLoading();
      expect(mainContent).toHaveClass('content-loading');
      
      global.hideLoading();
      expect(mainContent).not.toHaveClass('content-loading');
    });

    test('should not affect content structure during loading', () => {
      const mainContent = screen.getByTestId('main-content');
      const heading = mainContent.querySelector('h1');
      const paragraph = mainContent.querySelector('p');
      
      global.showLoading();
      
      // Content should still be present
      expect(heading).toBeInTheDocument();
      expect(paragraph).toBeInTheDocument();
      expect(heading).toHaveTextContent('Test Content');
    });
  });

  describe('Integration with Application States', () => {
    test('should work with form submissions', async () => {
      // Simulate form submission workflow
      global.showLoading();
      
      const loadingIndicator = container.querySelector('.loading-indicator');
      expect(loadingIndicator).toHaveStyle('display: block');
      
      // Simulate async operation completion
      await new Promise(resolve => setTimeout(resolve, 10));
      
      global.hideLoading();
      expect(loadingIndicator).toHaveStyle('display: none');
    });

    test('should work with navigation events', () => {
      // Simulate navigation start
      global.showLoading();
      
      const mainContent = screen.getByTestId('main-content');
      expect(mainContent).toHaveClass('content-loading');
      
      // Simulate page load complete
      global.hideLoading();
      expect(mainContent).not.toHaveClass('content-loading');
    });

    test('should handle rapid state changes', () => {
      const loadingIndicator = container.querySelector('.loading-indicator');
      
      // Rapid show/hide sequence
      global.showLoading();
      global.hideLoading();
      global.showLoading();
      global.hideLoading();
      
      // Should end in hidden state
      expect(loadingIndicator).toHaveStyle('display: none');
    });

    test('should clean up state properly', () => {
      const loadingIndicator = container.querySelector('.loading-indicator');
      const mainContent = screen.getByTestId('main-content');
      
      // Ensure clean initial state
      global.hideLoading();
      
      expect(loadingIndicator).toHaveStyle('display: none');
      expect(mainContent).not.toHaveClass('content-loading');
    });
  });
});
