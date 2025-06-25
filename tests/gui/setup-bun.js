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
if (!global.fetch) {
  global.fetch = () => Promise.resolve({ 
    ok: true, 
    json: () => Promise.resolve({}),
    text: () => Promise.resolve(''),
    status: 200
  });
}

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
  Modal: class {
    constructor() {}
    show() {}
    hide() {}
  },
  Tooltip: class {
    constructor() {}
    show() {}
    hide() {}
  },
  Collapse: class {
    constructor() {}
    show() {}
    hide() {}
  }
};

// Mock localStorage
const localStorageMock = {
  getItem: () => null,
  setItem: () => {},
  removeItem: () => {},
  clear: () => {},
};

// Mock sessionStorage  
const sessionStorageMock = {
  getItem: () => null,
  setItem: () => {},
  removeItem: () => {},
  clear: () => {},
};

// Set up storage mocks only if they don't exist
if (typeof window !== 'undefined') {
  if (!window.localStorage) {
    Object.defineProperty(window, 'localStorage', {
      value: localStorageMock,
      writable: true
    });
  }
  
  if (!window.sessionStorage) {
    Object.defineProperty(window, 'sessionStorage', {
      value: sessionStorageMock,
      writable: true
    });
  }

  // Mock window.location if needed
  if (!window.location) {
    Object.defineProperty(window, 'location', {
      value: {
        href: 'http://localhost:3000',
        pathname: '/',
        search: '',
        hash: '',
        origin: 'http://localhost:3000',
        reload: () => {},
        assign: () => {},
        replace: () => {}
      },
      writable: true
    });
  }
}

// Global test utilities
global.sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms));

global.waitForElement = async (selector, timeout = 5000) => {
  const start = Date.now();
  while (Date.now() - start < timeout) {
    const element = document.querySelector(selector);
    if (element) return element;
    await sleep(50);
  }
  throw new Error(`Element ${selector} not found within ${timeout}ms`);
};

global.simulateEvent = (element, eventType, options = {}) => {
  const event = new Event(eventType, { bubbles: true, ...options });
  element.dispatchEvent(event);
  return event;
};

global.simulateClick = (element) => {
  return simulateEvent(element, 'click');
};

global.simulateSubmit = (form) => {
  return simulateEvent(form, 'submit');
};

global.simulateChange = (input, value) => {
  input.value = value;
  return simulateEvent(input, 'change');
};

global.simulateInput = (input, value) => {
  input.value = value;
  return simulateEvent(input, 'input');
};

// Mock XMLHttpRequest
global.XMLHttpRequest = class {
  constructor() {
    this.readyState = 0;
    this.status = 200;
    this.responseText = '';
    this.response = '';
  }
  
  open() {}
  send() {
    setTimeout(() => {
      this.readyState = 4;
      if (this.onreadystatechange) this.onreadystatechange();
    }, 0);
  }
  setRequestHeader() {}
};

// Mock performance API
if (!global.performance) {
  global.performance = {
    now: () => Date.now(),
    mark: () => {},
    measure: () => {},
    getEntriesByType: () => [],
    getEntriesByName: () => []
  };
}

// Mock IntersectionObserver
global.IntersectionObserver = class {
  constructor(callback) {
    this.callback = callback;
  }
  observe() {}
  unobserve() {}
  disconnect() {}
};

// Mock ResizeObserver
global.ResizeObserver = class {
  constructor(callback) {
    this.callback = callback;
  }
  observe() {}
  unobserve() {}
  disconnect() {}
};

// Mock MutationObserver
global.MutationObserver = class {
  constructor(callback) {
    this.callback = callback;
  }
  observe() {}
  disconnect() {}
};

// Test Helper Functions
global.simulateInput = (element, value) => {
  element.value = value;
  element.dispatchEvent(new Event('input', { bubbles: true }));
  element.dispatchEvent(new Event('change', { bubbles: true }));
};

global.simulateSubmit = (form) => {
  const event = new Event('submit', { bubbles: true, cancelable: true });
  form.dispatchEvent(event);
};

global.simulateClick = (element) => {
  const event = new Event('click', { bubbles: true, cancelable: true });
  element.dispatchEvent(event);
};

global.waitFor = async (condition, timeout = 1000) => {
  const start = Date.now();
  while (Date.now() - start < timeout) {
    if (await condition()) return true;
    await new Promise(resolve => setTimeout(resolve, 10));
  }
  throw new Error('Condition not met within timeout');
};

console.log('✅ GUI test environment setup complete');
