"""Pydantic schemas for API request/response models."""

from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class DocumentUploadResponse(BaseModel):
    """Response model for document upload."""
    document_id: int
    filename: str
    file_type: str
    file_size: int
    processing_status: str
    domain: Optional[str] = None
    message: str


class QueryRequest(BaseModel):
    """Request model for query processing."""
    query: str = Field(..., min_length=1, max_length=1000, description="The query text")
    document_id: Optional[int] = Field(None, description="Specific document ID to search within")
    domain: Optional[str] = Field(None, description="Domain hint (insurance, legal, hr, compliance)")
    max_results: Optional[int] = Field(10, ge=1, le=50, description="Maximum number of results")


class SearchResult(BaseModel):
    """Model for individual search result."""
    vector_id: str
    score: float
    adjusted_score: Optional[float] = None
    content: str
    document_id: int
    chunk_index: int
    metadata: Dict[str, Any] = {}


class QueryResponse(BaseModel):
    """Response model for query processing."""
    query: str
    domain: str
    answer: str
    reasoning: str
    confidence_score: float
    supporting_evidence: List[str]
    limitations: List[str]
    follow_up_questions: List[str]
    search_results: List[SearchResult]
    total_processing_time_ms: int
    metadata: Dict[str, Any]


class DocumentListResponse(BaseModel):
    """Response model for document listing."""
    documents: List[Dict[str, Any]]
    total_count: int
    page: int
    page_size: int


class DocumentDetailResponse(BaseModel):
    """Response model for document details."""
    id: int
    filename: str
    original_filename: str
    file_type: str
    file_size: int
    domain: Optional[str]
    processing_status: str
    created_at: datetime
    processed_at: Optional[datetime]
    chunk_count: int
    metadata: Dict[str, Any] = {}


class ErrorResponse(BaseModel):
    """Standard error response model."""
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None
    request_id: Optional[str] = None
