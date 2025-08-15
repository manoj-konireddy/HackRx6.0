"""Document-related database models."""

from sqlalchemy import Column, Integer, String, Text, DateTime, Float, JSON, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Document(Base):
    """Document metadata model."""

    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=False)  # pdf, docx, email
    file_size = Column(Integer, nullable=False)
    file_hash = Column(String(64), unique=True, index=True)

    # Document metadata
    title = Column(String(500))
    author = Column(String(255))
    subject = Column(String(500))
    domain = Column(String(50))  # insurance, legal, hr, compliance

    # Processing status
    # pending, processing, completed, failed
    processing_status = Column(String(50), default="pending")
    error_message = Column(Text)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    processed_at = Column(DateTime(timezone=True))

    # Relationships
    chunks = relationship(
        "DocumentChunk", back_populates="document", cascade="all, delete-orphan")
    queries = relationship("Query", back_populates="document")


class DocumentChunk(Base):
    """Document chunk model for storing processed text segments."""

    __tablename__ = "document_chunks"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)

    # Chunk content
    content = Column(Text, nullable=False)
    chunk_index = Column(Integer, nullable=False)
    start_char = Column(Integer)
    end_char = Column(Integer)

    # Vector embedding metadata
    vector_id = Column(String(255))  # ID in vector database
    embedding_model = Column(String(100))

    # Chunk metadata
    page_number = Column(Integer)
    section_title = Column(String(500))
    chunk_metadata = Column(JSON)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    document = relationship("Document", back_populates="chunks")


class Query(Base):
    """Query history and results model."""

    __tablename__ = "queries"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=True)

    # Query details
    query_text = Column(Text, nullable=False)
    # semantic_search, clause_retrieval, decision_making
    query_type = Column(String(50))
    domain = Column(String(50))  # insurance, legal, hr, compliance

    # Results
    response = Column(JSON)
    confidence_score = Column(Float)
    processing_time_ms = Column(Integer)

    # Context
    retrieved_chunks = Column(JSON)  # List of chunk IDs and scores
    llm_reasoning = Column(Text)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    document = relationship("Document", back_populates="queries")
