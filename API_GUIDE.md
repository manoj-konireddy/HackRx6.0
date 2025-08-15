# API Guide - Intelligent Query Retrieval System

This guide provides comprehensive documentation for using the Intelligent Query Retrieval System API.

## Base URL

```
http://localhost:8000/api/v1
```

## Authentication

Currently, the API does not require authentication. For production deployment, implement proper authentication mechanisms.

## Content Types

- Request: `application/json` (for JSON endpoints) or `multipart/form-data` (for file uploads)
- Response: `application/json`

## Error Handling

All endpoints return structured error responses:

```json
{
  "error": "error_type",
  "message": "Human-readable error message",
  "details": {
    "additional": "error details"
  }
}
```

Common HTTP status codes:
- `200`: Success
- `400`: Bad Request (validation errors)
- `404`: Not Found
- `422`: Unprocessable Entity (validation errors)
- `500`: Internal Server Error

## Endpoints

### Health Check

#### GET /health
Basic health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "service": "Intelligent Query Retrieval System",
  "version": "1.0.0"
}
```

#### GET /health/detailed
Detailed health check with system information.

**Response:**
```json
{
  "status": "healthy",
  "service": "Intelligent Query Retrieval System",
  "version": "1.0.0",
  "environment": {
    "debug": false,
    "log_level": "INFO"
  },
  "features": {
    "document_processing": true,
    "vector_search": true,
    "llm_integration": true,
    "supported_domains": ["insurance", "legal", "hr", "compliance", "general"]
  }
}
```

### Document Management

#### POST /documents/upload
Upload and process a document.

**Request:**
- Content-Type: `multipart/form-data`
- Body:
  - `file`: Document file (PDF, DOCX, or email)
  - `domain` (optional): Domain hint ("insurance", "legal", "hr", "compliance")

**Example:**
```bash
curl -X POST "http://localhost:8000/api/v1/documents/upload" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@insurance_policy.pdf" \
  -F "domain=insurance"
