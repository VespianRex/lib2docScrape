/**
 * Dashboard JavaScript functionality
 * Handles scraping operations, WebSocket connections, and UI updates
 */

class ScrapingDashboard {
    constructor() {
        this.ws = null;
        this.isConnected = false;
        this.scrapingInProgress = false;
        this.currentScrapingId = null;
        this.metrics = {
            pages_scraped: 0,
            successful_requests: 0,
            failed_requests: 0,
            current_depth: 0,
            pages_per_second: 0.0
        };
        
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.setupWebSocket();
        this.loadBackends();
        this.loadConfigPresets();
        this.initializeTooltips();
    }

    setupEventListeners() {
        // Form submission
        const scrapingForm = document.getElementById('scrapingForm');
        if (scrapingForm) {
            scrapingForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.startScraping();
            });
        }

        // Backend selection change
        const backendSelect = document.getElementById('backend');
        if (backendSelect) {
            backendSelect.addEventListener('change', () => {
                this.updateBackendDescription();
            });
        }

        // Config preset change
        const configPreset = document.getElementById('configPreset');
        if (configPreset) {
            configPreset.addEventListener('change', () => {
                this.updateConfigPreset();
            });
        }

        // Benchmark button
        const benchmarkBtn = document.getElementById('benchmarkBtn');
        if (benchmarkBtn) {
            benchmarkBtn.addEventListener('click', () => {
                this.runBenchmark();
            });
        }

        // Stop scraping button
        const stopBtn = document.getElementById('stopScrapingBtn');
        if (stopBtn) {
            stopBtn.addEventListener('click', () => {
                this.stopScraping();
            });
        }

        // Download buttons
        document.querySelectorAll('[data-download-format]').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const format = e.target.dataset.downloadFormat;
                this.downloadResults(format);
            });
        });

        // Clear results button
        const clearBtn = document.getElementById('clearResultsBtn');
        if (clearBtn) {
            clearBtn.addEventListener('click', () => {
                this.clearResults();
            });
        }
    }

    setupWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/scraping`;
        
        try {
            this.ws = new WebSocket(wsUrl);
            
            this.ws.onopen = () => {
                console.log('WebSocket connected');
                this.isConnected = true;
                this.updateConnectionStatus(true);
            };

            this.ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                this.handleWebSocketMessage(data);
            };

            this.ws.onclose = () => {
                console.log('WebSocket disconnected');
                this.isConnected = false;
                this.updateConnectionStatus(false);
                
                // Attempt to reconnect after 3 seconds
                setTimeout(() => {
                    if (!this.isConnected) {
                        this.setupWebSocket();
                    }
                }, 3000);
            };

            this.ws.onerror = (error) => {
                console.error('WebSocket error:', error);
                this.showError('WebSocket connection error');
            };
        } catch (error) {
            console.error('Failed to create WebSocket connection:', error);
            this.showError('Failed to establish real-time connection');
        }
    }

    handleWebSocketMessage(data) {
        switch (data.type) {
            case 'connection_established':
                this.updateScrapingStatus(data.data);
                break;
            case 'scraping_progress':
                this.updateProgress(data.data);
                break;
            case 'metrics':
                this.updateMetrics(data.data);
                break;
            case 'scraping_complete':
                this.handleScrapingComplete(data.data);
                break;
            case 'scraping_error':
                this.handleScrapingError(data.data);
                break;
            default:
                console.log('Unknown message type:', data.type);
        }
    }

    async startScraping() {
        if (this.scrapingInProgress) {
            this.showError('Scraping is already in progress');
            return;
        }

        const formData = this.getFormData();
        if (!this.validateFormData(formData)) {
            return;
        }

        try {
            this.scrapingInProgress = true;
            this.updateUI(true);
            this.showLoading();

            const response = await fetch('/crawl', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(formData)
            });

            const result = await response.json();

            if (result.status === 'success') {
                this.currentScrapingId = result.scraping_id;
                this.showSuccess('Scraping started successfully');
                this.displayResults(result.results);
            } else {
                throw new Error(result.message || 'Scraping failed');
            }
        } catch (error) {
            console.error('Scraping error:', error);
            this.showError(`Scraping failed: ${error.message}`);
            this.scrapingInProgress = false;
            this.updateUI(false);
        } finally {
            this.hideLoading();
        }
    }

    getFormData() {
        return {
            url: document.getElementById('docUrl')?.value || '',
            backend: document.getElementById('backend')?.value || 'http',
            max_depth: parseInt(document.getElementById('maxDepth')?.value) || 3,
            max_pages: parseInt(document.getElementById('maxPages')?.value) || 100,
            concurrent_requests: parseInt(document.getElementById('concurrentRequests')?.value) || 5,
            delay: parseFloat(document.getElementById('requestDelay')?.value) || 1.0,
            follow_external: document.getElementById('followExternal')?.checked || false,
            respect_robots: document.getElementById('respectRobots')?.checked || true,
            custom_headers: this.parseCustomHeaders(),
            exclude_patterns: this.parseExcludePatterns(),
            include_patterns: this.parseIncludePatterns()
        };
    }

    validateFormData(data) {
        if (!data.url) {
            this.showError('Please enter a URL');
            return false;
        }

        try {
            new URL(data.url);
        } catch {
            this.showError('Please enter a valid URL');
            return false;
        }

        if (data.max_depth < 1 || data.max_depth > 10) {
            this.showError('Max depth must be between 1 and 10');
            return false;
        }

        if (data.max_pages < 1 || data.max_pages > 1000) {
            this.showError('Max pages must be between 1 and 1000');
            return false;
        }

        return true;
    }

    parseCustomHeaders() {
        const headersText = document.getElementById('customHeaders')?.value || '';
        if (!headersText.trim()) return {};

        try {
            return JSON.parse(headersText);
        } catch {
            // Try to parse as key:value pairs
            const headers = {};
            headersText.split('\n').forEach(line => {
                const [key, ...valueParts] = line.split(':');
                if (key && valueParts.length > 0) {
                    headers[key.trim()] = valueParts.join(':').trim();
                }
            });
            return headers;
        }
    }

    parseExcludePatterns() {
        const patterns = document.getElementById('excludePatterns')?.value || '';
        return patterns.split('\n').filter(p => p.trim()).map(p => p.trim());
    }

    parseIncludePatterns() {
        const patterns = document.getElementById('includePatterns')?.value || '';
        return patterns.split('\n').filter(p => p.trim()).map(p => p.trim());
    }

    updateProgress(data) {
        const progressBar = document.getElementById('scrapingProgress');
        const progressText = document.getElementById('progressText');
        const currentUrl = document.getElementById('currentUrl');

        if (progressBar) {
            progressBar.style.width = `${data.progress || 0}%`;
            progressBar.setAttribute('aria-valuenow', data.progress || 0);
        }

        if (progressText) {
            progressText.textContent = `${data.progress || 0}%`;
        }

        if (currentUrl && data.current_url) {
            currentUrl.textContent = data.current_url;
        }

        // Update status badge
        const statusBadge = document.getElementById('statusBadge');
        if (statusBadge) {
            if (data.is_running) {
                statusBadge.textContent = 'Running';
                statusBadge.className = 'badge bg-primary';
            } else {
                statusBadge.textContent = 'Idle';
                statusBadge.className = 'badge bg-secondary';
            }
        }
    }

    updateMetrics(metrics) {
        this.metrics = { ...this.metrics, ...metrics };
        
        const metricsDisplay = document.getElementById('metricsDisplay');
        if (metricsDisplay) {
            metricsDisplay.innerHTML = `
                <div class="row">
                    <div class="col-md-3">
                        <label>Pages Scraped:</label>
                        <span class="badge bg-info">${this.metrics.pages_scraped}</span>
                    </div>
                    <div class="col-md-3">
                        <label>Successful:</label>
                        <span class="badge bg-success">${this.metrics.successful_requests}</span>
                    </div>
                    <div class="col-md-3">
                        <label>Failed:</label>
                        <span class="badge bg-danger">${this.metrics.failed_requests}</span>
                    </div>
                    <div class="col-md-3">
                        <label>Pages/sec:</label>
                        <span class="badge bg-secondary">${this.metrics.pages_per_second.toFixed(2)}</span>
                    </div>
                </div>
            `;
        }
    }

    displayResults(results) {
        const resultsContainer = document.getElementById('scrapingResults');
        if (!resultsContainer || !results) return;

        resultsContainer.innerHTML = `
            <div class="card">
                <div class="card-header">
                    <h5>Scraping Results</h5>
                    <small class="text-muted">${results.length} pages processed</small>
                </div>
                <div class="card-body">
                    <div class="table-responsive">
                        <table class="table table-striped">
                            <thead>
                                <tr>
                                    <th>URL</th>
                                    <th>Title</th>
                                    <th>Status</th>
                                    <th>Content Length</th>
                                    <th>Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${results.map(result => `
                                    <tr>
                                        <td>
                                            <a href="${result.url}" target="_blank" class="text-truncate" style="max-width: 200px;">
                                                ${result.url}
                                            </a>
                                        </td>
                                        <td class="text-truncate" style="max-width: 150px;">
                                            ${result.content?.title || 'No title'}
                                        </td>
                                        <td>
                                            <span class="badge ${result.success ? 'bg-success' : 'bg-danger'}">
                                                ${result.success ? 'Success' : 'Failed'}
                                            </span>
                                        </td>
                                        <td>${result.content?.text?.length || 0} chars</td>
                                        <td>
                                            <button class="btn btn-sm btn-outline-primary" onclick="dashboard.viewDocument('${result.url}')">
                                                View
                                            </button>
                                        </td>
                                    </tr>
                                `).join('')}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        `;

        resultsContainer.style.display = 'block';
    }

    async loadBackends() {
        try {
            const response = await fetch('/api/scraping/backends');
            const backends = await response.json();
            
            const backendSelect = document.getElementById('backend');
            if (backendSelect && Array.isArray(backends)) {
                // Clear existing options except the first few default ones
                const defaultOptions = Array.from(backendSelect.options).slice(0, 6);
                backendSelect.innerHTML = '';
                defaultOptions.forEach(option => backendSelect.appendChild(option));
                
                // Add available backends
                backends.forEach(backend => {
                    if (!Array.from(backendSelect.options).some(opt => opt.value === backend)) {
                        const option = document.createElement('option');
                        option.value = backend;
                        option.textContent = backend.charAt(0).toUpperCase() + backend.slice(1);
                        backendSelect.appendChild(option);
                    }
                });
            }
        } catch (error) {
            console.error('Failed to load backends:', error);
        }
    }

    updateBackendDescription() {
        const backend = document.getElementById('backend')?.value;
        const description = document.getElementById('backendDescription');
        
        if (!description) return;

        const descriptions = {
            'http': 'Fast and reliable for most documentation sites',
            'crawl4ai': 'AI-powered extraction with advanced content understanding',
            'lightpanda': 'JavaScript support for dynamic content',
            'playwright': 'Full browser automation for complex sites',
            'scrapy': 'High-performance crawling for large sites',
            'file': 'Local file system access for offline documentation'
        };

        description.textContent = descriptions[backend] || 'Select a backend for more information';
    }

    loadConfigPresets() {
        // This would load preset configurations from the server
        // For now, we'll use client-side presets
        const presets = {
            'default': {
                max_depth: 3,
                max_pages: 100,
                concurrent_requests: 5,
                delay: 1.0
            },
            'comprehensive': {
                max_depth: 5,
                max_pages: 500,
                concurrent_requests: 3,
                delay: 2.0
            },
            'performance': {
                max_depth: 2,
                max_pages: 50,
                concurrent_requests: 10,
                delay: 0.5
            },
            'javascript': {
                max_depth: 3,
                max_pages: 100,
                concurrent_requests: 2,
                delay: 3.0
            },
            'minimal': {
                max_depth: 1,
                max_pages: 10,
                concurrent_requests: 1,
                delay: 1.0
            }
        };

        this.configPresets = presets;
    }

    updateConfigPreset() {
        const preset = document.getElementById('configPreset')?.value;
        const presetDescription = document.getElementById('presetDescription');
        
        if (preset && this.configPresets[preset]) {
            const config = this.configPresets[preset];
            
            // Update form fields
            if (document.getElementById('maxDepth')) {
                document.getElementById('maxDepth').value = config.max_depth;
            }
            if (document.getElementById('maxPages')) {
                document.getElementById('maxPages').value = config.max_pages;
            }
            if (document.getElementById('concurrentRequests')) {
                document.getElementById('concurrentRequests').value = config.concurrent_requests;
            }
            if (document.getElementById('requestDelay')) {
                document.getElementById('requestDelay').value = config.delay;
            }

            // Update description
            const descriptions = {
                'default': 'Balanced configuration for most use cases',
                'comprehensive': 'Maximum coverage with thorough crawling',
                'performance': 'Fast crawling with minimal resource usage',
                'javascript': 'Optimized for JavaScript-heavy sites',
                'minimal': 'Lightweight configuration for testing'
            };

            if (presetDescription) {
                presetDescription.textContent = descriptions[preset] || '';
            }
        }
    }

    async runBenchmark() {
        const url = document.getElementById('docUrl')?.value;
        if (!url) {
            this.showError('Please enter a URL to benchmark');
            return;
        }

        try {
            this.showLoading();
            const response = await fetch('/api/benchmark', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ url, backends: 'all' })
            });

            const results = await response.json();
            this.displayBenchmarkResults(results);
        } catch (error) {
            console.error('Benchmark error:', error);
            this.showError('Benchmark failed');
        } finally {
            this.hideLoading();
        }
    }

    displayBenchmarkResults(results) {
        // Implementation for displaying benchmark results
        console.log('Benchmark results:', results);
        this.showSuccess('Benchmark completed - check console for results');
    }

    stopScraping() {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({
                type: 'stop_scraping',
                scraping_id: this.currentScrapingId
            }));
        }
        
        this.scrapingInProgress = false;
        this.updateUI(false);
        this.showInfo('Scraping stopped');
    }

    async downloadResults(format) {
        if (!this.currentScrapingId) {
            this.showError('No results to download');
            return;
        }

        try {
            const response = await fetch(`/api/scraping/download/${format}`);
            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `scraping_results.${format}`;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);
                this.showSuccess(`Results downloaded as ${format.toUpperCase()}`);
            } else {
                throw new Error('Download failed');
            }
        } catch (error) {
            console.error('Download error:', error);
            this.showError('Failed to download results');
        }
    }

    clearResults() {
        const resultsContainer = document.getElementById('scrapingResults');
        if (resultsContainer) {
            resultsContainer.innerHTML = '';
            resultsContainer.style.display = 'none';
        }
        
        this.currentScrapingId = null;
        this.resetMetrics();
        this.showInfo('Results cleared');
    }

    resetMetrics() {
        this.metrics = {
            pages_scraped: 0,
            successful_requests: 0,
            failed_requests: 0,
            current_depth: 0,
            pages_per_second: 0.0
        };
        this.updateMetrics(this.metrics);
    }

    updateUI(scraping) {
        const startBtn = document.getElementById('startScrapingBtn');
        const stopBtn = document.getElementById('stopScrapingBtn');
        const form = document.getElementById('scrapingForm');

        if (startBtn) {
            startBtn.disabled = scraping;
            startBtn.innerHTML = scraping ? 
                '<i class="bi bi-hourglass-split"></i> Scraping...' : 
                '<i class="bi bi-play-circle"></i> Start Scraping';
        }

        if (stopBtn) {
            stopBtn.style.display = scraping ? 'inline-block' : 'none';
        }

        if (form) {
            const inputs = form.querySelectorAll('input, select, textarea');
            inputs.forEach(input => {
                input.disabled = scraping;
            });
        }
    }

    updateConnectionStatus(connected) {
        const statusIndicator = document.getElementById('connectionStatus');
        if (statusIndicator) {
            statusIndicator.innerHTML = connected ? 
                '<i class="bi bi-wifi text-success"></i> Connected' :
                '<i class="bi bi-wifi-off text-danger"></i> Disconnected';
        }
    }

    updateScrapingStatus(status) {
        if (status.is_running) {
            this.scrapingInProgress = true;
            this.updateUI(true);
        } else {
            this.scrapingInProgress = false;
            this.updateUI(false);
        }
    }

    handleScrapingComplete(data) {
        this.scrapingInProgress = false;
        this.updateUI(false);
        this.showSuccess('Scraping completed successfully');
        
        if (data.results) {
            this.displayResults(data.results);
        }
    }

    handleScrapingError(data) {
        this.scrapingInProgress = false;
        this.updateUI(false);
        this.showError(`Scraping failed: ${data.error || 'Unknown error'}`);
    }

    viewDocument(url) {
        // Open document viewer in new tab/modal
        window.open(`/doc-viewer?url=${encodeURIComponent(url)}`, '_blank');
    }

    initializeTooltips() {
        // Initialize Bootstrap tooltips
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }

    showLoading() {
        const loadingIndicator = document.querySelector('.loading-indicator');
        if (loadingIndicator) {
            loadingIndicator.style.display = 'block';
        }
    }

    hideLoading() {
        const loadingIndicator = document.querySelector('.loading-indicator');
        if (loadingIndicator) {
            loadingIndicator.style.display = 'none';
        }
    }

    showError(message) {
        this.showAlert(message, 'danger');
    }

    showSuccess(message) {
        this.showAlert(message, 'success');
    }

    showInfo(message) {
        this.showAlert(message, 'info');
    }

    showAlert(message, type) {
        const alertContainer = document.getElementById('alertContainer') || this.createAlertContainer();
        
        const alertId = 'alert-' + Date.now();
        const alertHtml = `
            <div id="${alertId}" class="alert alert-${type} alert-dismissible fade show" role="alert">
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;
        
        alertContainer.insertAdjacentHTML('beforeend', alertHtml);
        
        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            const alert = document.getElementById(alertId);
            if (alert) {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            }
        }, 5000);
    }

    createAlertContainer() {
        const container = document.createElement('div');
        container.id = 'alertContainer';
        container.className = 'position-fixed top-0 end-0 p-3';
        container.style.zIndex = '1050';
        document.body.appendChild(container);
        return container;
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.dashboard = new ScrapingDashboard();
});

// Global functions for template usage
window.updateConfigPreset = function() {
    if (window.dashboard) {
        window.dashboard.updateConfigPreset();
    }
};