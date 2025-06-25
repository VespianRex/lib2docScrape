/**
 * Main JavaScript file for lib2docScrape
 * Handles common functionality across all pages
 */

// Global state
const state = {
  websocket: null,
  isConnected: false,
  connectionRetries: 0,
  maxRetries: 5,
  retryInterval: 2000, // ms
};

// Initialize the application
document.addEventListener('DOMContentLoaded', () => {
  initializeWebSocket();
  setupGlobalEventListeners();
  setupThemeToggle();
});

/**
 * Initialize WebSocket connection
 */
function initializeWebSocket() {
  if (!window.WebSocket) {
    console.error('WebSocket not supported by this browser');
    return;
  }

  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const wsUrl = `${protocol}//${window.location.host}/ws`;
  
  try {
    state.websocket = new WebSocket(wsUrl);
    
    state.websocket.onopen = (event) => {
      console.log('WebSocket connection established');
      state.isConnected = true;
      state.connectionRetries = 0;
      
      // Notify any components that need to know about the connection
      document.dispatchEvent(new CustomEvent('websocket-connected'));
      
      // Send initial message to confirm connection
      sendWebSocketMessage({
        type: 'connection',
        data: {
          page: window.location.pathname,
          timestamp: new Date().toISOString()
        }
      });
    };
    
    state.websocket.onclose = (event) => {
      console.log('WebSocket connection closed');
      state.isConnected = false;
      
      // Attempt to reconnect
      if (state.connectionRetries < state.maxRetries) {
        state.connectionRetries++;
        console.log(`Attempting to reconnect (${state.connectionRetries}/${state.maxRetries})...`);
        setTimeout(initializeWebSocket, state.retryInterval);
      } else {
        console.error('Maximum WebSocket reconnection attempts reached');
        showNotification('Connection lost. Please refresh the page.', 'error');
      }
    };
    
    state.websocket.onerror = (error) => {
      console.error('WebSocket error:', error);
      showNotification('Connection error occurred', 'error');
    };
    
    state.websocket.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        handleWebSocketMessage(message);
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
      }
    };
  } catch (error) {
    console.error('Error initializing WebSocket:', error);
  }
}

/**
 * Send a message through the WebSocket connection
 * @param {Object} message - The message to send
 */
function sendWebSocketMessage(message) {
  if (state.isConnected && state.websocket) {
    state.websocket.send(JSON.stringify(message));
  } else {
    console.warn('Cannot send message: WebSocket not connected');
  }
}

/**
 * Handle incoming WebSocket messages
 * @param {Object} message - The received message
 */
function handleWebSocketMessage(message) {
  console.log('Received WebSocket message:', message);
  
  switch (message.type) {
    case 'notification':
      showNotification(message.message, message.level || 'info');
      break;
    
    case 'update':
      // Dispatch custom event for components to handle
      document.dispatchEvent(new CustomEvent('data-update', { 
        detail: message.data 
      }));
      break;
    
    case 'scraping_progress':
      document.dispatchEvent(new CustomEvent('scraping-progress', { 
        detail: message.data 
      }));
      break;
      
    default:
      // Dispatch a generic event for any other message types
      document.dispatchEvent(new CustomEvent(`websocket-${message.type}`, {
        detail: message.data
      }));
  }
}

/**
 * Set up global event listeners
 */
function setupGlobalEventListeners() {
  // Handle form submissions with AJAX
  document.querySelectorAll('form[data-ajax="true"]').forEach(form => {
    form.addEventListener('submit', handleAjaxFormSubmit);
  });
  
  // Handle loading state for buttons
  document.querySelectorAll('[data-loading-text]').forEach(button => {
    button.addEventListener('click', handleLoadingButton);
  });
}

/**
 * Handle AJAX form submissions
 * @param {Event} event - The form submit event
 */
