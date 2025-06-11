/**
 * Bun Test Setup for GUI Testing
 *
 * Modern, fast test setup using Bun's built-in test runner and happy-dom
 */

import { beforeEach, afterEach } from "bun:test";

// Use Bun's built-in DOM environment
// No need for external DOM library with Bun

// Mock Bootstrap components
(globalThis as any).bootstrap = {
  Modal: class MockModal {
    constructor(element: Element) {}
    show() {}
    hide() {}
    toggle() {}
    static getInstance(element: Element) {
      return new MockModal(element);
    }
  },
  Tooltip: class MockTooltip {
    constructor(element: Element) {}
    show() {}
    hide() {}
    toggle() {}
  },
  Collapse: class MockCollapse {
    constructor(element: Element) {}
    show() {}
    hide() {}
    toggle() {}
  }
};

// Mock localStorage
const localStorageMock = {
  getItem: (key: string) => null,
  setItem: (key: string, value: string) => {},
  removeItem: (key: string) => {},
  clear: () => {},
  length: 0,
  key: (index: number) => null
};

Object.defineProperty(globalThis, 'localStorage', {
  value: localStorageMock,
  writable: true
});

// Mock sessionStorage
Object.defineProperty(globalThis, 'sessionStorage', {
  value: { ...localStorageMock },
  writable: true
});

// Mock fetch
(globalThis as any).fetch = async (url: string, options?: any) => {
  return {
    ok: true,
    status: 200,
    json: async () => ({}),
    text: async () => "",
    blob: async () => new Blob(),
  };
};

// Mock WebSocket
(globalThis as any).WebSocket = class MockWebSocket {
  static CONNECTING = 0;
  static OPEN = 1;
  static CLOSING = 2;
  static CLOSED = 3;

  readyState = MockWebSocket.CONNECTING;
  onopen: ((event: Event) => void) | null = null;
  onclose: ((event: CloseEvent) => void) | null = null;
  onmessage: ((event: MessageEvent) => void) | null = null;
  onerror: ((event: Event) => void) | null = null;

  constructor(url: string) {
    setTimeout(() => {
      this.readyState = MockWebSocket.OPEN;
      this.onopen?.(new Event('open'));
    }, 0);
  }

  send(data: string) {}
  close() {
    this.readyState = MockWebSocket.CLOSED;
  }
};

// Mock window.alert, confirm, prompt
(globalThis as any).alert = (message: string) => {};
(globalThis as any).confirm = (message: string) => true;
(globalThis as any).prompt = (message: string, defaultValue?: string) => defaultValue || 'test';

// Mock console methods to reduce noise
const originalConsole = console;
(globalThis as any).console = {
  ...originalConsole,
  log: () => {},
  debug: () => {},
  info: () => {},
  warn: () => {},
  error: originalConsole.error // Keep errors for debugging
};

// Test utilities
export const testUtils = {
  // Create a mock HTML template
  createMockTemplate: (templateName: string, content: string) => {
    const template = document.createElement('div');
    template.innerHTML = content;
    template.setAttribute('data-template', templateName);
    return template;
  },

  // Simulate user interaction
  simulateClick: (element: Element) => {
    const event = new MouseEvent('click', {
      view: window,
      bubbles: true,
      cancelable: true
    });
    element.dispatchEvent(event);
  },

  // Simulate form submission
  simulateSubmit: (form: HTMLFormElement) => {
    const event = new Event('submit', {
      bubbles: true,
      cancelable: true
    });
    form.dispatchEvent(event);
  },

  // Simulate input change
  simulateInput: (input: HTMLInputElement, value: string) => {
    input.value = value;
    const event = new Event('input', {
      bubbles: true,
      cancelable: true
    });
    input.dispatchEvent(event);
  },

  // Wait for async operations
  waitFor: async (callback: () => boolean, timeout = 1000): Promise<void> => {
    const startTime = Date.now();
    while (Date.now() - startTime < timeout) {
      if (callback()) {
        return;
      }
      await new Promise(resolve => setTimeout(resolve, 10));
    }
    throw new Error('Timeout waiting for condition');
  }
};

// Mock configuration presets for testing
export const mockConfigPresets = {
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
export const mockBackendDescriptions = {
  'http': 'Fast and reliable for most documentation sites',
  'crawl4ai': 'AI-powered crawling with intelligent content extraction',
  'lightpanda': 'JavaScript support for dynamic content',
  'playwright': 'Full browser automation for complex sites',
  'scrapy': 'High-performance crawling for large-scale operations',
  'file': 'Local file system processing'
};

// Mock API responses for testing
export const mockApiResponses = {
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

// Setup and teardown for each test
beforeEach(() => {
  // Clear DOM
  document.body.innerHTML = '';
  document.head.innerHTML = '';

  // Reset mocks
  localStorageMock.clear();

  // Add basic HTML structure
  document.body.innerHTML = `
    <div id="app">
      <!-- Test content will be inserted here -->
    </div>
  `;
});

afterEach(() => {
  // Clean up any remaining timers
  // Bun handles this automatically, but we can add custom cleanup here
});

console.log('🧪 Bun GUI Testing environment initialized');
