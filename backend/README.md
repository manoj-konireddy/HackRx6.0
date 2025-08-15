# Intelligent Query Retrieval System - Backend

This is the backend API for the Intelligent Query Retrieval System, built with FastAPI, PostgreSQL, and Pinecone vector database.

## 🏗️ Architecture

### Core Components
- **FastAPI**: Modern, fast web framework for building APIs
- **PostgreSQL**: Primary database for documents and metadata
- **Pinecone**: Vector database for semantic search
- **OpenRouter/DeepSeek**: LLM integration for intelligent responses
- **SQLAlchemy**: Async ORM for database operations

### Key Features
- 📄 **Document Processing**: Upload and process PDF, DOCX, DOC, EML files
- 🔍 **Hybrid Search**: Vector embeddings + text-based fallback
- 🌐 **Web Search Fallback**: Online search when documents don't contain answers
- 🛡️ **Duplicate Detection**: Hash-based duplicate prevention
- 📊 **Query History**: Track and store all queries and responses

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- PostgreSQL database
- Pinecone account (optional, has fallback)
- OpenRouter API key

### Installation

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and database settings
   ```

3. **Run the server:**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

## 📁 Project Structure

```
backend/
├── app/
│   ├── api/
│   │   ├── routes/
│   │   │   ├── documents.py    # Document upload/management
│   │   │   └── queries.py      # Query processing
│   │   └── schemas.py          # Pydantic models
│   ├── core/
│   │   └── database.py         # Database configuration
│   ├── models/
│   │   └── document.py         # SQLAlchemy models
│   ├── services/
│   │   ├── document_processor.py  # File processing
│   │   ├── vector_store.py        # Pinecone integration
│   │   ├── search_engine.py       # Hybrid search
│   │   ├── query_processor.py     # Query orchestration
│   │   └── llm_engine.py          # LLM integration
│   ├── config.py               # Configuration settings
│   └── main.py                 # FastAPI application
├── tests/                      # Test files
├── uploads/                    # Uploaded files storage
├── scripts/                    # Setup scripts
└── requirements.txt            # Python dependencies
```

## 🔧 Configuration

Key environment variables in `.env`:

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/db_name

# OpenRouter/DeepSeek (Required)
OPENAI_API_KEY=your_openrouter_api_key
OPENAI_MODEL=deepseek/deepseek-r1-0528:free
OPENAI_BASE_URL=https://openrouter.ai/api/v1

# Pinecone (Optional)
PINECONE_API_KEY=your_pinecone_api_key
PINECONE_ENVIRONMENT=us-east1-gcp
PINECONE_INDEX_NAME=document-retrieval

# Features
ENABLE_EMBEDDINGS=true
```

## 📚 API Endpoints

### Document Management
- `POST /api/v1/documents/upload` - Upload and process documents
- `GET /api/v1/documents` - List documents with pagination
- `GET /api/v1/documents/{id}` - Get document details
- `DELETE /api/v1/documents/{id}` - Delete document

### Query Processing
- `POST /api/v1/query` - Process natural language queries
- `GET /api/v1/queries/history` - Get query history
- `GET /api/v1/queries/{id}` - Get specific query details

## 🧪 Testing

Run the test suite:
```bash
# Basic functionality test
python test_simple_query.py

# Document upload test
python test_document_search.py

# API tests
python -m pytest tests/
```

## 🐳 Docker Support

Build and run with Docker:
```bash
docker-compose up --build
```

## 🔍 How It Works

1. **Document Upload**: Files are processed, chunked, and stored
2. **Embedding Generation**: Text chunks are converted to vector embeddings
3. **Vector Storage**: Embeddings stored in Pinecone for semantic search
4. **Query Processing**: 
   - Search documents using vector similarity
   - Fall back to text-based search if needed
   - Use web search if no relevant documents found
5. **LLM Response**: Generate intelligent answers using retrieved context

## 🛠️ Development

### Adding New Features
- **Document Types**: Extend `document_processor.py`
- **Search Methods**: Modify `search_engine.py`
- **LLM Models**: Update `llm_engine.py`
- **API Endpoints**: Add routes in `api/routes/`

### Database Migrations
The system uses SQLAlchemy with automatic table creation. For production, implement proper migrations.

## 📊 Monitoring

The system includes structured logging with:
- Query processing times
- Search result counts
- Error tracking
- Performance metrics

## 🔒 Security

- Input validation with Pydantic
- SQL injection prevention with SQLAlchemy
- File type restrictions for uploads
- Environment-based configuration
