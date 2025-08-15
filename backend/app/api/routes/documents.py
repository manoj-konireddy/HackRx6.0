"""Document management endpoints."""

import os
import shutil
from typing import List, Optional
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, select, func
from sqlalchemy.exc import IntegrityError
from datetime import datetime
import structlog

from app.core.database import get_db
from app.models.document import Document, DocumentChunk
from app.services.document_processor import DocumentProcessor
from app.services.vector_store import VectorStore
from app.api.schemas import DocumentUploadResponse, DocumentListResponse, DocumentDetailResponse
from app.config import settings

logger = structlog.get_logger()
router = APIRouter()

# Initialize services
document_processor = DocumentProcessor()
vector_store = VectorStore()

# Create upload directory
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


@router.post("/documents/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    domain: Optional[str] = Query(None, description="Document domain hint"),
    db: Session = Depends(get_db)
):
    """Upload and process a document."""

    try:
        # Validate file type
        allowed_types = ['pdf', 'docx', 'doc', 'eml']
        file_extension = file.filename.split('.')[-1].lower()

        if file_extension not in allowed_types:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type. Allowed types: {', '.join(allowed_types)}"
            )

        # Validate file size
        file_size = 0
        content = await file.read()
        file_size = len(content)

        if file_size > settings.max_file_size_mb * 1024 * 1024:
            raise HTTPException(
                status_code=400,
                detail=f"File size exceeds maximum limit of {settings.max_file_size_mb}MB"
            )

        # Save file temporarily
        temp_file_path = UPLOAD_DIR / f"temp_{file.filename}"
        with open(temp_file_path, "wb") as buffer:
            buffer.write(content)

        try:
            # Process document
            processed_data = await document_processor.process_document(
                str(temp_file_path), file_extension
            )

            # Check if document with same hash already exists
            existing_document = await db.execute(
                select(Document).where(Document.file_hash ==
                                       processed_data['file_hash'])
            )
            existing_doc = existing_document.scalar_one_or_none()

            if existing_doc:
                logger.info("Document with same hash already exists",
                            existing_document_id=existing_doc.id,
                            filename=file.filename,
                            existing_filename=existing_doc.filename)

                return DocumentUploadResponse(
                    document_id=existing_doc.id,
                    filename=existing_doc.filename,
                    file_type=existing_doc.file_type,
                    file_size=existing_doc.file_size,
                    processing_status=existing_doc.processing_status,
                    domain=existing_doc.domain,
                    message="Document already exists with the same content"
                )

            # Create document record
            document = Document(
                filename=file.filename,
                original_filename=file.filename,
                file_type=file_extension,
                file_size=file_size,
                file_hash=processed_data['file_hash'],
                title=processed_data['metadata'].get('title', ''),
                author=processed_data['metadata'].get('author', ''),
                subject=processed_data['metadata'].get('subject', ''),
                domain=domain or processed_data['domain'],
                processing_status='processing'
            )

            db.add(document)
            try:
                await db.commit()
                await db.refresh(document)
            except IntegrityError as e:
                # Handle unique constraint violation as fallback
                await db.rollback()
                if "file_hash" in str(e) and "unique" in str(e).lower():
                    # Find the existing document with the same hash
                    existing_result = await db.execute(
                        select(Document).where(Document.file_hash ==
                                               processed_data['file_hash'])
                    )
                    existing_doc = existing_result.scalar_one_or_none()

                    if existing_doc:
                        logger.info("Duplicate document detected via constraint violation",
                                    existing_document_id=existing_doc.id,
                                    filename=file.filename,
                                    existing_filename=existing_doc.filename)

                        return DocumentUploadResponse(
                            document_id=existing_doc.id,
                            filename=existing_doc.filename,
                            file_type=existing_doc.file_type,
                            file_size=existing_doc.file_size,
                            processing_status=existing_doc.processing_status,
                            domain=existing_doc.domain,
                            message="Document already exists with the same content"
                        )

                # Re-raise if it's not a file_hash constraint violation
                raise

            # Store chunks in database and vector store
            chunk_records = []
            for chunk_data in processed_data['chunks']:
                chunk = DocumentChunk(
                    document_id=document.id,
                    content=chunk_data['content'],
                    chunk_index=chunk_data['chunk_index'],
                    start_char=chunk_data['start_char'],
                    end_char=chunk_data['end_char'],
                    embedding_model=vector_store.embedding_model
                )
                chunk_records.append(chunk)
                db.add(chunk)

            await db.commit()

            # Store in vector database
            vector_ids = await vector_store.store_chunks(document.id, processed_data['chunks'])

            # Update chunk records with vector IDs
            for chunk, vector_id in zip(chunk_records, vector_ids):
                chunk.vector_id = vector_id

            # Update document status
            document.processing_status = 'completed'
            document.processed_at = datetime.utcnow()
            await db.commit()

            logger.info("Document processed successfully",
                        document_id=document.id,
                        filename=file.filename,
                        chunks=len(processed_data['chunks']))

            return DocumentUploadResponse(
                document_id=document.id,
                filename=file.filename,
                file_type=file_extension,
                file_size=file_size,
                processing_status='completed',
                domain=document.domain,
                message="Document uploaded and processed successfully"
            )

        except Exception as e:
            # Rollback the transaction
            await db.rollback()

            # Update document status to failed if document was created
            try:
                if 'document' in locals() and document.id:
                    document.processing_status = 'failed'
                    document.error_message = str(e)
                    await db.commit()
            except Exception as commit_error:
                logger.error("Failed to update document status",
                             error=str(commit_error))
                await db.rollback()

            logger.error("Document processing failed",
                         filename=file.filename,
                         error=str(e))
            raise HTTPException(
                status_code=500, detail=f"Document processing failed: {str(e)}")

        finally:
            # Clean up temporary file
            if temp_file_path.exists():
                temp_file_path.unlink()

    except HTTPException:
        raise
    except Exception as e:
        # Ensure session is rolled back on any unexpected error
        try:
            await db.rollback()
        except Exception:
            pass

        logger.error("Document upload failed",
                     filename=file.filename, error=str(e))
        raise HTTPException(status_code=500, detail="Document upload failed")


