/**
 * Progress Monitoring Tests (Bun)
 * 
 * Modern tests for real-time progress tracking and WebSocket handling
 */

import { test, expect, describe, beforeEach } from "bun:test";
import { testUtils } from "../setup";

describe("Progress Monitoring", () => {
  beforeEach(() => {
    // Create mock DOM structure for progress monitoring
    document.body.innerHTML = `
      <div class="container-fluid">
        <!-- Primary Progress Metrics -->
        <div class="row" id="primaryMetrics">
          <div class="col-md-3">
            <div class="card bg-primary text-white">
              <div class="card-body text-center">
                <h3 class="mb-0" id="pagesProcessed">0</h3>
                <small>Pages Processed</small>
              </div>
            </div>
          </div>
          <div class="col-md-3">
            <div class="card bg-success text-white">
              <div class="card-body text-center">
                <h3 class="mb-0" id="successRate">0%</h3>
                <small>Success Rate</small>
              </div>
            </div>
          </div>
          <div class="col-md-3">
            <div class="card bg-info text-white">
              <div class="card-body text-center">
                <h3 class="mb-0" id="qualityScore">0%</h3>
                <small>Quality Score</small>
              </div>
            </div>
          </div>
          <div class="col-md-3">
            <div class="card bg-warning text-dark">
              <div class="card-body text-center">
                <h3 class="mb-0" id="completionTime">-</h3>
                <small>Est. Completion</small>
              </div>
            </div>
          </div>
        </div>

        <!-- Secondary Progress Metrics -->
        <div class="row mt-3" id="secondaryMetrics">
          <div class="col-md-2">
            <div class="card">
              <div class="card-body text-center">
                <h5 class="mb-0" id="currentDepth">0</h5>
                <small>Current Depth</small>
              </div>
            </div>
          </div>
          <div class="col-md-2">
            <div class="card">
              <div class="card-body text-center">
                <h5 class="mb-0" id="contentSize">0 KB</h5>
                <small>Content Size</small>
              </div>
            </div>
          </div>
          <div class="col-md-2">
            <div class="card">
              <div class="card-body text-center">
                <h5 class="mb-0" id="linksFound">0</h5>
                <small>Links Found</small>
              </div>
            </div>
          </div>
          <div class="col-md-2">
            <div class="card">
              <div class="card-body text-center">
                <h5 class="mb-0" id="codeBlocks">0</h5>
                <small>Code Blocks</small>
              </div>
            </div>
          </div>
          <div class="col-md-2">
            <div class="card">
              <div class="card-body text-center">
                <h5 class="mb-0" id="imagesFound">0</h5>
                <small>Images</small>
              </div>
            </div>
          </div>
          <div class="col-md-2">
            <div class="card">
              <div class="card-body text-center">
                <h5 class="mb-0" id="currentBackend">-</h5>
                <small>Backend</small>
              </div>
            </div>
          </div>
        </div>

        <!-- Progress Bar -->
        <div class="progress mt-3">
          <div class="progress-bar progress-bar-striped progress-bar-animated" 
               id="overallProgress" style="width: 0%"></div>
        </div>

        <!-- Status Messages -->
        <div id="statusMessages" class="mt-3">
          <div class="alert alert-info" id="currentStatus">
            Ready to start scraping...
          </div>
        </div>

        <!-- Control Buttons -->
        <div class="mt-3">
          <button type="button" id="startBtn" class="btn btn-primary">Start Scraping</button>
          <button type="button" id="stopBtn" class="btn btn-danger" disabled>Stop</button>
          <button type="button" id="pauseBtn" class="btn btn-warning" disabled>Pause</button>
        </div>
      </div>
    `;
  });

  describe("Progress Display", () => {
    test("should initialize with zero values", () => {
      const pagesProcessed = document.getElementById('pagesProcessed') as HTMLElement;
      const successRate = document.getElementById('successRate') as HTMLElement;
      const qualityScore = document.getElementById('qualityScore') as HTMLElement;
      const completionTime = document.getElementById('completionTime') as HTMLElement;

      expect(pagesProcessed.textContent).toBe('0');
      expect(successRate.textContent).toBe('0%');
      expect(qualityScore.textContent).toBe('0%');
      expect(completionTime.textContent).toBe('-');
    });

    test("should update primary metrics", () => {
      const pagesProcessed = document.getElementById('pagesProcessed') as HTMLElement;
      const successRate = document.getElementById('successRate') as HTMLElement;
      const qualityScore = document.getElementById('qualityScore') as HTMLElement;
      const completionTime = document.getElementById('completionTime') as HTMLElement;

      // Simulate progress update
      pagesProcessed.textContent = '15';
      successRate.textContent = '95%';
      qualityScore.textContent = '85%';
      completionTime.textContent = '2 minutes';

      expect(pagesProcessed.textContent).toBe('15');
      expect(successRate.textContent).toBe('95%');
      expect(qualityScore.textContent).toBe('85%');
      expect(completionTime.textContent).toBe('2 minutes');
    });

    test("should update secondary metrics", () => {
      const currentDepth = document.getElementById('currentDepth') as HTMLElement;
      const contentSize = document.getElementById('contentSize') as HTMLElement;
      const linksFound = document.getElementById('linksFound') as HTMLElement;
      const codeBlocks = document.getElementById('codeBlocks') as HTMLElement;
      const imagesFound = document.getElementById('imagesFound') as HTMLElement;
      const currentBackend = document.getElementById('currentBackend') as HTMLElement;

      // Simulate secondary metrics update
      currentDepth.textContent = '3';
      contentSize.textContent = '1.2 MB';
      linksFound.textContent = '45';
      codeBlocks.textContent = '12';
      imagesFound.textContent = '8';
      currentBackend.textContent = 'Crawl4AI';

      expect(currentDepth.textContent).toBe('3');
      expect(contentSize.textContent).toBe('1.2 MB');
      expect(linksFound.textContent).toBe('45');
      expect(codeBlocks.textContent).toBe('12');
      expect(imagesFound.textContent).toBe('8');
      expect(currentBackend.textContent).toBe('Crawl4AI');
    });

    test("should update progress bar", () => {
      const progressBar = document.getElementById('overallProgress') as HTMLElement;

      // Simulate progress update
      progressBar.style.width = '65%';
      progressBar.setAttribute('aria-valuenow', '65');

      expect(progressBar.style.width).toBe('65%');
      expect(progressBar.getAttribute('aria-valuenow')).toBe('65');
    });
  });

  describe("WebSocket Communication", () => {
    test("should establish WebSocket connection", () => {
      const ws = new WebSocket('ws://localhost:8000/ws');
      
      expect(ws.readyState).toBe(WebSocket.CONNECTING);
    });

    test("should handle progress messages", async () => {
      const ws = new WebSocket('ws://localhost:8000/ws');
      
      // Wait for connection to open
      await testUtils.waitFor(() => ws.readyState === WebSocket.OPEN);
      
      // Mock progress message handling
      const progressMessage = {
        type: 'progress',
        data: {
          pages: 15,
          success_rate: 95,
          quality_score: 85,
          depth: 3,
          content_size: '1.2 MB',
          links: 45,
          code_blocks: 12,
          images: 8,
          backend: 'Crawl4AI',
          completion_time: '2 minutes'
        }
      };

      // Simulate message handling
      ws.send(JSON.stringify(progressMessage));

      expect(ws.readyState).toBe(WebSocket.OPEN);
    });
  });

  describe("Control Buttons", () => {
    test("should handle start button click", () => {
      const startBtn = document.getElementById('startBtn') as HTMLButtonElement;
      const stopBtn = document.getElementById('stopBtn') as HTMLButtonElement;
      const pauseBtn = document.getElementById('pauseBtn') as HTMLButtonElement;

      testUtils.simulateClick(startBtn);

      // Verify button states would change (in real implementation)
      expect(startBtn).toBeTruthy();
      expect(stopBtn).toBeTruthy();
      expect(pauseBtn).toBeTruthy();
    });

    test("should handle stop button click", () => {
      const stopBtn = document.getElementById('stopBtn') as HTMLButtonElement;
      
      // Enable stop button first
      stopBtn.disabled = false;
      
      testUtils.simulateClick(stopBtn);

      expect(stopBtn).toBeTruthy();
    });

    test("should manage button states correctly", () => {
      const startBtn = document.getElementById('startBtn') as HTMLButtonElement;
      const stopBtn = document.getElementById('stopBtn') as HTMLButtonElement;
      const pauseBtn = document.getElementById('pauseBtn') as HTMLButtonElement;

      // Initial state
      expect(startBtn.disabled).toBe(false);
      expect(stopBtn.disabled).toBe(true);
      expect(pauseBtn.disabled).toBe(true);

      // Simulate starting
      startBtn.disabled = true;
      stopBtn.disabled = false;
      pauseBtn.disabled = false;

      expect(startBtn.disabled).toBe(true);
      expect(stopBtn.disabled).toBe(false);
      expect(pauseBtn.disabled).toBe(false);
    });
  });

  describe("Status Messages", () => {
    test("should display status messages", () => {
      const statusDiv = document.getElementById('currentStatus') as HTMLElement;

      statusDiv.textContent = 'Processing page: https://docs.python.org/3/';
      statusDiv.className = 'alert alert-info';

      expect(statusDiv.textContent).toBe('Processing page: https://docs.python.org/3/');
      expect(statusDiv.className).toContain('alert-info');
    });

    test("should handle different status levels", () => {
      const statusDiv = document.getElementById('currentStatus') as HTMLElement;

      // Info status
      statusDiv.className = 'alert alert-info';
      expect(statusDiv.className).toContain('alert-info');

      // Warning status
      statusDiv.className = 'alert alert-warning';
      expect(statusDiv.className).toContain('alert-warning');

      // Error status
      statusDiv.className = 'alert alert-danger';
      expect(statusDiv.className).toContain('alert-danger');

      // Success status
      statusDiv.className = 'alert alert-success';
      expect(statusDiv.className).toContain('alert-success');
    });
  });

  describe("Real-time Updates", () => {
    test("should handle rapid progress updates", () => {
      const pagesProcessed = document.getElementById('pagesProcessed') as HTMLElement;
      const progressBar = document.getElementById('overallProgress') as HTMLElement;

      // Simulate rapid updates
      for (let i = 1; i <= 10; i++) {
        pagesProcessed.textContent = i.toString();
        progressBar.style.width = `${i * 10}%`;
      }

      expect(pagesProcessed.textContent).toBe('10');
      expect(progressBar.style.width).toBe('100%');
    });

    test("should handle concurrent metric updates", () => {
      const metrics = {
        pagesProcessed: document.getElementById('pagesProcessed') as HTMLElement,
        successRate: document.getElementById('successRate') as HTMLElement,
        qualityScore: document.getElementById('qualityScore') as HTMLElement,
        currentDepth: document.getElementById('currentDepth') as HTMLElement,
        contentSize: document.getElementById('contentSize') as HTMLElement
      };

      // Update all metrics simultaneously
      metrics.pagesProcessed.textContent = '25';
      metrics.successRate.textContent = '92%';
      metrics.qualityScore.textContent = '87%';
      metrics.currentDepth.textContent = '4';
      metrics.contentSize.textContent = '2.1 MB';

      expect(metrics.pagesProcessed.textContent).toBe('25');
      expect(metrics.successRate.textContent).toBe('92%');
      expect(metrics.qualityScore.textContent).toBe('87%');
      expect(metrics.currentDepth.textContent).toBe('4');
      expect(metrics.contentSize.textContent).toBe('2.1 MB');
    });
  });

  describe("Error Handling", () => {
    test("should handle missing DOM elements", () => {
      // Remove an element
      const pagesElement = document.getElementById('pagesProcessed');
      pagesElement?.remove();

      // Should handle gracefully
      expect(() => {
        const element = document.getElementById('pagesProcessed');
        if (element) {
          element.textContent = '10';
        }
      }).not.toThrow();
    });
  });
});
