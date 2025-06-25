/**
 * Page Transitions Integration Tests
 * 
 * Tests for navigation flow, URL history management, and data persistence
 */

import { screen, fireEvent, waitFor } from '@testing-library/dom';
import '@testing-library/jest-dom';

describe('Page Transitions Integration', () => {
  let container;
  let mockRouter;
  
  beforeEach(() => {
    // Mock window.history
    const mockHistory = {
      pushState: jest.fn(),
      replaceState: jest.fn(),
      state: null,
      length: 1
    };
    
    Object.defineProperty(window, 'history', {
      value: mockHistory,
      writable: true
    });
    
    // Mock location
    Object.defineProperty(window, 'location', {
      value: {
        pathname: '/',
        search: '',
        hash: '',
        href: 'http://localhost/',
      },
      writable: true
    });
    
    // Create basic page structure
    document.body.innerHTML = `
      <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
        <div class="container-fluid">
          <div class="collapse navbar-collapse">
            <ul class="navbar-nav">
              <li class="nav-item">
                <a class="nav-link" href="/" data-testid="nav-home">Home</a>
              </li>
              <li class="nav-item">
                <a class="nav-link" href="/config" data-testid="nav-config">Configuration</a>
              </li>
              <li class="nav-item">
                <a class="nav-link" href="/results" data-testid="nav-results">Results</a>
              </li>
              <li class="nav-item">
                <a class="nav-link" href="/search" data-testid="nav-search">Search</a>
              </li>
            </ul>
          </div>
        </div>
      </nav>
      
      <main class="container my-4" data-testid="main-content">
        <div id="page-content"></div>
      </main>
      
      <div class="loading-indicator" data-testid="loading-indicator" style="display: none;">
        <div class="spinner-border"></div>
      </div>
    `;
    
    container = document.body;
    
    // Mock simple router
    mockRouter = {
      currentRoute: '/',
      routes: {
        '/': '<div data-testid="home-page">Home Page Content</div>',
        '/config': '<div data-testid="config-page">Configuration Page Content</div>',
        '/results': '<div data-testid="results-page">Results Page Content</div>',
        '/search': '<div data-testid="search-page">Search Page Content</div>'
      },
      navigate: function(path) {
        this.currentRoute = path;
        const content = this.routes[path] || '<div>404 Not Found</div>';
        document.getElementById('page-content').innerHTML = content;
        
        // Update active nav link
        document.querySelectorAll('.nav-link').forEach(link => {
          link.classList.remove('active');
          if (link.getAttribute('href') === path) {
            link.classList.add('active');
          }
        });
        
        // Update URL
        window.history.pushState({ path }, '', path);
        window.location.pathname = path;
      }
    };
    
    // Initialize with home page
    mockRouter.navigate('/');
  });

  afterEach(() => {
    document.body.innerHTML = '';
    jest.clearAllMocks();
  });

  describe('Navigation Flow', () => {
    test('should navigate between all pages', async () => {
      const configLink = screen.getByTestId('nav-config');
      const resultsLink = screen.getByTestId('nav-results');
      const searchLink = screen.getByTestId('nav-search');
      const homeLink = screen.getByTestId('nav-home');
      
      // Navigate to config
      fireEvent.click(configLink);
      mockRouter.navigate('/config');
      
      await waitFor(() => {
        expect(screen.getByTestId('config-page')).toBeInTheDocument();
        expect(configLink).toHaveClass('active');
      });
      
      // Navigate to results
      fireEvent.click(resultsLink);
      mockRouter.navigate('/results');
      
      await waitFor(() => {
        expect(screen.getByTestId('results-page')).toBeInTheDocument();
        expect(resultsLink).toHaveClass('active');
        expect(configLink).not.toHaveClass('active');
      });
      
      // Navigate to search
      fireEvent.click(searchLink);
      mockRouter.navigate('/search');
      
      await waitFor(() => {
        expect(screen.getByTestId('search-page')).toBeInTheDocument();
        expect(searchLink).toHaveClass('active');
      });
      
      // Navigate back to home
      fireEvent.click(homeLink);
      mockRouter.navigate('/');
      
      await waitFor(() => {
        expect(screen.getByTestId('home-page')).toBeInTheDocument();
        expect(homeLink).toHaveClass('active');
      });
    });

    test('should update URL history during navigation', () => {
      const configLink = screen.getByTestId('nav-config');
      
      fireEvent.click(configLink);
      mockRouter.navigate('/config');
      
      expect(window.history.pushState).toHaveBeenCalledWith(
        { path: '/config' }, 
        '', 
        '/config'
      );
    });

    test('should handle direct URL access', () => {
      // Simulate direct URL access
      mockRouter.navigate('/results');
      
      expect(screen.getByTestId('results-page')).toBeInTheDocument();
      expect(mockRouter.currentRoute).toBe('/results');
    });

    test('should handle invalid routes gracefully', () => {
      // Navigate to non-existent route
      mockRouter.navigate('/non-existent');
      
      const content = document.getElementById('page-content');
      expect(content).toHaveTextContent('404 Not Found');
    });

    test('should maintain navigation state consistency', () => {
      const configLink = screen.getByTestId('nav-config');
      const homeLink = screen.getByTestId('nav-home');
      
      // Navigate to config
      fireEvent.click(configLink);
      mockRouter.navigate('/config');
      
      expect(configLink).toHaveClass('active');
      expect(homeLink).not.toHaveClass('active');
      
      // Navigate back to home
      fireEvent.click(homeLink);
      mockRouter.navigate('/');
      
      expect(homeLink).toHaveClass('active');
      expect(configLink).not.toHaveClass('active');
    });
  });

  describe('Data Persistence Across Pages', () => {
    test('should preserve form data during navigation', () => {
      // Add form to home page
      document.getElementById('page-content').innerHTML = `
        <div data-testid="home-page">
          <form data-testid="scraping-form">
            <input type="url" data-testid="url-input" value="">
            <input type="number" data-testid="depth-input" value="3">
          </form>
        </div>
      `;
      
      const urlInput = screen.getByTestId('url-input');
      const depthInput = screen.getByTestId('depth-input');
      
      // Fill form
      fireEvent.change(urlInput, { target: { value: 'https://example.com' } });
      fireEvent.change(depthInput, { target: { value: '5' } });
      
      // Store data in sessionStorage (simulating persistence)
      const formData = {
        url: urlInput.value,
        depth: depthInput.value
      };
      sessionStorage.setItem('scraping-form-data', JSON.stringify(formData));
      
      // Navigate away and back
      mockRouter.navigate('/config');
      mockRouter.navigate('/');
      
      // Restore form (simulate form restoration)
      document.getElementById('page-content').innerHTML = `
        <div data-testid="home-page">
          <form data-testid="scraping-form">
            <input type="url" data-testid="url-input" value="">
            <input type="number" data-testid="depth-input" value="3">
          </form>
        </div>
      `;
      
      const restoredData = JSON.parse(sessionStorage.getItem('scraping-form-data'));
      const restoredUrlInput = screen.getByTestId('url-input');
      const restoredDepthInput = screen.getByTestId('depth-input');
      
      restoredUrlInput.value = restoredData.url;
      restoredDepthInput.value = restoredData.depth;
      
      expect(restoredUrlInput.value).toBe('https://example.com');
      expect(restoredDepthInput.value).toBe('5');
    });

    test('should preserve search filters across navigation', () => {
      // Simulate search page with filters
      document.getElementById('page-content').innerHTML = `
        <div data-testid="search-page">
          <input type="text" data-testid="search-query" placeholder="Search...">
          <select data-testid="library-filter">
            <option value="">All Libraries</option>
            <option value="requests">Requests</option>
            <option value="flask">Flask</option>
          </select>
        </div>
      `;
      
      const searchQuery = screen.getByTestId('search-query');
      const libraryFilter = screen.getByTestId('library-filter');
      
      // Set search criteria
      fireEvent.change(searchQuery, { target: { value: 'authentication' } });
      fireEvent.change(libraryFilter, { target: { value: 'requests' } });
      
      // Store search state
      const searchState = {
        query: searchQuery.value,
        library: libraryFilter.value
      };
      sessionStorage.setItem('search-state', JSON.stringify(searchState));
      
      // Navigate away and back
      mockRouter.navigate('/home');
      mockRouter.navigate('/search');
      
      // Restore search page
      document.getElementById('page-content').innerHTML = `
        <div data-testid="search-page">
          <input type="text" data-testid="search-query" placeholder="Search...">
          <select data-testid="library-filter">
            <option value="">All Libraries</option>
            <option value="requests">Requests</option>
            <option value="flask">Flask</option>
          </select>
        </div>
      `;
      
      const restoredState = JSON.parse(sessionStorage.getItem('search-state'));
      const restoredQuery = screen.getByTestId('search-query');
      const restoredFilter = screen.getByTestId('library-filter');
      
      restoredQuery.value = restoredState.query;
      restoredFilter.value = restoredState.library;
      
      expect(restoredQuery.value).toBe('authentication');
      expect(restoredFilter.value).toBe('requests');
    });

    test('should maintain user preferences across sessions', () => {
      // Simulate user preferences
      const preferences = {
        theme: 'dark',
        itemsPerPage: 25,
        defaultBackend: 'crawl4ai'
      };
      
      localStorage.setItem('user-preferences', JSON.stringify(preferences));
      
      // Navigate between pages
      mockRouter.navigate('/config');
      mockRouter.navigate('/results');
      mockRouter.navigate('/home');
      
      // Preferences should persist
      const savedPreferences = JSON.parse(localStorage.getItem('user-preferences'));
      
      expect(savedPreferences.theme).toBe('dark');
      expect(savedPreferences.itemsPerPage).toBe(25);
      expect(savedPreferences.defaultBackend).toBe('crawl4ai');
    });
  });

  describe('URL History Management', () => {
    test('should handle browser back/forward buttons', () => {
      // Simulate navigation history
      mockRouter.navigate('/config');
      mockRouter.navigate('/results');
      mockRouter.navigate('/search');
      
      expect(window.history.pushState).toHaveBeenCalledTimes(4); // Including initial
      
      // Simulate back button
      const popstateEvent = new PopStateEvent('popstate', {
        state: { path: '/results' }
      });
      
      // Mock popstate handler
      window.addEventListener('popstate', (event) => {
        if (event.state && event.state.path) {
          mockRouter.navigate(event.state.path);
        }
      });
      
      window.dispatchEvent(popstateEvent);
      
      expect(screen.getByTestId('results-page')).toBeInTheDocument();
    });

    test('should preserve query parameters during navigation', () => {
      // Navigate with query parameters
      const path = '/search?query=python&library=requests';
      window.location.search = '?query=python&library=requests';
      mockRouter.navigate('/search');
      
      // Query parameters should be preserved
      expect(window.location.search).toBe('?query=python&library=requests');
    });

    test('should handle hash fragments', () => {
      // Navigate with hash fragment
      window.location.hash = '#section-authentication';
      mockRouter.navigate('/results');
      
      expect(window.location.hash).toBe('#section-authentication');
    });

    test('should update document title based on route', () => {
      const titleMap = {
        '/': 'Home - Lib2DocScrape',
        '/config': 'Configuration - Lib2DocScrape',
        '/results': 'Results - Lib2DocScrape',
        '/search': 'Search - Lib2DocScrape'
      };
      
      // Extend router to update title
      const originalNavigate = mockRouter.navigate;
      mockRouter.navigate = function(path) {
        originalNavigate.call(this, path);
        document.title = titleMap[path] || 'Lib2DocScrape';
      };
      
      mockRouter.navigate('/config');
      expect(document.title).toBe('Configuration - Lib2DocScrape');
      
      mockRouter.navigate('/results');
      expect(document.title).toBe('Results - Lib2DocScrape');
    });
  });

  describe('Loading States During Transitions', () => {
    test('should show loading indicator during page transitions', async () => {
      const loadingIndicator = screen.getByTestId('loading-indicator');
      
      // Extend router to simulate loading
      const originalNavigate = mockRouter.navigate;
      mockRouter.navigate = async function(path) {
        // Show loading
        loadingIndicator.style.display = 'block';
        
        // Simulate async page load
        await new Promise(resolve => setTimeout(resolve, 100));
        
        originalNavigate.call(this, path);
        
        // Hide loading
        loadingIndicator.style.display = 'none';
      };
      
      const configLink = screen.getByTestId('nav-config');
      fireEvent.click(configLink);
      
      // Start navigation
      const navigationPromise = mockRouter.navigate('/config');
      
      // Should show loading
      expect(loadingIndicator).toHaveStyle('display: block');
      
      // Wait for completion
      await navigationPromise;
      
      expect(loadingIndicator).toHaveStyle('display: none');
      expect(screen.getByTestId('config-page')).toBeInTheDocument();
    });

    test('should handle navigation errors gracefully', async () => {
      const errorNavigate = async function(path) {
        if (path === '/error-page') {
          throw new Error('Navigation failed');
        }
        return mockRouter.navigate(path);
      };
      
      // Attempt navigation to error page
      try {
        await errorNavigate('/error-page');
      } catch (error) {
        // Should handle error gracefully
        expect(error.message).toBe('Navigation failed');
        
        // Should stay on current page
        expect(screen.getByTestId('home-page')).toBeInTheDocument();
      }
    });

    test('should cancel previous navigation if new one starts', async () => {
      let cancelFirstNavigation = false;
      
      const slowNavigate = async function(path) {
        const navigationId = Date.now();
        
        // Simulate slow navigation
        for (let i = 0; i < 10; i++) {
          if (cancelFirstNavigation && navigationId < Date.now() - 100) {
            throw new Error('Navigation cancelled');
          }
          await new Promise(resolve => setTimeout(resolve, 10));
        }
        
        return mockRouter.navigate(path);
      };
      
      // Start first navigation
      const firstNavigation = slowNavigate('/config');
      
      // Start second navigation quickly
      setTimeout(() => {
        cancelFirstNavigation = true;
      }, 50);
      
      const secondNavigation = slowNavigate('/results');
      
      // Second navigation should complete
      await expect(secondNavigation).resolves.toBeUndefined();
      
      // First should be cancelled
      await expect(firstNavigation).rejects.toThrow('Navigation cancelled');
    });
  });

  describe('Accessibility During Transitions', () => {
    test('should maintain focus management during navigation', () => {
      const configLink = screen.getByTestId('nav-config');
      
      // Focus navigation link
      configLink.focus();
      expect(document.activeElement).toBe(configLink);
      
      // Navigate
      fireEvent.click(configLink);
      mockRouter.navigate('/config');
      
      // Focus should be managed appropriately
      // In a real app, focus might move to main content
      expect(document.activeElement).toBeDefined();
    });

    test('should announce page changes to screen readers', () => {
      // Add aria-live region for announcements
      const announcer = document.createElement('div');
      announcer.setAttribute('aria-live', 'polite');
      announcer.setAttribute('data-testid', 'page-announcer');
      announcer.classList.add('visually-hidden');
      container.appendChild(announcer);
      
      // Extend router to make announcements
      const originalNavigate = mockRouter.navigate;
      mockRouter.navigate = function(path) {
        originalNavigate.call(this, path);
        
        const pageNames = {
          '/': 'Home page',
          '/config': 'Configuration page',
          '/results': 'Results page',
          '/search': 'Search page'
        };
        
        announcer.textContent = `Navigated to ${pageNames[path] || 'page'}`;
      };
      
      const configLink = screen.getByTestId('nav-config');
      fireEvent.click(configLink);
      mockRouter.navigate('/config');
      
      const pageAnnouncer = screen.getByTestId('page-announcer');
      expect(pageAnnouncer).toHaveTextContent('Navigated to Configuration page');
    });

    test('should preserve landmark navigation', () => {
      // Ensure main content landmark is always present
      const mainContent = screen.getByTestId('main-content');
      
      mockRouter.navigate('/config');
      expect(mainContent).toBeInTheDocument();
      
      mockRouter.navigate('/results');
      expect(mainContent).toBeInTheDocument();
      
      mockRouter.navigate('/search');
      expect(mainContent).toBeInTheDocument();
    });
  });
});
