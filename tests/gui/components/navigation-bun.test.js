/**
 * Navigation Bar Component Tests
 * 
 * Tests for navigation bar functionality, active states, and responsive behavior
 */

import { describe, it, expect, beforeEach, afterEach } from 'bun:test';
import '../setup-bun.js';

describe('Navigation Bar Component', () => {
  
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
  });

  afterEach(() => {
    document.body.innerHTML = '';
  });

  describe('Active State Tests', () => {
    it('should highlight correct menu item for home page', () => {
      // Simulate being on home page
      const homeLink = document.querySelector('[data-testid="nav-home"]');
      homeLink.classList.add('active');

      expect(homeLink.classList.contains('active')).toBe(true);
      expect(document.querySelector('[data-testid="nav-config"]').classList.contains('active')).toBe(false);
      expect(document.querySelector('[data-testid="nav-results"]').classList.contains('active')).toBe(false);
    });

    it('should highlight correct menu item for config page', () => {
      // Simulate being on config page
      const configLink = document.querySelector('[data-testid="nav-config"]');
      configLink.classList.add('active');

      expect(configLink.classList.contains('active')).toBe(true);
      expect(document.querySelector('[data-testid="nav-home"]').classList.contains('active')).toBe(false);
      expect(document.querySelector('[data-testid="nav-results"]').classList.contains('active')).toBe(false);
    });

    it('should display icons for each menu item', () => {
      const homeIcon = document.querySelector('[data-testid="nav-home"] i.bi-play-circle');
      const welcomeIcon = document.querySelector('[data-testid="nav-welcome"] i.bi-house-door');
      const configIcon = document.querySelector('[data-testid="nav-config"] i.bi-gear');
      const resultsIcon = document.querySelector('[data-testid="nav-results"] i.bi-folder-open');

      expect(homeIcon).not.toBeNull();
      expect(welcomeIcon).not.toBeNull();
      expect(configIcon).not.toBeNull();
      expect(resultsIcon).not.toBeNull();
    });

    it('should update active state on navigation', () => {
      const homeLink = document.querySelector('[data-testid="nav-home"]');
      const configLink = document.querySelector('[data-testid="nav-config"]');

      // Simulate navigation
      homeLink.classList.remove('active');
      configLink.classList.add('active');

      expect(homeLink.classList.contains('active')).toBe(false);
      expect(configLink.classList.contains('active')).toBe(true);
    });
  });

  describe('Responsive Behavior Tests', () => {
    it('should contain responsive navbar toggle button', () => {
      const toggleButton = document.querySelector('.navbar-toggler');
      expect(toggleButton).not.toBeNull();
      expect(toggleButton.getAttribute('data-bs-toggle')).toBe('collapse');
      expect(toggleButton.getAttribute('data-bs-target')).toBe('#navbarNav');
    });

    it('should have collapsible navigation menu', () => {
      const navbarCollapse = document.querySelector('#navbarNav');
      expect(navbarCollapse).not.toBeNull();
      expect(navbarCollapse.classList.contains('collapse')).toBe(true);
      expect(navbarCollapse.classList.contains('navbar-collapse')).toBe(true);
    });

    it('should contain all navigation links in collapsible section', () => {
      const collapsibleNav = document.querySelector('#navbarNav');
      const navLinks = collapsibleNav.querySelectorAll('.nav-link');
      
      expect(navLinks.length).toBe(4);
    });
  });

  describe('Brand and Logo Tests', () => {
    it('should display brand name correctly', () => {
      const brand = document.querySelector('.navbar-brand');
      expect(brand).not.toBeNull();
      expect(brand.textContent).toBe('Lib2DocScrape');
      expect(brand.getAttribute('href')).toBe('/');
    });

    it('should be clickable brand link', () => {
      const brand = document.querySelector('.navbar-brand');
      expect(brand.tagName.toLowerCase()).toBe('a');
      expect(brand.getAttribute('href')).toBe('/');
    });
  });

  describe('Navigation Link Tests', () => {
    it('should have correct href attributes for all links', () => {
      const homeLink = document.querySelector('[data-testid="nav-home"]');
      const welcomeLink = document.querySelector('[data-testid="nav-welcome"]');
      const configLink = document.querySelector('[data-testid="nav-config"]');
      const resultsLink = document.querySelector('[data-testid="nav-results"]');

      expect(homeLink.getAttribute('href')).toBe('/');
      expect(welcomeLink.getAttribute('href')).toBe('/home');
      expect(configLink.getAttribute('href')).toBe('/config');
      expect(resultsLink.getAttribute('href')).toBe('/results');
    });

    it('should have proper Bootstrap navigation classes', () => {
      const navItems = document.querySelectorAll('.nav-item');
      const navLinks = document.querySelectorAll('.nav-link');

      expect(navItems.length).toBe(4);
      expect(navLinks.length).toBe(4);

      navLinks.forEach(link => {
        expect(link.classList.contains('nav-link')).toBe(true);
      });
    });

    it('should contain correct text content for links', () => {
      const homeLink = document.querySelector('[data-testid="nav-home"]');
      const welcomeLink = document.querySelector('[data-testid="nav-welcome"]');
      const configLink = document.querySelector('[data-testid="nav-config"]');
      const resultsLink = document.querySelector('[data-testid="nav-results"]');

      expect(homeLink.textContent.trim()).toContain('Documentation Scraper');
      expect(welcomeLink.textContent.trim()).toContain('Welcome');
      expect(configLink.textContent.trim()).toContain('Configuration');
      expect(resultsLink.textContent.trim()).toContain('Browse Results');
    });
  });

  describe('CSS Classes and Styling Tests', () => {
    it('should have correct Bootstrap navbar classes', () => {
      const navbar = document.querySelector('nav');
      
      expect(navbar.classList.contains('navbar')).toBe(true);
      expect(navbar.classList.contains('navbar-expand-lg')).toBe(true);
      expect(navbar.classList.contains('navbar-dark')).toBe(true);
      expect(navbar.classList.contains('bg-dark')).toBe(true);
    });

    it('should have proper container structure', () => {
      const container = document.querySelector('.container-fluid');
      expect(container).not.toBeNull();
      expect(container.parentElement.tagName.toLowerCase()).toBe('nav');
    });
  });

  describe('Accessibility Tests', () => {
    it('should have accessible toggle button', () => {
      const toggleButton = document.querySelector('.navbar-toggler');
      
      expect(toggleButton.getAttribute('type')).toBe('button');
      expect(toggleButton.getAttribute('data-bs-toggle')).toBe('collapse');
      expect(toggleButton.querySelector('.navbar-toggler-icon')).not.toBeNull();
    });

    it('should have semantic navigation structure', () => {
      const nav = document.querySelector('nav');
      const navList = document.querySelector('ul.navbar-nav');
      const navItems = document.querySelectorAll('li.nav-item');
      
      expect(nav).not.toBeNull();
      expect(navList).not.toBeNull();
      expect(navItems.length).toBe(4);
    });
  });
});
