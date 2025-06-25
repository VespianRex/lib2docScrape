/**
 * Bun Test Setup for GUI Testing
 * 
 * This file sets up the testing environment for comprehensive GUI testing
 * of the lib2docScrape application using Bun's test runner.
 */

// Import Happy DOM for browser-like environment
import { GlobalRegistrator } from '@happy-dom/global-registrator';

// Register DOM globals
GlobalRegistrator.register();

// Mock fetch for API calls
global.fetch = fetch || (() => Promise.resolve({ ok: true, json: () => ({}) }));

// Mock WebSocket for real-time features
class MockWebSocket {
  constructor(url) {
    this.url = url;
    this.readyState = 1; // OPEN
    this.onopen = null;
    this.onmessage = null;
    this.onclose = null;
    this.onerror = null;
  }
  
  send(data) {
    // Mock send functionality
  }
  
  close() {
    this.readyState = 3; // CLOSED
    if (this.onclose) this.onclose();
  }
}

global.WebSocket = MockWebSocket;

// Mock Bootstrap components
global.bootstrap = {
    Modal: jest.fn().mockImplementation(() => ({
        show: jest.fn(),
        hide: jest.fn(),
        toggle: jest.fn()
    })),
    Tooltip: jest.fn().mockImplementation(() => ({
        show: jest.fn(),
        hide: jest.fn(),
        toggle: jest.fn()
    })),
    Collapse: jest.fn().mockImplementation(() => ({
        show: jest.fn(),
        hide: jest.fn(),
        toggle: jest.fn()
    }))
};

// Mock localStorage
const localStorageMock = {
    getItem: jest.fn(),
    setItem: jest.fn(),
    removeItem: jest.fn(),
    clear: jest.fn(),
};
global.localStorage = localStorageMock;

// Mock sessionStorage
const sessionStorageMock = {
    getItem: jest.fn(),
    setItem: jest.fn(),
    removeItem: jest.fn(),
    clear: jest.fn(),
};
global.sessionStorage = sessionStorageMock;

// Mock window.location
delete window.location;
window.location = {
    href: 'http://localhost:3000',
    origin: 'http://localhost:3000',
    pathname: '/',
    search: '',
    hash: '',
    assign: jest.fn(),
    replace: jest.fn(),
    reload: jest.fn()
};

// Mock window.alert, confirm, prompt
global.alert = jest.fn();
global.confirm = jest.fn(() => true);
global.prompt = jest.fn(() => 'test');

// Mock console methods to reduce noise in tests
global.console = {
    ...console,
    log: jest.fn(),
    debug: jest.fn(),
    info: jest.fn(),
    warn: jest.fn(),
    error: jest.fn()
};

// Setup DOM environment
beforeEach(() => {
    // Clear all mocks before each test
    jest.clearAllMocks();
    
    // Reset fetch mock
    fetch.resetMocks();
    
    // Clear localStorage and sessionStorage
    localStorageMock.clear();
    sessionStorageMock.clear();
    
    // Reset DOM
    document.body.innerHTML = '';
    document.head.innerHTML = '';
    
    // Add basic HTML structure
    document.body.innerHTML = `
        <div id="app">
            <!-- Test content will be inserted here -->
        </div>
    `;
});

// Cleanup after each test
afterEach(() => {
    // Clean up any remaining timers
    jest.runOnlyPendingTimers();
    jest.useRealTimers();
    
    // Clean up WebSocket mocks
    WS.clean();
});

// Global test utilities
global.testUtils = {
    // Create a mock HTML template
    createMockTemplate: (templateName, content) => {
        const template = document.createElement('div');
        template.innerHTML = content;
        template.setAttribute('data-template', templateName);
        return template;
    },
    
    // Simulate user interaction
    simulateClick: (element) => {
        const event = new MouseEvent('click', {
            view: window,
            bubbles: true,
            cancelable: true
        });
        element.dispatchEvent(event);
    },
    
    // Simulate form submission
    simulateSubmit: (form) => {
        const event = new Event('submit', {
            bubbles: true,
            cancelable: true
        });
        form.dispatchEvent(event);
    },
    
    // Simulate input change
    simulateInput: (input, value) => {
        input.value = value;
        const event = new Event('input', {
            bubbles: true,
            cancelable: true
        });
        input.dispatchEvent(event);
    },
    
    // Wait for async operations
    waitFor: (callback, timeout = 1000) => {
        return new Promise((resolve, reject) => {
            const startTime = Date.now();
            const check = () => {
                try {
                    const result = callback();
                    if (result) {
                        resolve(result);
                    } else if (Date.now() - startTime > timeout) {
                        reject(new Error('Timeout waiting for condition'));
                    } else {
                        setTimeout(check, 10);
                    }
                } catch (error) {
                    if (Date.now() - startTime > timeout) {
                        reject(error);
                    } else {
                        setTimeout(check, 10);
                    }
                }
            };
            check();
        });
    }
};

// Mock configuration presets for testing
global.mockConfigPresets = {
    'default': {
        maxDepth: 5,
        maxPages: 100,
        outputFormat: 'markdown',
        description: 'Balanced configuration for most use cases'
    },
    'comprehensive': {
        maxDepth: 3,
        maxPages: 50,
        outputFormat: 'markdown',
        description: 'Maximum coverage with comprehensive scraping'
    },
    'performance': {
        maxDepth: 2,
        maxPages: 20,
        outputFormat: 'markdown',
        description: 'Fast scraping with minimal resource usage'
    }
};

// Mock backend descriptions for testing
global.mockBackendDescriptions = {
    'http': 'Fast and reliable for most documentation sites',
    'crawl4ai': 'AI-powered crawling with intelligent content extraction',
    'lightpanda': 'JavaScript support for dynamic content',
    'playwright': 'Full browser automation for complex sites',
    'scrapy': 'High-performance crawling for large-scale operations',
    'file': 'Local file system processing'
};

// Mock API responses for testing
global.mockApiResponses = {
    benchmark: {
        results: [
            { backend: 'HTTP', speed: 2.3, success: 95, size: '1.2 MB', memory: '45 MB' },
            { backend: 'Crawl4AI', speed: 4.1, success: 98, size: '1.8 MB', memory: '120 MB' },
            { backend: 'Lightpanda', speed: 3.2, success: 92, size: '1.5 MB', memory: '80 MB' }
        ]
    },
    scraping: {
        progress: {
            pages: 15,
            depth: 2,
            success_rate: 95,
            quality_score: 85,
            completion: '2 minutes'
        }
    }
};

console.log('🧪 GUI Testing environment initialized');
