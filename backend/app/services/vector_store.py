"""Vector database service for storing and retrieving document embeddings."""

import asyncio
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import structlog

try:
    from pinecone import Pinecone, ServerlessSpec
    PINECONE_AVAILABLE = True
except ImportError:
    PINECONE_AVAILABLE = False
    Pinecone = None
    ServerlessSpec = None

import openai
from openai import OpenAI
import faiss

from app.config import settings

logger = structlog.get_logger()


class VectorStore:
    """Service for managing vector embeddings and similarity search."""

    def __init__(self):
        self.embeddings_enabled = settings.enable_embeddings

        if self.embeddings_enabled:
            self.openai_client = OpenAI(
                api_key=settings.openai_api_key,
                base_url=settings.openai_base_url
            )
            # Use a model available on OpenRouter for embeddings
            self.embedding_model = "openai/text-embedding-ada-002"  # OpenRouter format
            self.embedding_dimension = 1536

            # Initialize Pinecone (if available)
            if PINECONE_AVAILABLE:
                self._init_pinecone()
            else:
                logger.warning("Pinecone not available, using FAISS only")
                self._init_faiss()

            # Initialize FAISS as backup/local option
            self.faiss_index = None
            self.faiss_metadata = {}
        else:
            logger.info(
                "Embeddings disabled - vector search functionality will be limited")
            self.openai_client = None
            self.embedding_model = None
            self.embedding_dimension = None
            self.faiss_index = None
            self.faiss_metadata = {}

    def _init_pinecone(self):
        """Initialize Pinecone vector database."""
        if not PINECONE_AVAILABLE:
            logger.warning("Pinecone not available, skipping initialization")
            return

        try:
            # Initialize Pinecone client
            pc = Pinecone(api_key=settings.pinecone_api_key)

            # Create index if it doesn't exist
            existing_indexes = pc.list_indexes().names()
            if settings.pinecone_index_name not in existing_indexes:
                pc.create_index(
                    name=settings.pinecone_index_name,
                    dimension=self.embedding_dimension,
                    metric="cosine",
                    spec=ServerlessSpec(
                        cloud="aws",
                        region="us-east-1"
                    )
                )
                logger.info("Created Pinecone index",
                            index_name=settings.pinecone_index_name)

            self.pinecone_index = pc.Index(settings.pinecone_index_name)
            logger.info("Pinecone initialized successfully")

        except Exception as e:
            logger.error("Failed to initialize Pinecone", error=str(e))
            # Fall back to FAISS
            self._init_faiss()

    def _init_faiss(self):
        """Initialize FAISS index as fallback."""
        try:
            # Inner product for cosine similarity
            self.faiss_index = faiss.IndexFlatIP(self.embedding_dimension)
            logger.info("FAISS index initialized as fallback")
        except Exception as e:
            logger.error("Failed to initialize FAISS", error=str(e))
            raise

    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text using OpenAI."""
        if not self.embeddings_enabled:
            logger.warning(
                "Embeddings are disabled - returning empty embedding")
            return []

        try:
            response = self.openai_client.embeddings.create(
                model=self.embedding_model,
                input=text.replace("\n", " ")
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error("Failed to generate embedding", error=str(e))
            raise

    async def store_chunks(self, document_id: int, chunks: List[Dict[str, Any]]) -> List[str]:
        """Store document chunks in vector database."""
        if not self.embeddings_enabled:
            logger.info("Embeddings disabled - skipping vector storage for document",
                        document_id=document_id, chunk_count=len(chunks))
            # Return placeholder vector IDs
            return [f"doc_{document_id}_chunk_{chunk['chunk_index']}" for chunk in chunks]

        vector_ids = []

        try:
            for chunk in chunks:
                # Generate embedding
                embedding = await self.generate_embedding(chunk['content'])

                # Create unique vector ID
                vector_id = f"doc_{document_id}_chunk_{chunk['chunk_index']}"

                # Prepare metadata
                metadata = {
                    'document_id': document_id,
                    'chunk_index': chunk['chunk_index'],
                    # Truncate for metadata storage
                    'content': chunk['content'][:1000],
                    'start_char': chunk['start_char'],
                    'end_char': chunk['end_char']
                }

                # Store in Pinecone if available
                if hasattr(self, 'pinecone_index'):
                    self.pinecone_index.upsert(
                        vectors=[(vector_id, embedding, metadata)]
                    )
                else:
                    # Store in FAISS
                    self.faiss_index.add(
                        np.array([embedding], dtype=np.float32))
                    self.faiss_metadata[len(self.faiss_metadata)] = {
                        'vector_id': vector_id,
                        **metadata
                    }

                vector_ids.append(vector_id)
                logger.debug("Stored chunk embedding", vector_id=vector_id)

            logger.info("Stored document chunks",
                        document_id=document_id, chunk_count=len(chunks))
            return vector_ids

        except Exception as e:
            logger.error("Failed to store chunks",
                         document_id=document_id, error=str(e))
            raise

    async def similarity_search(self, query: str, top_k: int = 10, filter_metadata: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """Perform similarity search for query."""
        if not self.embeddings_enabled:
            logger.warning(
                "Embeddings disabled - returning empty search results")
            return []

        try:
            # Generate query embedding
            query_embedding = await self.generate_embedding(query)

            results = []

            if hasattr(self, 'pinecone_index'):
                # Search in Pinecone
                search_results = self.pinecone_index.query(
                    vector=query_embedding,
                    top_k=top_k,
                    include_metadata=True,
                    filter=filter_metadata
                )

                for match in search_results.matches:
                    results.append({
                        'vector_id': match.id,
                        'score': float(match.score),
                        'metadata': match.metadata
                    })

            else:
                # Search in FAISS
                query_vector = np.array([query_embedding], dtype=np.float32)
                scores, indices = self.faiss_index.search(query_vector, top_k)

                for i, (score, idx) in enumerate(zip(scores[0], indices[0])):
                    if idx in self.faiss_metadata:
                        metadata = self.faiss_metadata[idx]
                        results.append({
                            'vector_id': metadata['vector_id'],
                            'score': float(score),
                            'metadata': metadata
                        })

            # Filter by similarity threshold
            results = [r for r in results if r['score']
                       >= settings.similarity_threshold]

            logger.info("Similarity search completed", query_length=len(
                query), results_count=len(results))
            return results

        except Exception as e:
            logger.error("Similarity search failed", error=str(e))
            raise

    async def delete_document_vectors(self, document_id: int):
        """Delete all vectors for a document."""
        try:
            if hasattr(self, 'pinecone_index'):
                # Delete from Pinecone using filter
                self.pinecone_index.delete(filter={'document_id': document_id})
            else:
                # For FAISS, we'd need to rebuild the index (simplified approach)
                # In production, consider using a more sophisticated approach
                keys_to_remove = [k for k, v in self.faiss_metadata.items()
                                  if v.get('document_id') == document_id]
                for key in keys_to_remove:
                    del self.faiss_metadata[key]

            logger.info("Deleted document vectors", document_id=document_id)

        except Exception as e:
            logger.error("Failed to delete document vectors",
                         document_id=document_id, error=str(e))
            raise
