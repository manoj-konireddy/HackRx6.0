// Intelligent Query Retrieval System - Frontend Application

class QueryRetrievalApp {
    constructor() {
        this.apiBase = 'http://localhost:8000/api/v1';
        this.currentSection = 'documents';
        this.documents = [];
        this.queries = [];
        
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadDocuments();
        this.showSection('documents');
    }

    setupEventListeners() {
        // Navigation
        document.getElementById('documentsTab').addEventListener('click', () => this.showSection('documents'));
        document.getElementById('queryTab').addEventListener('click', () => this.showSection('query'));
        document.getElementById('historyTab').addEventListener('click', () => this.showSection('history'));

        // File Upload
        const uploadArea = document.getElementById('uploadArea');
        const fileInput = document.getElementById('fileInput');

        uploadArea.addEventListener('click', () => fileInput.click());
        uploadArea.addEventListener('dragover', this.handleDragOver.bind(this));
        uploadArea.addEventListener('dragleave', this.handleDragLeave.bind(this));
        uploadArea.addEventListener('drop', this.handleDrop.bind(this));
        fileInput.addEventListener('change', this.handleFileSelect.bind(this));

        // Buttons
        document.getElementById('refreshDocs').addEventListener('click', () => this.loadDocuments());
        document.getElementById('submitQuery').addEventListener('click', () => this.submitQuery());

        // Enter key for query
        document.getElementById('queryInput').addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && e.ctrlKey) {
                this.submitQuery();
            }
        });
    }

    showSection(section) {
        // Hide all sections
        document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
        document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));

        // Show selected section
        document.getElementById(`${section}Section`).classList.add('active');
        document.getElementById(`${section}Tab`).classList.add('active');

        this.currentSection = section;

        // Load data for section
        if (section === 'query') {
            this.loadDocumentsForQuery();
        } else if (section === 'history') {
            this.loadQueryHistory();
        }
    }

    // File Upload Handlers
    handleDragOver(e) {
        e.preventDefault();
        document.getElementById('uploadArea').classList.add('dragover');
    }

    handleDragLeave(e) {
        e.preventDefault();
        document.getElementById('uploadArea').classList.remove('dragover');
    }

    handleDrop(e) {
        e.preventDefault();
        document.getElementById('uploadArea').classList.remove('dragover');
        const files = Array.from(e.dataTransfer.files);
        this.uploadFiles(files);
    }

    handleFileSelect(e) {
        const files = Array.from(e.target.files);
        this.uploadFiles(files);
    }

    async uploadFiles(files) {
        const domain = document.getElementById('domainSelect').value;
        const progressContainer = document.getElementById('uploadProgress');
        const progressBar = document.getElementById('progressBar');
        const progressText = document.getElementById('progressText');

        progressContainer.classList.remove('hidden');

        for (let i = 0; i < files.length; i++) {
            const file = files[i];
            const formData = new FormData();
            formData.append('file', file);
            formData.append('domain', domain);

            try {
                progressText.textContent = `Uploading ${file.name}...`;
                progressBar.style.width = `${((i + 0.5) / files.length) * 100}%`;

                const response = await fetch(`${this.apiBase}/documents/upload`, {
                    method: 'POST',
                    body: formData
                });

                const result = await response.json();

                if (response.ok) {
                    this.showToast(`Successfully uploaded ${file.name}`, 'success');
                } else {
                    this.showToast(`Failed to upload ${file.name}: ${result.detail}`, 'error');
                }

                progressBar.style.width = `${((i + 1) / files.length) * 100}%`;
            } catch (error) {
                this.showToast(`Error uploading ${file.name}: ${error.message}`, 'error');
            }
        }

        progressText.textContent = 'Upload complete!';
        setTimeout(() => {
            progressContainer.classList.add('hidden');
            progressBar.style.width = '0%';
        }, 2000);

        // Refresh documents list
        this.loadDocuments();
        
        // Clear file input
        document.getElementById('fileInput').value = '';
    }

    async loadDocuments() {
        try {
            const response = await fetch(`${this.apiBase}/documents`);
            const data = await response.json();

            if (response.ok) {
                this.documents = data.documents;
                this.renderDocuments();
            } else {
                this.showToast('Failed to load documents', 'error');
            }
        } catch (error) {
            this.showToast(`Error loading documents: ${error.message}`, 'error');
        }
    }

    renderDocuments() {
        const tbody = document.getElementById('documentsTable');
        tbody.innerHTML = '';

        if (this.documents.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="5" class="px-6 py-4 text-center text-gray-500">
                        No documents uploaded yet. Upload some documents to get started!
                    </td>
                </tr>
            `;
            return;
        }

        this.documents.forEach(doc => {
            const row = document.createElement('tr');
            row.className = 'table-row';
            row.innerHTML = `
                <td class="px-6 py-4 whitespace-nowrap">
                    <div class="flex items-center">
                        <i class="fas fa-file-alt text-gray-400 mr-3"></i>
                        <div>
                            <div class="text-sm font-medium text-gray-900">${doc.filename}</div>
                            <div class="text-sm text-gray-500">${this.formatFileSize(doc.file_size)}</div>
                        </div>
                    </div>
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                    <span class="domain-badge domain-${doc.domain}">${doc.domain}</span>
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                    <span class="status-badge status-${doc.processing_status}">${doc.processing_status}</span>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    ${this.formatDate(doc.created_at)}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <button onclick="app.deleteDocument(${doc.id})" class="text-red-600 hover:text-red-900">
                        <i class="fas fa-trash"></i>
                    </button>
                </td>
            `;
            tbody.appendChild(row);
        });
    }

    async deleteDocument(documentId) {
        if (!confirm('Are you sure you want to delete this document?')) {
            return;
        }

        try {
            const response = await fetch(`${this.apiBase}/documents/${documentId}`, {
                method: 'DELETE'
            });

            if (response.ok) {
                this.showToast('Document deleted successfully', 'success');
                this.loadDocuments();
            } else {
                const result = await response.json();
                this.showToast(`Failed to delete document: ${result.detail}`, 'error');
            }
        } catch (error) {
            this.showToast(`Error deleting document: ${error.message}`, 'error');
        }
    }

    loadDocumentsForQuery() {
        const select = document.getElementById('queryDocument');
        select.innerHTML = '<option value="">All Documents</option>';

        this.documents
            .filter(doc => doc.processing_status === 'completed')
            .forEach(doc => {
                const option = document.createElement('option');
                option.value = doc.id;
                option.textContent = doc.filename;
                select.appendChild(option);
            });
    }

    async submitQuery() {
        const query = document.getElementById('queryInput').value.trim();
        const domain = document.getElementById('queryDomain').value;
        const documentId = document.getElementById('queryDocument').value;

        if (!query) {
            this.showToast('Please enter a question', 'warning');
            return;
        }

        const submitButton = document.getElementById('submitQuery');
        const originalText = submitButton.innerHTML;
        submitButton.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Processing...';
        submitButton.disabled = true;

        try {
            const requestBody = {
                query: query,
                max_results: 10
            };

            if (domain) requestBody.domain = domain;
            if (documentId) requestBody.document_id = parseInt(documentId);

            const response = await fetch(`${this.apiBase}/query`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(requestBody)
            });

            const result = await response.json();

            if (response.ok) {
                this.displayQueryResult(result);
                this.showToast('Query processed successfully', 'success');
            } else {
                this.showToast(`Query failed: ${result.detail}`, 'error');
            }
        } catch (error) {
            this.showToast(`Error processing query: ${error.message}`, 'error');
        } finally {
            submitButton.innerHTML = originalText;
            submitButton.disabled = false;
        }
    }

    displayQueryResult(result) {
        const resultsDiv = document.getElementById('queryResults');
        const answerContent = document.getElementById('answerContent');
        const sourceList = document.getElementById('sourceList');

        // Show results section
        resultsDiv.classList.remove('hidden');
        resultsDiv.scrollIntoView({ behavior: 'smooth' });

        // Display answer
        answerContent.innerHTML = `
            <div class="answer-content">
                <p>${result.response}</p>
                <div class="mt-4 text-sm text-gray-600">
                    <span class="font-medium">Confidence:</span> 
                    <span class="confidence-${this.getConfidenceClass(result.confidence_score)}">
                        ${Math.round(result.confidence_score * 100)}%
                    </span>
                    <span class="ml-4 font-medium">Processing Time:</span> ${result.processing_time_ms}ms
                </div>
            </div>
        `;

        // Display source documents
        sourceList.innerHTML = '';
        if (result.search_results && result.search_results.length > 0) {
            result.search_results.forEach(source => {
                const sourceDiv = document.createElement('div');
                sourceDiv.className = 'source-doc';
                sourceDiv.innerHTML = `
                    <div class="flex justify-between items-start">
                        <div>
                            <div class="font-medium text-gray-900">${source.metadata.document_title || 'Unknown Document'}</div>
                            <div class="text-sm text-gray-600 mt-1">${source.content.substring(0, 200)}...</div>
                        </div>
                        <div class="text-sm text-gray-500">
                            Score: ${Math.round(source.score * 100)}%
                        </div>
                    </div>
                `;
                sourceList.appendChild(sourceDiv);
            });
        } else {
            sourceList.innerHTML = '<p class="text-gray-500">No source documents found.</p>';
        }
    }

    async loadQueryHistory() {
        try {
            const response = await fetch(`${this.apiBase}/queries/history`);
            const data = await response.json();

            if (response.ok) {
                this.queries = data.queries;
                this.renderQueryHistory();
            } else {
                this.showToast('Failed to load query history', 'error');
            }
        } catch (error) {
            this.showToast(`Error loading query history: ${error.message}`, 'error');
        }
    }

    renderQueryHistory() {
        const historyList = document.getElementById('historyList');
        historyList.innerHTML = '';

        if (this.queries.length === 0) {
            historyList.innerHTML = `
                <div class="text-center text-gray-500 py-8">
                    <i class="fas fa-history text-4xl mb-4"></i>
                    <p>No queries yet. Ask your first question!</p>
                </div>
            `;
            return;
        }

        this.queries.forEach(query => {
            const historyItem = document.createElement('div');
            historyItem.className = 'history-item';
            historyItem.innerHTML = `
                <div class="flex justify-between items-start">
                    <div class="flex-1">
                        <div class="font-medium text-gray-900 mb-2">${query.query}</div>
                        <div class="text-sm text-gray-600 mb-2">${query.response.substring(0, 200)}...</div>
                        <div class="flex items-center space-x-4 text-xs text-gray-500">
                            <span><i class="fas fa-clock mr-1"></i>${this.formatDate(query.created_at)}</span>
                            <span><i class="fas fa-chart-line mr-1"></i>${Math.round(query.confidence_score * 100)}%</span>
                            <span><i class="fas fa-stopwatch mr-1"></i>${query.processing_time_ms}ms</span>
                        </div>
                    </div>
                </div>
            `;
            historyList.appendChild(historyItem);
        });
    }

    // Utility Functions
    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    formatDate(dateString) {
        return new Date(dateString).toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    }

    getConfidenceClass(score) {
        if (score >= 0.8) return 'high';
        if (score >= 0.5) return 'medium';
        return 'low';
    }

    showToast(message, type = 'info') {
        const container = document.getElementById('toastContainer');
        const toast = document.createElement('div');
        toast.className = `toast ${type} fade-in`;
        
        const icon = {
            success: 'fas fa-check-circle text-green-500',
            error: 'fas fa-exclamation-circle text-red-500',
            warning: 'fas fa-exclamation-triangle text-yellow-500',
            info: 'fas fa-info-circle text-blue-500'
        }[type];

        toast.innerHTML = `
            <div class="flex items-center">
                <i class="${icon} mr-3"></i>
                <span>${message}</span>
                <button onclick="this.parentElement.parentElement.remove()" class="ml-4 text-gray-400 hover:text-gray-600">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `;

        container.appendChild(toast);

        // Auto remove after 5 seconds
        setTimeout(() => {
            if (toast.parentElement) {
                toast.remove();
            }
        }, 5000);
    }
}

// Initialize the application
const app = new QueryRetrievalApp();
