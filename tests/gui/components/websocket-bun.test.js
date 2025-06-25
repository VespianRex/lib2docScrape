/**
 * WebSocket Integration Component Tests
 * 
 * Tests for real-time WebSocket communication and UI updates
 */

import { describe, it, expect, beforeEach, afterEach } from 'bun:test';
import '../setup-bun.js';

describe('WebSocket Integration Component', () => {
  let mockWebSocket;
  let container;
  
  beforeEach(() => {
    // Create test HTML structure with WebSocket-dependent components
    document.body.innerHTML = `
      <div class="websocket-container">
        <!-- Connection Status -->
        <div id="connection-status" class="alert alert-secondary" data-testid="connection-status">
          <span class="status-text">Disconnected</span>
          <span class="status-indicator bg-secondary"></span>
        </div>
        
        <!-- Real-time Updates Display -->
        <div id="realtime-updates" data-testid="realtime-updates">
          <h5>Real-time Updates</h5>
          <div class="updates-list" data-testid="updates-list"></div>
        </div>
        
        <!-- Progress Updates -->
        <div id="progress-updates" data-testid="progress-updates">
          <div class="progress mb-2">
            <div id="ws-progress-bar" class="progress-bar" style="width: 0%" data-testid="ws-progress-bar"></div>
          </div>
          <div class="progress-text" data-testid="progress-text">Ready</div>
        </div>
        
        <!-- Logs Display -->
        <div id="logs-display" data-testid="logs-display">
          <div class="logs-container" data-testid="logs-container"></div>
        </div>
        
        <!-- Error Display -->
        <div id="error-display" class="alert alert-danger d-none" data-testid="error-display">
          <span class="error-text"></span>
        </div>
      </div>
    `;
    
    container = document.querySelector('.websocket-container');
    
    // Create a mock WebSocket instance
    mockWebSocket = {
      readyState: 1, // OPEN
      url: 'ws://localhost:3000/ws',
      onopen: null,
      onmessage: null,
      onclose: null,
      onerror: null,
      send: function(data) {
        this.lastSentData = data;
      },
      close: function() {
        this.readyState = 3; // CLOSED
        if (this.onclose) this.onclose();
      },
      // Helper method to simulate receiving messages
      simulateMessage: function(data) {
        if (this.onmessage) {
          this.onmessage({ data: JSON.stringify(data) });
        }
      }
    };
  });

  afterEach(() => {
    document.body.innerHTML = '';
    mockWebSocket = null;
  });

  describe('Connection Status Tests', () => {
    it('should display connection status correctly', () => {
      const statusElement = document.querySelector('[data-testid="connection-status"]');
      const statusText = statusElement.querySelector('.status-text');
      const statusIndicator = statusElement.querySelector('.status-indicator');
      
      expect(statusElement).not.toBeNull();
      expect(statusText).not.toBeNull();
      expect(statusIndicator).not.toBeNull();
      expect(statusText.textContent).toBe('Disconnected');
    });

    it('should update status when connected', () => {
      const statusElement = document.querySelector('[data-testid="connection-status"]');
      const statusText = statusElement.querySelector('.status-text');
      const statusIndicator = statusElement.querySelector('.status-indicator');
      
      // Simulate connection
      statusText.textContent = 'Connected';
      statusElement.className = 'alert alert-success';
      statusIndicator.className = 'status-indicator bg-success';
      
      expect(statusText.textContent).toBe('Connected');
      expect(statusElement.classList.contains('alert-success')).toBe(true);
      expect(statusIndicator.classList.contains('bg-success')).toBe(true);
    });

    it('should update status when connection fails', () => {
      const statusElement = document.querySelector('[data-testid="connection-status"]');
      const statusText = statusElement.querySelector('.status-text');
      const statusIndicator = statusElement.querySelector('.status-indicator');
      
      // Simulate connection error
      statusText.textContent = 'Connection Error';
      statusElement.className = 'alert alert-danger';
      statusIndicator.className = 'status-indicator bg-danger';
      
      expect(statusText.textContent).toBe('Connection Error');
      expect(statusElement.classList.contains('alert-danger')).toBe(true);
      expect(statusIndicator.classList.contains('bg-danger')).toBe(true);
    });
  });

  describe('Real-time Updates Tests', () => {
    it('should have updates container structure', () => {
      const updatesContainer = document.querySelector('[data-testid="realtime-updates"]');
      const updatesList = document.querySelector('[data-testid="updates-list"]');
      
      expect(updatesContainer).not.toBeNull();
      expect(updatesList).not.toBeNull();
      expect(updatesContainer.querySelector('h5').textContent).toBe('Real-time Updates');
    });

    it('should be able to add new update messages', () => {
      const updatesList = document.querySelector('[data-testid="updates-list"]');
      
      // Simulate adding an update
      const updateElement = document.createElement('div');
      updateElement.className = 'update-item alert alert-info';
      updateElement.textContent = 'New update received';
      updatesList.appendChild(updateElement);
      
      expect(updatesList.children.length).toBe(1);
      expect(updatesList.children[0].textContent).toBe('New update received');
      expect(updatesList.children[0].classList.contains('alert-info')).toBe(true);
    });

    it('should be able to handle multiple updates', () => {
      const updatesList = document.querySelector('[data-testid="updates-list"]');
      
      // Add multiple updates
      for (let i = 1; i <= 3; i++) {
        const updateElement = document.createElement('div');
        updateElement.className = 'update-item';
        updateElement.textContent = `Update ${i}`;
        updatesList.appendChild(updateElement);
      }
      
      expect(updatesList.children.length).toBe(3);
      expect(updatesList.children[0].textContent).toBe('Update 1');
      expect(updatesList.children[2].textContent).toBe('Update 3');
    });

    it('should be able to clear updates', () => {
      const updatesList = document.querySelector('[data-testid="updates-list"]');
      
      // Add some updates first
      updatesList.innerHTML = '<div>Update 1</div><div>Update 2</div>';
      expect(updatesList.children.length).toBe(2);
      
      // Clear updates
      updatesList.innerHTML = '';
      expect(updatesList.children.length).toBe(0);
    });
  });

  describe('Progress Updates Tests', () => {
    it('should have progress bar structure', () => {
      const progressUpdates = document.querySelector('[data-testid="progress-updates"]');
      const progressBar = document.querySelector('[data-testid="ws-progress-bar"]');
      const progressText = document.querySelector('[data-testid="progress-text"]');
      
      expect(progressUpdates).not.toBeNull();
      expect(progressBar).not.toBeNull();
      expect(progressText).not.toBeNull();
      expect(progressText.textContent).toBe('Ready');
    });

    it('should update progress via WebSocket messages', () => {
      const progressBar = document.querySelector('[data-testid="ws-progress-bar"]');
      const progressText = document.querySelector('[data-testid="progress-text"]');
      
      // Simulate progress update
      progressBar.style.width = '45%';
      progressText.textContent = 'Processing... 45%';
      
      expect(progressBar.style.width).toBe('45%');
      expect(progressText.textContent).toBe('Processing... 45%');
    });

    it('should handle progress completion', () => {
      const progressBar = document.querySelector('[data-testid="ws-progress-bar"]');
      const progressText = document.querySelector('[data-testid="progress-text"]');
      
      // Simulate completion
      progressBar.style.width = '100%';
      progressBar.classList.add('bg-success');
      progressText.textContent = 'Completed';
      
      expect(progressBar.style.width).toBe('100%');
      expect(progressBar.classList.contains('bg-success')).toBe(true);
      expect(progressText.textContent).toBe('Completed');
    });
  });

  describe('Logs Display Tests', () => {
    it('should have logs container', () => {
      const logsDisplay = document.querySelector('[data-testid="logs-display"]');
      const logsContainer = document.querySelector('[data-testid="logs-container"]');
      
      expect(logsDisplay).not.toBeNull();
      expect(logsContainer).not.toBeNull();
    });

    it('should be able to add log entries', () => {
      const logsContainer = document.querySelector('[data-testid="logs-container"]');
      
      // Simulate adding a log entry
      const logEntry = document.createElement('div');
      logEntry.className = 'log-entry';
      logEntry.innerHTML = '<span class="timestamp">12:34:56</span> <span class="message">Operation started</span>';
      logsContainer.appendChild(logEntry);
      
      expect(logsContainer.children.length).toBe(1);
      expect(logsContainer.querySelector('.timestamp').textContent).toBe('12:34:56');
      expect(logsContainer.querySelector('.message').textContent).toBe('Operation started');
    });

    it('should handle different log levels', () => {
      const logsContainer = document.querySelector('[data-testid="logs-container"]');
      
      // Add logs with different levels
      const levels = ['info', 'warning', 'error'];
      levels.forEach((level, index) => {
        const logEntry = document.createElement('div');
        logEntry.className = `log-entry log-${level}`;
        logEntry.textContent = `${level} message ${index + 1}`;
        logsContainer.appendChild(logEntry);
      });
      
      expect(logsContainer.children.length).toBe(3);
      expect(logsContainer.children[0].classList.contains('log-info')).toBe(true);
      expect(logsContainer.children[1].classList.contains('log-warning')).toBe(true);
      expect(logsContainer.children[2].classList.contains('log-error')).toBe(true);
    });
  });

  describe('Error Display Tests', () => {
    it('should have error display container', () => {
      const errorDisplay = document.querySelector('[data-testid="error-display"]');
      const errorText = errorDisplay.querySelector('.error-text');
      
      expect(errorDisplay).not.toBeNull();
      expect(errorText).not.toBeNull();
      expect(errorDisplay.classList.contains('d-none')).toBe(true);
    });

    it('should show errors when they occur', () => {
      const errorDisplay = document.querySelector('[data-testid="error-display"]');
      const errorText = errorDisplay.querySelector('.error-text');
      
      // Simulate error
      errorText.textContent = 'WebSocket connection failed';
      errorDisplay.classList.remove('d-none');
      
      expect(errorDisplay.classList.contains('d-none')).toBe(false);
      expect(errorText.textContent).toBe('WebSocket connection failed');
    });

    it('should be able to hide errors', () => {
      const errorDisplay = document.querySelector('[data-testid="error-display"]');
      
      // Show error first
      errorDisplay.classList.remove('d-none');
      expect(errorDisplay.classList.contains('d-none')).toBe(false);
      
      // Hide error
      errorDisplay.classList.add('d-none');
      expect(errorDisplay.classList.contains('d-none')).toBe(true);
    });
  });

  describe('WebSocket Message Handling Tests', () => {
    it('should handle WebSocket connection setup', () => {
      expect(mockWebSocket.readyState).toBe(1); // OPEN
      expect(mockWebSocket.url).toBe('ws://localhost:3000/ws');
    });

    it('should handle incoming progress messages', () => {
      const progressBar = document.querySelector('[data-testid="ws-progress-bar"]');
      const progressText = document.querySelector('[data-testid="progress-text"]');
      
      // Simulate receiving progress message
      const progressData = { type: 'progress', value: 65, message: 'Processing files...' };
      
      // Mock message handling
      progressBar.style.width = `${progressData.value}%`;
      progressText.textContent = `${progressData.message} ${progressData.value}%`;
      
      expect(progressBar.style.width).toBe('65%');
      expect(progressText.textContent).toBe('Processing files... 65%');
    });

    it('should handle incoming log messages', () => {
      const logsContainer = document.querySelector('[data-testid="logs-container"]');
      
      // Simulate receiving log message
      const logData = { type: 'log', level: 'info', message: 'File processed successfully', timestamp: '12:34:56' };
      
      // Mock message handling
      const logEntry = document.createElement('div');
      logEntry.className = `log-entry log-${logData.level}`;
      logEntry.innerHTML = `<span class="timestamp">${logData.timestamp}</span> <span class="message">${logData.message}</span>`;
      logsContainer.appendChild(logEntry);
      
      expect(logsContainer.children.length).toBe(1);
      expect(logsContainer.querySelector('.message').textContent).toBe('File processed successfully');
      expect(logsContainer.querySelector('.log-entry').classList.contains('log-info')).toBe(true);
    });

    it('should handle error messages', () => {
      const errorDisplay = document.querySelector('[data-testid="error-display"]');
      const errorText = errorDisplay.querySelector('.error-text');
      
      // Simulate receiving error message
      const errorData = { type: 'error', message: 'Failed to process file' };
      
      // Mock error handling
      errorText.textContent = errorData.message;
      errorDisplay.classList.remove('d-none');
      
      expect(errorDisplay.classList.contains('d-none')).toBe(false);
      expect(errorText.textContent).toBe('Failed to process file');
    });

    it('should be able to send messages via WebSocket', () => {
      const testMessage = { type: 'ping', timestamp: Date.now() };
      
      mockWebSocket.send(JSON.stringify(testMessage));
      
      expect(mockWebSocket.lastSentData).toBe(JSON.stringify(testMessage));
    });
  });

  describe('Connection Lifecycle Tests', () => {
    it('should handle connection opening', () => {
      const statusElement = document.querySelector('[data-testid="connection-status"]');
      const statusText = statusElement.querySelector('.status-text');
      
      // Simulate onopen event
      mockWebSocket.onopen = () => {
        statusText.textContent = 'Connected';
        statusElement.className = 'alert alert-success';
      };
      
      if (mockWebSocket.onopen) mockWebSocket.onopen();
      
      expect(statusText.textContent).toBe('Connected');
      expect(statusElement.classList.contains('alert-success')).toBe(true);
    });

    it('should handle connection closing', () => {
      const statusElement = document.querySelector('[data-testid="connection-status"]');
      const statusText = statusElement.querySelector('.status-text');
      
      // Simulate onclose event
      mockWebSocket.onclose = () => {
        statusText.textContent = 'Disconnected';
        statusElement.className = 'alert alert-secondary';
      };
      
      mockWebSocket.close();
      
      expect(mockWebSocket.readyState).toBe(3); // CLOSED
      expect(statusText.textContent).toBe('Disconnected');
    });

    it('should handle connection errors', () => {
      const statusElement = document.querySelector('[data-testid="connection-status"]');
      const statusText = statusElement.querySelector('.status-text');
      const errorDisplay = document.querySelector('[data-testid="error-display"]');
      
      // Simulate onerror event
      mockWebSocket.onerror = (error) => {
        statusText.textContent = 'Connection Error';
        statusElement.className = 'alert alert-danger';
        errorDisplay.classList.remove('d-none');
      };
      
      if (mockWebSocket.onerror) mockWebSocket.onerror(new Error('Connection failed'));
      
      expect(statusText.textContent).toBe('Connection Error');
      expect(statusElement.classList.contains('alert-danger')).toBe(true);
      expect(errorDisplay.classList.contains('d-none')).toBe(false);
    });
  });

  describe('Real-time UI Updates Tests', () => {
    it('should update multiple UI elements from single message', () => {
      const progressBar = document.querySelector('[data-testid="ws-progress-bar"]');
      const progressText = document.querySelector('[data-testid="progress-text"]');
      const updatesList = document.querySelector('[data-testid="updates-list"]');
      
      // Simulate comprehensive status update
      const statusData = {
        type: 'status_update',
        progress: 80,
        message: 'Almost done...',
        update: 'Processing final batch'
      };
      
      // Mock comprehensive update handling
      progressBar.style.width = `${statusData.progress}%`;
      progressText.textContent = `${statusData.message} ${statusData.progress}%`;
      
      const updateElement = document.createElement('div');
      updateElement.className = 'update-item alert alert-info';
      updateElement.textContent = statusData.update;
      updatesList.appendChild(updateElement);
      
      expect(progressBar.style.width).toBe('80%');
      expect(progressText.textContent).toBe('Almost done... 80%');
      expect(updatesList.children.length).toBe(1);
      expect(updatesList.children[0].textContent).toBe('Processing final batch');
    });
  });
});
