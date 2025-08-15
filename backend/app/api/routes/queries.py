"""Query processing endpoints."""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query as QueryParam
from sqlalchemy.orm import Session
from sqlalchemy import desc, select, func
import structlog

from app.core.database import get_db
from app.models.document import Query, Document
from app.services.query_processor import QueryProcessor
from app.api.schemas import QueryRequest, QueryResponse, SearchResult

logger = structlog.get_logger()
router = APIRouter()

# Initialize query processor
query_processor = QueryProcessor()


@router.post("/query", response_model=QueryResponse)
async def process_query(
    request: QueryRequest,
    db: Session = Depends(get_db)
):
    """Process a natural language query against documents."""

    try:
        # Validate document exists if document_id is provided
        if request.document_id:
            document_result = await db.execute(
                select(Document).where(Document.id == request.document_id)
            )
            document = document_result.scalar_one_or_none()
            if not document:
                raise HTTPException(
                    status_code=404, detail="Document not found")

            if document.processing_status != 'completed':
                raise HTTPException(
                    status_code=400,
                    detail=f"Document is not ready for querying. Status: {document.processing_status}"
                )

        # Process the query
        result = await query_processor.process_query(
            query=request.query,
            document_id=request.document_id,
            domain=request.domain
        )

        # Format search results for response
        search_results = []
        for search_result in result['search_results']:
            search_results.append(SearchResult(
                vector_id=search_result.get(
                    'vector_id', search_result.get('id', 'unknown')),
                score=search_result.get('score', 0.0),
                adjusted_score=search_result.get('adjusted_score'),
                content=search_result['metadata']['content'],
                document_id=search_result['metadata']['document_id'],
                chunk_index=search_result['metadata']['chunk_index'],
                metadata=search_result['metadata']
            ))

        # Create response
        response = QueryResponse(
            query=result['query'],
            domain=result['domain'],
            answer=result['answer'],
            reasoning=result['reasoning'],
            confidence_score=result['confidence_score'],
            supporting_evidence=result['supporting_evidence'],
            limitations=result['limitations'],
            follow_up_questions=result['follow_up_questions'],
            search_results=search_results,
            total_processing_time_ms=result['total_processing_time_ms'],
            metadata=result['metadata']
        )

        logger.info("Query processed successfully",
                    query_length=len(request.query),
                    domain=result['domain'],
                    confidence=result['confidence_score'])

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Query processing failed",
                     query=request.query, error=str(e))
        raise HTTPException(
            status_code=500, detail=f"Query processing failed: {str(e)}")


@router.get("/queries/history")
async def get_query_history(
    page: int = QueryParam(1, ge=1, description="Page number"),
    page_size: int = QueryParam(
        20, ge=1, le=100, description="Items per page"),
    document_id: Optional[int] = QueryParam(
        None, description="Filter by document ID"),
    domain: Optional[str] = QueryParam(None, description="Filter by domain"),
    db: Session = Depends(get_db)
):
    """Get query history with pagination and filtering."""

    try:
        # Build query with filters
        query = select(Query)

        # Apply filters
        if document_id:
            query = query.where(Query.document_id == document_id)
        if domain:
            query = query.where(Query.domain == domain)

        # Get total count
        count_query = select(func.count(Query.id))
        if document_id:
            count_query = count_query.where(Query.document_id == document_id)
        if domain:
            count_query = count_query.where(Query.domain == domain)

        total_count_result = await db.execute(count_query)
        total_count = total_count_result.scalar()

        # Apply pagination
        offset = (page - 1) * page_size
        query = query.order_by(desc(Query.created_at)).offset(
            offset).limit(page_size)

        queries_result = await db.execute(query)
        queries = queries_result.scalars().all()

        # Format response
        query_list = []
        for q in queries:
            query_list.append({
                'id': q.id,
                'query_text': q.query_text,
                'domain': q.domain,
                'document_id': q.document_id,
                'confidence_score': q.confidence_score,
                'processing_time_ms': q.processing_time_ms,
                'created_at': q.created_at,
                'response_summary': q.response.get('answer', '')[:200] if q.response else ''
            })

        return {
            'queries': query_list,
            'total_count': total_count,
            'page': page,
            'page_size': page_size
        }

    except Exception as e:
        logger.error("Failed to get query history", error=str(e))
        raise HTTPException(
            status_code=500, detail="Failed to retrieve query history")


@router.get("/queries/{query_id}")
async def get_query_details(query_id: int, db: Session = Depends(get_db)):
    """Get detailed information about a specific query."""

    try:
        query_result = await db.execute(
            select(Query).where(Query.id == query_id)
        )
        query = query_result.scalar_one_or_none()

        if not query:
            raise HTTPException(status_code=404, detail="Query not found")

        return {
            'id': query.id,
            'query_text': query.query_text,
            'query_type': query.query_type,
            'domain': query.domain,
            'document_id': query.document_id,
            'response': query.response,
            'confidence_score': query.confidence_score,
            'processing_time_ms': query.processing_time_ms,
            'retrieved_chunks': query.retrieved_chunks,
            'llm_reasoning': query.llm_reasoning,
            'created_at': query.created_at
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get query details",
                     query_id=query_id, error=str(e))
        raise HTTPException(
            status_code=500, detail="Failed to retrieve query details")


@router.post("/query/sample")
async def process_sample_query():
    """Process a sample query for demonstration purposes."""

    sample_queries = [
        {
            "query": "Does this policy cover knee surgery, and what are the conditions?",
            "domain": "insurance",
            "description": "Sample insurance coverage query"
        },
        {
            "query": "What are the termination clauses in this contract?",
            "domain": "legal",
            "description": "Sample legal contract query"
        },
        {
            "query": "What is the vacation policy for new employees?",
            "domain": "hr",
            "description": "Sample HR policy query"
        },
        {
            "query": "What are the audit requirements for this process?",
            "domain": "compliance",
            "description": "Sample compliance query"
        }
    ]

    return {
        "message": "Sample queries for testing the system",
        "sample_queries": sample_queries,
        "usage": "Use POST /api/v1/query with one of these sample queries to test the system"
    }


@router.get("/domains")
async def get_supported_domains():
    """Get list of supported domains and their descriptions."""

    domains = {
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
        },
        "hr": {
            "name": "Human Resources",
            "description": "HR policies, employee benefits, and workplace procedures",
            "sample_queries": [
                "What is the remote work policy?",
                "How many vacation days do employees get?",
                "What is the performance review process?"
            ]
        },
        "compliance": {
            "name": "Compliance",
            "description": "Regulatory requirements, audit procedures, and standards",
            "sample_queries": [
                "What are the data retention requirements?",
                "How often should audits be conducted?",
                "What documentation is required for compliance?"
            ]
        },
        "general": {
            "name": "General",
            "description": "General document queries without domain-specific optimization",
            "sample_queries": [
                "What is the main topic of this document?",
                "Summarize the key points",
                "Find information about specific terms"
            ]
        }
    }

    return {
        "supported_domains": domains,
        "default_domain": "general",
        "auto_detection": "The system can automatically detect the domain based on query content"
    }
