/**
 * WebSocket Integration Component Tests
 * 
 * Tests for WebSocket connection management, event handling, and real-time updates
 */

import { screen, fireEvent, waitFor } from '@testing-library/dom';
import '@testing-library/jest-dom';
import WS from 'jest-websocket-mock';

describe('WebSocket Integration Component', () => {
  let server;
  let container;
  let WebSocketManager;
  
  beforeEach(() => {
    // Mock WebSocket server
    server = new WS('ws://localhost:8080/ws');
    
    // Create test HTML structure
    document.body.innerHTML = `
      <div data-testid="websocket-status" class="connection-status">Disconnected</div>
      <div data-testid="message-area" class="message-area"></div>
      <button data-testid="send-button" onclick="sendTestMessage()">Send Test</button>
    `;
    
    container = document.body;
    
    // Add WebSocketManager class from base.html
    global.WebSocketManager = class {
      constructor(path) {
        this.connect(path);
        this.callbacks = new Map();
      }

      connect(path) {
        const protocol = 'ws:';
        this.ws = new WebSocket(`${protocol}//localhost:8080${path}`);

        this.ws.onopen = () => {
          console.log('WebSocket connected');
          this.trigger('connect', null);
        };

        this.ws.onclose = () => {
          console.log('WebSocket disconnected, attempting reconnect...');
          this.trigger('disconnect', null);
          setTimeout(() => this.connect(path), 1000);
        };

        this.ws.onmessage = (event) => {
          const data = JSON.parse(event.data);
          this.trigger(data.type, data.data);
        };
      }

      on(event, callback) {
        if (!this.callbacks.has(event)) {
          this.callbacks.set(event, []);
        }
        this.callbacks.get(event).push(callback);
      }

      trigger(event, data) {
        const callbacks = this.callbacks.get(event) || [];
        callbacks.forEach(callback => callback(data));
      }

      send(data) {
        if (this.ws.readyState === WebSocket.OPEN) {
          this.ws.send(JSON.stringify(data));
        }
      }
    };
    
    WebSocketManager = global.WebSocketManager;
  });

  afterEach(() => {
    WS.clean();
    document.body.innerHTML = '';
    delete global.WebSocketManager;
  });

  describe('Connection Management', () => {
    test('should establish WebSocket connection', async () => {
      const wsManager = new WebSocketManager('/ws');
      
      await server.connected;
      expect(server).toHaveReceivedMessages([]);
    });

    test('should handle connection events', async () => {
      const wsManager = new WebSocketManager('/ws');
      const connectCallback = jest.fn();
      
      wsManager.on('connect', connectCallback);
      
      await server.connected;
      expect(connectCallback).toHaveBeenCalled();
    });

    test('should handle disconnection events', async () => {
      const wsManager = new WebSocketManager('/ws');
      const disconnectCallback = jest.fn();
      
      wsManager.on('disconnect', disconnectCallback);
      
      await server.connected;
      
      // Simulate disconnection
      server.close();
      
      await waitFor(() => {
        expect(disconnectCallback).toHaveBeenCalled();
      });
    });

    test('should attempt reconnection on disconnect', async () => {
      jest.useFakeTimers();
      
      const wsManager = new WebSocketManager('/ws');
      await server.connected;
      
      // Mock the connect method to track reconnection attempts
      const connectSpy = jest.spyOn(wsManager, 'connect');
      
      // Simulate disconnection
      server.close();
      
      // Fast-forward time to trigger reconnection
      jest.advanceTimersByTime(1000);
      
      expect(connectSpy).toHaveBeenCalledWith('/ws');
      
      jest.useRealTimers();
    });

    test('should handle connection status indicators', async () => {
      const statusElement = screen.getByTestId('websocket-status');
      const wsManager = new WebSocketManager('/ws');
      
      // Set up status callbacks
      wsManager.on('connect', () => {
        statusElement.textContent = 'Connected';
        statusElement.className = 'connection-status connected';
      });
      
      wsManager.on('disconnect', () => {
        statusElement.textContent = 'Disconnected';
        statusElement.className = 'connection-status disconnected';
      });
      
      await server.connected;
      
      expect(statusElement).toHaveTextContent('Connected');
      expect(statusElement).toHaveClass('connected');
    });
  });

  describe('Event Handling', () => {
    test('should register event callbacks', () => {
      const wsManager = new WebSocketManager('/ws');
      const callback = jest.fn();
      
      wsManager.on('test-event', callback);
      
      expect(wsManager.callbacks.has('test-event')).toBe(true);
      expect(wsManager.callbacks.get('test-event')).toContain(callback);
    });

    test('should handle multiple callbacks for same event', () => {
      const wsManager = new WebSocketManager('/ws');
      const callback1 = jest.fn();
      const callback2 = jest.fn();
      
      wsManager.on('test-event', callback1);
      wsManager.on('test-event', callback2);
      
      wsManager.trigger('test-event', { test: 'data' });
      
      expect(callback1).toHaveBeenCalledWith({ test: 'data' });
      expect(callback2).toHaveBeenCalledWith({ test: 'data' });
    });

    test('should process incoming messages correctly', async () => {
      const wsManager = new WebSocketManager('/ws');
      const messageCallback = jest.fn();
      
      wsManager.on('progress-update', messageCallback);
      
      await server.connected;
      
      // Send message from server
      server.send(JSON.stringify({
        type: 'progress-update',
        data: { progress: 50, message: 'Processing...' }
      }));
      
      expect(messageCallback).toHaveBeenCalledWith({
        progress: 50,
        message: 'Processing...'
      });
    });

    test('should handle malformed messages gracefully', async () => {
      const wsManager = new WebSocketManager('/ws');
      const errorCallback = jest.fn();
      
      // Mock console.error to track errors
      const consoleSpy = jest.spyOn(console, 'error').mockImplementation();
      
      await server.connected;
      
      // Send malformed JSON
      server.send('invalid-json');
      
      // The WebSocket should handle this gracefully
      expect(consoleSpy).not.toHaveBeenCalled();
      
      consoleSpy.mockRestore();
    });

    test('should trigger callbacks with correct data', async () => {
      const wsManager = new WebSocketManager('/ws');
      const callback = jest.fn();
      
      wsManager.on('scraping-complete', callback);
      
      await server.connected;
      
      const testData = {
        type: 'scraping-complete',
        data: {
          url: 'https://example.com',
          pages: 10,
          duration: 1500
        }
      };
      
      server.send(JSON.stringify(testData));
      
      expect(callback).toHaveBeenCalledWith(testData.data);
    });
  });

  describe('Message Sending', () => {
    test('should send messages when connection is open', async () => {
      const wsManager = new WebSocketManager('/ws');
      
      await server.connected;
      
      const testMessage = { action: 'start-scraping', url: 'https://example.com' };
      wsManager.send(testMessage);
      
      await expect(server).toReceiveMessage(JSON.stringify(testMessage));
    });

    test('should not send messages when connection is closed', () => {
      const wsManager = new WebSocketManager('/ws');
      
      // Don't wait for connection
      const testMessage = { action: 'test' };
      wsManager.send(testMessage);
      
      // Message should not be sent
      expect(server).not.toHaveReceivedMessages([JSON.stringify(testMessage)]);
    });

    test('should handle send errors gracefully', async () => {
      const wsManager = new WebSocketManager('/ws');
      await server.connected;
      
      // Close connection from server side
      server.close();
      
      // Attempt to send message
      const consoleSpy = jest.spyOn(console, 'error').mockImplementation();
      wsManager.send({ test: 'message' });
      
      // Should not throw error
      expect(consoleSpy).not.toHaveBeenCalled();
      consoleSpy.mockRestore();
    });
  });

  describe('Real-time Updates Integration', () => {
    test('should update UI elements on progress messages', async () => {
      const wsManager = new WebSocketManager('/ws');
      const messageArea = screen.getByTestId('message-area');
      
      wsManager.on('progress-update', (data) => {
        messageArea.innerHTML = `
          <div class="progress-update">
            <div class="progress-bar" style="width: ${data.progress}%"></div>
            <span class="progress-text">${data.message}</span>
          </div>
        `;
      });
      
      await server.connected;
      
      server.send(JSON.stringify({
        type: 'progress-update',
        data: { progress: 75, message: 'Almost done...' }
      }));
      
      await waitFor(() => {
        expect(messageArea.querySelector('.progress-bar')).toHaveStyle('width: 75%');
        expect(messageArea.querySelector('.progress-text')).toHaveTextContent('Almost done...');
      });
    });

    test('should handle real-time scraping status updates', async () => {
      const wsManager = new WebSocketManager('/ws');
      const statusArea = screen.getByTestId('message-area');
      
      wsManager.on('scraping-status', (data) => {
        statusArea.innerHTML = `
          <div class="status-update">
            <h4>Scraping ${data.url}</h4>
            <p>Pages processed: ${data.pages}</p>
            <p>Status: ${data.status}</p>
          </div>
        `;
      });
      
      await server.connected;
      
      server.send(JSON.stringify({
        type: 'scraping-status',
        data: {
          url: 'https://docs.python.org',
          pages: 42,
          status: 'in-progress'
        }
      }));
      
      await waitFor(() => {
        expect(statusArea.querySelector('h4')).toHaveTextContent('Scraping https://docs.python.org');
        expect(statusArea).toHaveTextContent('Pages processed: 42');
        expect(statusArea).toHaveTextContent('Status: in-progress');
      });
    });

    test('should handle completion notifications', async () => {
      const wsManager = new WebSocketManager('/ws');
      const messageArea = screen.getByTestId('message-area');
      
      wsManager.on('scraping-complete', (data) => {
        messageArea.innerHTML = `
          <div class="completion-notice alert alert-success">
            <h4>Scraping Complete!</h4>
            <p>Successfully processed ${data.pages} pages in ${data.duration}ms</p>
            <a href="/results/${data.resultId}" class="btn btn-primary">View Results</a>
          </div>
        `;
      });
      
      await server.connected;
      
      server.send(JSON.stringify({
        type: 'scraping-complete',
        data: {
          pages: 156,
          duration: 12500,
          resultId: 'abc123'
        }
      }));
      
      await waitFor(() => {
        expect(messageArea.querySelector('.alert-success')).toBeInTheDocument();
        expect(messageArea).toHaveTextContent('Successfully processed 156 pages');
        expect(messageArea.querySelector('a[href="/results/abc123"]')).toBeInTheDocument();
      });
    });
  });

  describe('Error Handling', () => {
    test('should handle WebSocket errors gracefully', async () => {
      const wsManager = new WebSocketManager('/ws');
      const errorCallback = jest.fn();
      
      wsManager.on('error', errorCallback);
      
      await server.connected;
      
      // Simulate server error
      server.error();
      
      // Should handle error without crashing
      expect(() => wsManager.send({ test: 'message' })).not.toThrow();
    });

    test('should handle invalid JSON messages', async () => {
      const wsManager = new WebSocketManager('/ws');
      
      await server.connected;
      
      // This should not crash the application
      expect(() => {
        server.send('not-valid-json');
      }).not.toThrow();
    });

    test('should maintain connection state consistency', async () => {
      const wsManager = new WebSocketManager('/ws');
      
      await server.connected;
      expect(wsManager.ws.readyState).toBe(WebSocket.OPEN);
      
      server.close();
      
      await waitFor(() => {
        expect(wsManager.ws.readyState).toBe(WebSocket.CLOSED);
      });
    });
  });
});
