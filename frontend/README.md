# Frontend - Intelligent Query Retrieval System

A modern, responsive web interface for the Intelligent Query Retrieval System built with vanilla JavaScript, HTML5, and Tailwind CSS.

## 🌟 Features

### 📄 Document Management
- **Drag & Drop Upload**: Intuitive file upload with drag-and-drop support
- **Multiple File Types**: Support for PDF, DOCX, DOC, and EML files
- **Domain Classification**: Organize documents by domain (Insurance, Legal, HR, Compliance, General)
- **Real-time Status**: Live upload progress and processing status
- **Document Library**: View all uploaded documents with metadata

### 🔍 Intelligent Querying
- **Natural Language**: Ask questions in plain English
- **Domain Filtering**: Filter queries by specific domains
- **Document-Specific**: Query specific documents or all documents
- **Confidence Scoring**: See how confident the AI is in its answers
- **Source Attribution**: View which documents were used to generate answers

### 📊 Query History
- **Complete History**: View all previous queries and responses
- **Performance Metrics**: See processing times and confidence scores
- **Easy Navigation**: Quickly find and review past interactions

### 🎨 Modern UI/UX
- **Responsive Design**: Works perfectly on desktop, tablet, and mobile
- **Clean Interface**: Professional, intuitive design
- **Real-time Feedback**: Toast notifications and loading states
- **Accessibility**: WCAG compliant with keyboard navigation

## 🚀 Quick Start

### Prerequisites
- Python 3.7+ (for the development server)
- Backend API running on `http://localhost:8000`

### Starting the Frontend

**Option 1: Using the batch file (Windows)**
```bash
start_frontend.bat
```

**Option 2: Using Python directly**
```bash
python serve.py
```

The frontend will be available at: `http://localhost:3000`

## 📁 Project Structure

```
frontend/
├── index.html              # Main HTML file
├── styles.css              # Custom CSS styles
├── app.js                  # JavaScript application logic
├── serve.py                # Python development server
├── start_frontend.bat      # Windows startup script
└── FRONTEND_README.md      # This file
```

## 🎯 Usage Guide

### 1. Upload Documents
1. Navigate to the **Documents** tab
2. Select a domain for your documents
3. Drag and drop files or click to select
4. Wait for processing to complete

### 2. Ask Questions
1. Go to the **Query** tab
2. Type your question in natural language
3. Optionally filter by domain or specific document
4. Click "Ask Question" or press Ctrl+Enter
5. View the AI-generated answer and source documents

### 3. Review History
1. Visit the **History** tab
2. Browse through all previous queries
3. See confidence scores and processing times

## 🔌 API Integration

The frontend communicates with the backend through these endpoints:

- `GET /api/v1/documents` - List all documents
- `POST /api/v1/documents/upload` - Upload new documents
- `DELETE /api/v1/documents/{id}` - Delete a document
- `POST /api/v1/query` - Submit a query
- `GET /api/v1/queries/history` - Get query history

## 📱 Mobile Support

The frontend is fully responsive and works on:
- Desktop computers (1024px+)
- Tablets (768px - 1023px)
- Mobile phones (320px - 767px)

## 🐛 Troubleshooting

### Common Issues

**Frontend won't start:**
- Ensure Python 3.7+ is installed
- Check if port 3000 is available

**Can't connect to backend:**
- Verify backend is running on `http://localhost:8000`
- Check for CORS issues

**File uploads fail:**
- Check file size limits
- Verify supported file types
- Ensure backend upload endpoint is working

---

**Built with ❤️ using vanilla JavaScript, HTML5, and Tailwind CSS**