function handleAjaxFormSubmit(event) {
  event.preventDefault();
  
  const form = event.target;
  const url = form.action;
  const method = form.method.toUpperCase();
  const formData = new FormData(form);
  
  // Show loading state
  const submitButton = form.querySelector('[type="submit"]');
  if (submitButton) {
    const originalText = submitButton.textContent;
    submitButton.disabled = true;
    submitButton.textContent = submitButton.dataset.loadingText || 'Processing...';
  }
  
  // Convert FormData to JSON if needed
  let body;
  if (form.dataset.format === 'json') {
    body = JSON.stringify(Object.fromEntries(formData));
    headers = {
      'Content-Type': 'application/json'
    };
  } else {
    body = formData;
    headers = {};
  }
  
  // Make the request
  fetch(url, {
    method,
    body,
    headers
  })
  .then(response => {
    if (!response.ok) {
      throw new Error(`HTTP error ${response.status}`);
    }
    return response.json();
  })
  .then(data => {
    // Handle success
    if (form.dataset.successMessage) {
      showNotification(form.dataset.successMessage, 'success');
    }
    
    // Trigger success event
    form.dispatchEvent(new CustomEvent('ajax-success', { detail: data }));
    
    // Reset form if specified
    if (form.dataset.resetOnSuccess === 'true') {
      form.reset();
    }
  })
  .catch(error => {
    console.error('Form submission error:', error);
    showNotification('An error occurred while submitting the form', 'error');
    
    // Trigger error event
    form.dispatchEvent(new CustomEvent('ajax-error', { detail: error }));
  })
  .finally(() => {
    // Restore button state
    if (submitButton) {
      submitButton.disabled = false;
      submitButton.textContent = originalText;
    }
  });
}

/**
 * Handle loading state for buttons
 * @param {Event} event - The click event
 */
function handleLoadingButton(event) {
  const button = event.currentTarget;
  const originalText = button.textContent;
  const loadingText = button.dataset.loadingText || 'Loading...';
  
  button.disabled = true;
  button.textContent = loadingText;
  
  // Restore button after action completes
  document.addEventListener('action-complete', () => {
    button.disabled = false;
    button.textContent = originalText;
  }, { once: true });
}

/**
 * Show a notification to the user
 * @param {string} message - The notification message
 * @param {string} type - The notification type (info, success, warning, error)
 */
function showNotification(message, type = 'info') {
  // Check if we have a notification container
  let container = document.getElementById('notification-container');
  
  // Create one if it doesn't exist
  if (!container) {
    container = document.createElement('div');
    container.id = 'notification-container';
    container.style.position = 'fixed';
    container.style.top = '20px';
    container.style.right = '20px';
    container.style.zIndex = '9999';
    document.body.appendChild(container);
  }
  
  // Create notification element
  const notification = document.createElement('div');
  notification.className = `alert alert-${type} alert-dismissible fade show`;
  notification.role = 'alert';
  
  notification.innerHTML = `
    ${message}
    <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
  `;
  
  // Add to container
  container.appendChild(notification);
  
  // Auto-dismiss after 5 seconds
  setTimeout(() => {
    notification.classList.remove('show');
    setTimeout(() => {
      container.removeChild(notification);
    }, 300);
  }, 5000);
}

/**
 * Set up theme toggle functionality
 */
function setupThemeToggle() {
  const themeToggle = document.getElementById('theme-toggle');
  if (!themeToggle) return;
  
  // Check for saved theme preference or use device preference
  const savedTheme = localStorage.getItem('theme');
  const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
  
  // Set initial theme
  if (savedTheme) {
    document.documentElement.setAttribute('data-bs-theme', savedTheme);
    themeToggle.checked = savedTheme === 'dark';
  } else if (prefersDark) {
    document.documentElement.setAttribute('data-bs-theme', 'dark');
    themeToggle.checked = true;
  }
  
  // Handle theme toggle
  themeToggle.addEventListener('change', () => {
    const newTheme = themeToggle.checked ? 'dark' : 'light';
    document.documentElement.setAttribute('data-bs-theme', newTheme);
    localStorage.setItem('theme', newTheme);
  });
}

// Export functions for use in other modules
window.lib2docScrape = {
  sendWebSocketMessage,
  showNotification,
  state
};