@router.get("/documents", response_model=DocumentListResponse)
async def list_documents(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    domain: Optional[str] = Query(None, description="Filter by domain"),
    status: Optional[str] = Query(
        None, description="Filter by processing status"),
    db: Session = Depends(get_db)
):
    """List documents with pagination and filtering."""

    try:
        # Build query with filters
        query = select(Document)

        if domain:
            query = query.where(Document.domain == domain)
        if status:
            query = query.where(Document.processing_status == status)

        # Get total count
        count_query = select(func.count(Document.id))
        if domain:
            count_query = count_query.where(Document.domain == domain)
        if status:
            count_query = count_query.where(
                Document.processing_status == status)

        total_count_result = await db.execute(count_query)
        total_count = total_count_result.scalar()

        # Apply pagination and ordering
        offset = (page - 1) * page_size
        query = query.order_by(desc(Document.created_at)
                               ).offset(offset).limit(page_size)

        documents_result = await db.execute(query)
        documents = documents_result.scalars().all()

        # Format response
        document_list = []
        for doc in documents:
            # Get chunk count for each document
            chunk_count_query = select(func.count(DocumentChunk.id)).where(
                DocumentChunk.document_id == doc.id
            )
            chunk_count_result = await db.execute(chunk_count_query)
            chunk_count = chunk_count_result.scalar()
            document_list.append({
                'id': doc.id,
                'filename': doc.filename,
                'file_type': doc.file_type,
                'file_size': doc.file_size,
                'domain': doc.domain,
                'processing_status': doc.processing_status,
                'created_at': doc.created_at,
                'processed_at': doc.processed_at,
                'chunk_count': chunk_count
            })

        return DocumentListResponse(
            documents=document_list,
            total_count=total_count,
            page=page,
            page_size=page_size
        )

    except Exception as e:
        logger.error("Failed to list documents", error=str(e))
        raise HTTPException(
            status_code=500, detail="Failed to retrieve documents")


@router.get("/documents/{document_id}", response_model=DocumentDetailResponse)
async def get_document(document_id: int, db: Session = Depends(get_db)):
    """Get detailed information about a specific document."""

    try:
        document_result = await db.execute(
            select(Document).where(Document.id == document_id)
        )
        document = document_result.scalar_one_or_none()

        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        # Get chunk count
        chunk_count_result = await db.execute(
            select(func.count(DocumentChunk.id)).where(
                DocumentChunk.document_id == document_id
            )
        )
        chunk_count = chunk_count_result.scalar()

        return DocumentDetailResponse(
            id=document.id,
            filename=document.filename,
            original_filename=document.original_filename,
            file_type=document.file_type,
            file_size=document.file_size,
            domain=document.domain,
            processing_status=document.processing_status,
            created_at=document.created_at,
            processed_at=document.processed_at,
            chunk_count=chunk_count,
            metadata={
                'title': document.title,
                'author': document.author,
                'subject': document.subject,
                'file_hash': document.file_hash
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get document",
                     document_id=document_id, error=str(e))
        raise HTTPException(
            status_code=500, detail="Failed to retrieve document")


@router.delete("/documents/{document_id}")
async def delete_document(document_id: int, db: Session = Depends(get_db)):
    """Delete a document and all associated data."""

    try:
        document_result = await db.execute(
            select(Document).where(Document.id == document_id)
        )
        document = document_result.scalar_one_or_none()

        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        # Delete from vector store
        await vector_store.delete_document_vectors(document_id)

        # Delete from database (cascades to chunks)
        await db.delete(document)
        await db.commit()

        logger.info("Document deleted successfully", document_id=document_id)

        return {"message": "Document deleted successfully", "document_id": document_id}

    except HTTPException:
        raise
    except Exception as e:
        # Rollback the transaction
        try:
            await db.rollback()
        except Exception:
            pass

        logger.error("Failed to delete document",
                     document_id=document_id, error=str(e))
        raise HTTPException(
            status_code=500, detail="Failed to delete document")