```

**Response:**
```json
{
  "document_id": 123,
  "filename": "insurance_policy.pdf",
  "file_type": "pdf",
  "file_size": 1048576,
  "processing_status": "completed",
  "domain": "insurance",
  "message": "Document uploaded and processed successfully"
}
```

#### GET /documents
List documents with pagination and filtering.

**Query Parameters:**
- `page` (int, default: 1): Page number
- `page_size` (int, default: 20): Items per page
- `domain` (string, optional): Filter by domain
- `status` (string, optional): Filter by processing status

**Example:**
```bash
curl "http://localhost:8000/api/v1/documents?page=1&page_size=10&domain=insurance"
```

**Response:**
```json
{
  "documents": [
    {
      "id": 123,
      "filename": "insurance_policy.pdf",
      "file_type": "pdf",
      "file_size": 1048576,
      "domain": "insurance",
      "processing_status": "completed",
      "created_at": "2024-01-15T10:30:00Z",
      "processed_at": "2024-01-15T10:31:30Z",
      "chunk_count": 25
    }
  ],
  "total_count": 1,
  "page": 1,
  "page_size": 10
}
```

#### GET /documents/{document_id}
Get detailed information about a specific document.

**Response:**
```json
{
  "id": 123,
  "filename": "insurance_policy.pdf",
  "original_filename": "insurance_policy.pdf",
  "file_type": "pdf",
  "file_size": 1048576,
  "domain": "insurance",
  "processing_status": "completed",
  "created_at": "2024-01-15T10:30:00Z",
  "processed_at": "2024-01-15T10:31:30Z",
  "chunk_count": 25,
  "metadata": {
    "title": "Health Insurance Policy",
    "author": "Insurance Company",
    "subject": "Policy Terms and Conditions",
    "file_hash": "abc123..."
  }
}
```

#### DELETE /documents/{document_id}
Delete a document and all associated data.

**Response:**
```json
{
  "message": "Document deleted successfully",
  "document_id": 123
}
```

### Query Processing

#### POST /query
Process a natural language query against documents.

**Request Body:**
```json
{
  "query": "Does this policy cover knee surgery, and what are the conditions?",
  "document_id": 123,  // optional: search within specific document
  "domain": "insurance",  // optional: domain hint
  "max_results": 5  // optional: maximum search results
}
```

**Response:**
```json
{
  "query": "Does this policy cover knee surgery, and what are the conditions?",
  "domain": "insurance",
  "answer": "Yes, this policy covers knee surgery including joint replacement procedures. Coverage is provided at 80% after meeting the annual deductible of $1,500. Pre-authorization is required for non-emergency procedures.",
  "reasoning": "Based on the policy documents, knee surgery is explicitly listed under covered procedures in Section 3.2. The coverage details specify that orthopedic surgeries, including knee replacement, are covered benefits subject to standard deductible and coinsurance terms.",
  "confidence_score": 0.92,
  "supporting_evidence": [
    "Section 3.2: Covered surgical procedures include orthopedic surgeries such as knee and hip replacements",
    "Page 15: Knee replacement surgery is covered at 80% after deductible",
    "Section 5.1: Pre-authorization required for non-emergency surgical procedures"
  ],
  "limitations": [
    "Pre-authorization required for non-emergency procedures",
    "Annual deductible of $1,500 must be met",
    "Coverage subject to medical necessity determination"
  ],
  "follow_up_questions": [
    "Do you need information about the pre-authorization process?",
    "Would you like details about the claims submission procedure?",
    "Are you interested in coverage for physical therapy after surgery?"
  ],
  "search_results": [
    {
      "vector_id": "doc_123_chunk_5",
      "score": 0.95,
      "adjusted_score": 0.98,
      "content": "Covered surgical procedures include orthopedic surgeries...",
      "document_id": 123,
      "chunk_index": 5,
      "metadata": {
        "start_char": 2500,
        "end_char": 3500
      }
    }
  ],
  "total_processing_time_ms": 1250,
  "metadata": {
    "search_time_ms": 500,
    "llm_model": "gpt-4-turbo-preview",
    "total_chunks_found": 8
  }
}
```

#### GET /queries/history
Get query history with pagination and filtering.

**Query Parameters:**
- `page` (int, default: 1): Page number
- `page_size` (int, default: 20): Items per page
- `document_id` (int, optional): Filter by document ID
- `domain` (string, optional): Filter by domain

**Response:**
```json
{
  "queries": [
    {
      "id": 456,
      "query_text": "Does this policy cover knee surgery?",
      "domain": "insurance",
      "document_id": 123,
      "confidence_score": 0.92,
      "processing_time_ms": 1250,
      "created_at": "2024-01-15T11:00:00Z",
      "response_summary": "Yes, this policy covers knee surgery including joint replacement procedures..."
    }
  ],
  "total_count": 1,
  "page": 1,
  "page_size": 20
}
```

#### GET /queries/{query_id}
Get detailed information about a specific query.

**Response:**
```json
{
  "id": 456,
  "query_text": "Does this policy cover knee surgery?",
  "query_type": "semantic_search",
  "domain": "insurance",
  "document_id": 123,
  "response": {
    // Full query response object
  },
  "confidence_score": 0.92,
  "processing_time_ms": 1250,
  "retrieved_chunks": [
    {
      "vector_id": "doc_123_chunk_5",
      "score": 0.95
    }
  ],
  "llm_reasoning": "Based on the policy documents...",
  "created_at": "2024-01-15T11:00:00Z"
}
```

### Domain Information

#### GET /domains
Get information about supported domains.

**Response:**
```json
{
  "supported_domains": {
    "insurance": {
      "name": "Insurance",
      "description": "Insurance policies, coverage, claims, and benefits",
      "sample_queries": [
        "Does this policy cover dental procedures?",
        "What is the deductible for emergency room visits?",
        "How do I file a claim for this treatment?"
      ]
    },
    "legal": {
      "name": "Legal",
      "description": "Contracts, agreements, legal clauses, and obligations",
      "sample_queries": [
        "What are the liability limitations in this contract?",
        "When does this agreement expire?",
        "What are the termination conditions?"
      ]
    }
    // ... other domains
  },
  "default_domain": "general",
  "auto_detection": "The system can automatically detect the domain based on query content"
}
```

#### GET /query/sample
Get sample queries for testing.

**Response:**
```json
{
  "message": "Sample queries for testing the system",
  "sample_queries": [
    {
      "query": "Does this policy cover knee surgery, and what are the conditions?",
      "domain": "insurance",
      "description": "Sample insurance coverage query"
    }
    // ... more samples
  ],
  "usage": "Use POST /api/v1/query with one of these sample queries to test the system"
}
```

## Usage Examples

### Complete Workflow Example

1. **Upload a document:**
```bash
curl -X POST "http://localhost:8000/api/v1/documents/upload" \
  -F "file=@policy.pdf" \
  -F "domain=insurance"
```

2. **Query the document:**
```bash
curl -X POST "http://localhost:8000/api/v1/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is covered under this policy?",
    "document_id": 123,
    "domain": "insurance"
  }'
```

3. **Check query history:**
```bash
curl "http://localhost:8000/api/v1/queries/history?document_id=123"
```

### Domain-Specific Examples

#### Insurance Query
```json
{
  "query": "Does this policy cover knee surgery, and what are the conditions?",
  "domain": "insurance",
  "max_results": 5
}
```

#### Legal Query
```json
{
  "query": "What are the termination clauses in this contract?",
  "domain": "legal",
  "max_results": 10
}
```

#### HR Query
```json
{
  "query": "What is the vacation policy for new employees?",
  "domain": "hr",
  "max_results": 3
}
```

#### Compliance Query
```json
{
  "query": "What are the audit requirements for this process?",
  "domain": "compliance",
  "max_results": 7
}
```

## Rate Limits

Currently, no rate limits are implemented. For production deployment, consider implementing rate limiting based on your requirements.

## Best Practices

1. **Document Upload**: Use appropriate domain hints for better processing
2. **Query Formulation**: Be specific and clear in your queries
3. **Domain Selection**: Use domain-specific queries for better results
4. **Error Handling**: Always check response status codes
5. **Pagination**: Use pagination for large result sets

## Interactive API Documentation

Visit `http://localhost:8000/docs` for interactive Swagger UI documentation where you can test all endpoints directly in your browser.
