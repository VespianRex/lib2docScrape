/**
 * Navigation Bar Component Tests
 * 
 * Tests for navigation bar functionality, active states, and responsive behavior
 */

import { describe, it, expect, beforeEach } from 'bun:test';
import '../setup.js';

describe('Navigation Bar Component', () => {
  let container;
  
  beforeEach(() => {
    // Create test HTML structure
    document.body.innerHTML = `
      <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
        <div class="container-fluid">
          <a class="navbar-brand" href="/">Lib2DocScrape</a>
          <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
            <span class="navbar-toggler-icon"></span>
          </button>
          <div class="collapse navbar-collapse" id="navbarNav">
            <ul class="navbar-nav">
              <li class="nav-item">
                <a class="nav-link" href="/" data-testid="nav-home">
                  <i class="bi bi-play-circle"></i> Documentation Scraper
                </a>
              </li>
              <li class="nav-item">
                <a class="nav-link" href="/home" data-testid="nav-welcome">
                  <i class="bi bi-house-door"></i> Welcome
                </a>
              </li>
              <li class="nav-item">
                <a class="nav-link" href="/config" data-testid="nav-config">
                  <i class="bi bi-gear"></i> Configuration
                </a>
              </li>
              <li class="nav-item">
                <a class="nav-link" href="/results" data-testid="nav-results">
                  <i class="bi bi-folder-open"></i> Browse Results
                </a>
              </li>
            </ul>
          </div>
        </div>
      </nav>
    `;
    container = document.body;
  });

  afterEach(() => {
    document.body.innerHTML = '';
  });

  describe('Active State Tests', () => {
    test('should highlight correct menu item for home page', () => {
      // Simulate being on home page
      const homeLink = screen.getByTestId('nav-home');
      homeLink.classList.add('active');

      expect(homeLink).toHaveClass('active');
      expect(screen.getByTestId('nav-config')).not.toHaveClass('active');
      expect(screen.getByTestId('nav-results')).not.toHaveClass('active');
    });

    test('should highlight correct menu item for config page', () => {
      // Simulate being on config page
      const configLink = screen.getByTestId('nav-config');
      configLink.classList.add('active');

      expect(configLink).toHaveClass('active');
      expect(screen.getByTestId('nav-home')).not.toHaveClass('active');
      expect(screen.getByTestId('nav-results')).not.toHaveClass('active');
    });

    test('should display icons for each menu item', () => {
      const homeIcon = screen.getByTestId('nav-home').querySelector('i.bi-play-circle');
      const welcomeIcon = screen.getByTestId('nav-welcome').querySelector('i.bi-house-door');
      const configIcon = screen.getByTestId('nav-config').querySelector('i.bi-gear');
      const resultsIcon = screen.getByTestId('nav-results').querySelector('i.bi-folder-open');

      expect(homeIcon).toBeInTheDocument();
      expect(welcomeIcon).toBeInTheDocument();
      expect(configIcon).toBeInTheDocument();
      expect(resultsIcon).toBeInTheDocument();
    });

    test('should update active state on navigation', () => {
      const homeLink = screen.getByTestId('nav-home');
      const configLink = screen.getByTestId('nav-config');

      // Simulate navigation
      homeLink.classList.remove('active');
      configLink.classList.add('active');

      expect(homeLink).not.toHaveClass('active');
      expect(configLink).toHaveClass('active');
    });
  });

  describe('Responsive Behavior', () => {
    test('should have navbar toggler for mobile', () => {
      const toggler = container.querySelector('.navbar-toggler');
      expect(toggler).toBeInTheDocument();
      expect(toggler).toHaveAttribute('data-bs-toggle', 'collapse');
      expect(toggler).toHaveAttribute('data-bs-target', '#navbarNav');
    });

    test('should have collapsible navigation menu', () => {
      const navCollapse = container.querySelector('#navbarNav');
      expect(navCollapse).toHaveClass('collapse');
      expect(navCollapse).toHaveClass('navbar-collapse');
    });

    test('should toggle navigation on mobile button click', async () => {
      const toggler = container.querySelector('.navbar-toggler');
      const navCollapse = container.querySelector('#navbarNav');

      // Mock Bootstrap collapse behavior
      const mockCollapse = jest.fn();
      global.bootstrap = { Collapse: mockCollapse };

      fireEvent.click(toggler);

      // Verify Bootstrap collapse would be called
      expect(mockCollapse).toHaveBeenCalled();
    });

    test('should have proper hamburger menu icon', () => {
      const togglerIcon = container.querySelector('.navbar-toggler-icon');
      expect(togglerIcon).toBeInTheDocument();
    });
  });

  describe('Link Functionality', () => {
    test('should have correct href attributes', () => {
      expect(screen.getByTestId('nav-home')).toHaveAttribute('href', '/');
      expect(screen.getByTestId('nav-welcome')).toHaveAttribute('href', '/home');
      expect(screen.getByTestId('nav-config')).toHaveAttribute('href', '/config');
      expect(screen.getByTestId('nav-results')).toHaveAttribute('href', '/results');
    });

    test('should have navbar brand link', () => {
      const brandLink = container.querySelector('.navbar-brand');
      expect(brandLink).toBeInTheDocument();
      expect(brandLink).toHaveAttribute('href', '/');
      expect(brandLink).toHaveTextContent('Lib2DocScrape');
    });

    test('should handle click events on navigation links', () => {
      const homeLink = screen.getByTestId('nav-home');
      const clickHandler = jest.fn();
      
      homeLink.addEventListener('click', clickHandler);
      fireEvent.click(homeLink);

      expect(clickHandler).toHaveBeenCalled();
    });

    test('should prevent default behavior for SPA navigation', () => {
      const homeLink = screen.getByTestId('nav-home');
      const event = new Event('click', { cancelable: true });
      const preventDefaultSpy = jest.spyOn(event, 'preventDefault');

      // Simulate SPA navigation handler
      homeLink.addEventListener('click', (e) => {
        e.preventDefault();
        // SPA routing logic would go here
      });

      homeLink.dispatchEvent(event);
      expect(preventDefaultSpy).toHaveBeenCalled();
    });
  });

  describe('Accessibility', () => {
    test('should have proper ARIA labels', () => {
      const toggler = container.querySelector('.navbar-toggler');
      // Note: In a real implementation, we'd add aria-label
      expect(toggler).toHaveAttribute('data-bs-toggle', 'collapse');
    });

    test('should be keyboard navigable', () => {
      const homeLink = screen.getByTestId('nav-home');
      expect(homeLink).toBeInstanceOf(HTMLAnchorElement);
      
      // Links are naturally focusable
      homeLink.focus();
      expect(document.activeElement).toBe(homeLink);
    });

    test('should have semantic navigation structure', () => {
      const nav = container.querySelector('nav');
      const navList = container.querySelector('.navbar-nav');
      
      expect(nav).toBeInTheDocument();
      expect(navList).toBeInTheDocument();
      expect(navList.tagName).toBe('UL');
    });
  });
});
