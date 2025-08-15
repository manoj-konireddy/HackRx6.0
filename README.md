# Intelligent Query-Retrieval System

An LLM-powered intelligent query-retrieval system that processes large documents and makes contextual decisions for insurance, legal, HR, and compliance domains.

## 🏗️ Project Structure

```
HackRx6_0/
├── backend/                    # Backend API (FastAPI)
│   ├── app/                   # Main application code
│   │   ├── api/               # API routes and schemas
│   │   ├── core/              # Database configuration
│   │   ├── models/            # SQLAlchemy models
│   │   ├── services/          # Business logic services
│   │   ├── config.py          # Configuration settings
│   │   └── main.py            # FastAPI application
│   ├── tests/                 # Backend tests
│   ├── uploads/               # File storage
│   ├── requirements.txt       # Python dependencies
│   ├── .env                   # Environment configuration
│   └── README.md              # Backend documentation
├── frontend/                  # 🌐 Modern Web Interface
│   ├── index.html             # Main HTML file
│   ├── styles.css             # Custom CSS styles
│   ├── app.js                 # JavaScript application logic
│   ├── serve.py               # Development server
│   ├── start_frontend.bat     # Windows startup script
│   └── README.md              # Frontend documentation
├── venv/                      # Python virtual environment
└── README.md                  # This file
```

## Features

- **Multi-format Document Processing**: Supports PDF, DOCX, and email documents
- **Semantic Search**: Advanced vector-based similarity search using embeddings
- **Domain-Specific Intelligence**: Specialized processing for insurance, legal, HR, and compliance queries
- **LLM-Powered Analysis**: DeepSeek integration for contextual understanding and explainable decisions
- **RESTful API**: FastAPI-based backend with comprehensive endpoints
- **Scalable Architecture**: PostgreSQL + Pinecone/FAISS for production-ready deployment

## Tech Stack

- **Backend**: FastAPI, Python 3.8+
- **Database**: PostgreSQL (metadata), Pinecone/FAISS (vectors)
- **LLM**: DeepSeek via OpenRouter
- **Document Processing**: PyPDF2, python-docx, email parsing
- **Vector Search**: Pinecone (primary), FAISS (fallback)

## Quick Start

### Prerequisites

- Python 3.8+
- PostgreSQL database
- OpenRouter API key (for DeepSeek access)
- Pinecone account (optional, FAISS used as fallback)

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd HackRx6_0
```

2. Navigate to backend and install dependencies:
```bash
cd backend
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your API keys and database configuration
```

4. Initialize the database:
```bash
# Create PostgreSQL database
createdb intelligent_query_db

# Run the backend server (it will create tables automatically)
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`
- API Documentation: `http://localhost:8000/docs`
- Alternative docs: `http://localhost:8000/redoc`

5. Start the frontend (in a new terminal):
```bash
cd frontend
python serve.py
```

The frontend will be available at `http://localhost:3000`

### Configuration

Edit `.env` file with your settings:

```env
# OpenRouter/DeepSeek Configuration
OPENAI_API_KEY=your_openrouter_api_key_here
OPENAI_MODEL=deepseek/deepseek-r1-0528:free
OPENAI_BASE_URL=https://openrouter.ai/api/v1

# Pinecone Configuration (optional)
PINECONE_API_KEY=your_pinecone_api_key_here
PINECONE_ENVIRONMENT=your_pinecone_environment
PINECONE_INDEX_NAME=document-retrieval

# PostgreSQL Configuration
DATABASE_URL=postgresql://username:password@localhost:5432/intelligent_query_db

# Application Configuration
MAX_FILE_SIZE_MB=50
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
SIMILARITY_THRESHOLD=0.7
```

## API Usage

### 1. Upload a Document

```bash
curl -X POST "http://localhost:8000/api/v1/documents/upload" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@your_document.pdf" \
  -F "domain=insurance"
```

### 2. Query Documents

```bash
curl -X POST "http://localhost:8000/api/v1/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Does this policy cover knee surgery, and what are the conditions?",
    "domain": "insurance",
    "max_results": 5
  }'
```

### 3. Sample Response

```json
{
  "query": "Does this policy cover knee surgery, and what are the conditions?",
  "domain": "insurance",
  "answer": "Yes, this policy covers knee surgery including joint replacement procedures. The coverage includes...",
  "reasoning": "Based on the policy documents, knee surgery is explicitly listed under covered procedures...",
  "confidence_score": 0.92,
  "supporting_evidence": [
    "Section 3.2: Covered surgical procedures include orthopedic surgeries...",
    "Page 15: Knee replacement surgery is covered at 80% after deductible..."
  ],
  "limitations": [
    "Pre-authorization required for non-emergency procedures",
    "Annual deductible of $1,500 must be met"
  ],
  "follow_up_questions": [
    "Do you need information about pre-authorization requirements?",
    "Would you like details about the claims process?"
  ],
  "total_processing_time_ms": 1250
}
```

## Supported Domains

### Insurance
- Policy coverage analysis
- Claims processing guidance
- Benefits explanation
- Exclusions identification

### Legal
- Contract clause analysis
- Terms and conditions interpretation
- Liability assessment
- Compliance requirements

### HR
- Employee policy queries
- Benefits information
- Workplace procedures
- Performance guidelines

### Compliance
- Regulatory requirements
- Audit procedures
- Standards compliance
- Documentation requirements

## API Endpoints

### Documents
- `POST /api/v1/documents/upload` - Upload and process documents
- `GET /api/v1/documents` - List documents with filtering
- `GET /api/v1/documents/{id}` - Get document details
- `DELETE /api/v1/documents/{id}` - Delete document

### Queries
- `POST /api/v1/query` - Process natural language queries
- `GET /api/v1/queries/history` - Get query history
- `GET /api/v1/queries/{id}` - Get query details
- `GET /api/v1/domains` - Get supported domains

### Health
- `GET /api/v1/health` - Basic health check
- `GET /api/v1/health/detailed` - Detailed system status

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app tests/

# Run specific test file
pytest tests/test_document_processor.py -v
```

### Code Quality

```bash
# Format code
black app/ tests/

# Lint code
flake8 app/ tests/

# Type checking
mypy app/
```

## Deployment

### Docker Deployment

```bash
# Build image
docker build -t intelligent-query-system .

# Run with docker-compose
docker-compose up -d
```

### Production Considerations

1. **Environment Variables**: Use secure secret management
2. **Database**: Configure PostgreSQL with proper indexing
3. **Vector Store**: Set up Pinecone for production scale
4. **Monitoring**: Implement logging and metrics collection
5. **Security**: Add authentication and rate limiting
6. **Scaling**: Consider horizontal scaling for high load

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   FastAPI       │    │  Document        │    │  Vector Store   │
│   Web Server    │───▶│  Processor       │───▶│  (Pinecone/     │
│                 │    │                  │    │   FAISS)        │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Query         │    │  PostgreSQL      │    │  OpenAI GPT-4   │
│   Processor     │───▶│  Database        │    │  LLM Engine     │
│                 │    │                  │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
