"""Semantic search engine for intelligent document retrieval."""

import re
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import structlog

from app.services.vector_store import VectorStore
from app.config import settings
from app.models.document import DocumentChunk, Document
from app.core.database import AsyncSessionLocal
from sqlalchemy import select, func, or_, and_

logger = structlog.get_logger()


class SemanticSearchEngine:
    """Core semantic search functionality for document retrieval."""

    def __init__(self):
        self.vector_store = VectorStore()
        self.query_processors = {
            'insurance': self._process_insurance_query,
            'legal': self._process_legal_query,
            'hr': self._process_hr_query,
            'compliance': self._process_compliance_query,
            'general': self._process_general_query
        }

    async def search(self, query: str, domain: Optional[str] = None,
                     document_id: Optional[int] = None, top_k: int = 10) -> Dict[str, Any]:
        """Perform semantic search with domain-specific processing."""
        start_time = datetime.now()

        try:
            # Preprocess query
            processed_query = await self._preprocess_query(query, domain)

            # Build search filters
            filters = {}
            if document_id:
                filters['document_id'] = document_id

            # Perform hybrid search (vector + text-based)
            search_results = []

            if settings.enable_embeddings:
                try:
                    # Try vector similarity search first
                    vector_results = await self.vector_store.similarity_search(
                        processed_query['enhanced_query'],
                        top_k=top_k,
                        filter_metadata=filters
                    )
                    search_results.extend(vector_results)
                    logger.info("Vector search completed",
                                results_count=len(vector_results))
                except Exception as e:
                    logger.warning(
                        "Vector search failed, falling back to text search", error=str(e))

            # If vector search didn't return enough results or failed, supplement with text search
            if len(search_results) < top_k:
                remaining_results = top_k - len(search_results)
                text_results = await self._text_based_search(
                    processed_query['enhanced_query'],
                    top_k=remaining_results,
                    document_id=document_id,
                    domain=domain
                )

                # Avoid duplicates by checking existing result IDs
                existing_ids = {result.get('id', '')
                                for result in search_results}
                for result in text_results:
                    if result.get('id', '') not in existing_ids:
                        search_results.append(result)
                        if len(search_results) >= top_k:
                            break

                logger.info("Text search completed",
                            text_results_count=len(text_results),
                            total_results=len(search_results))

            # Post-process results based on domain
            if domain and domain in self.query_processors:
                search_results = await self.query_processors[domain](
                    query, search_results, processed_query
                )

            # Calculate processing time
            processing_time = (
                datetime.now() - start_time).total_seconds() * 1000

            # Prepare response
            response = {
                'query': query,
                'processed_query': processed_query,
                'results': search_results,
                'total_results': len(search_results),
                'processing_time_ms': int(processing_time),
                'domain': domain or 'general'
            }

            logger.info("Search completed",
                        query_length=len(query),
                        results_count=len(search_results),
                        processing_time_ms=int(processing_time))

            return response

        except Exception as e:
            logger.error("Search failed", query=query, error=str(e))
            raise

    async def _preprocess_query(self, query: str, domain: Optional[str] = None) -> Dict[str, Any]:
        """Preprocess query to enhance search effectiveness."""

        # Extract key entities and concepts
        entities = self._extract_entities(query)

        # Expand query with domain-specific terms
        expanded_terms = self._expand_domain_terms(query, domain)

        # Create enhanced query
        enhanced_query = query
        if expanded_terms:
            enhanced_query += " " + " ".join(expanded_terms)

        return {
            'original_query': query,
            'enhanced_query': enhanced_query,
            'entities': entities,
            'expanded_terms': expanded_terms,
            'domain': domain
        }

    def _extract_entities(self, query: str) -> Dict[str, List[str]]:
        """Extract entities from query using pattern matching."""
        entities = {
            'medical_procedures': [],
            'body_parts': [],
            'legal_terms': [],
            'financial_terms': [],
            'time_periods': []
        }

        # Medical procedures and body parts
        medical_patterns = [
            r'\b(surgery|operation|procedure|treatment|therapy)\b',
            r'\b(knee|hip|shoulder|back|spine|heart|brain)\b'
        ]

        # Legal terms
        legal_patterns = [
            r'\b(contract|agreement|clause|liability|coverage|policy)\b',
            r'\b(terms|conditions|exclusions|limitations)\b'
        ]

        # Financial terms
        financial_patterns = [
            r'\b(premium|deductible|copay|coinsurance|benefit|claim)\b',
            r'\$[\d,]+|\b\d+\s*dollars?\b'
        ]

        # Time periods
        time_patterns = [
            r'\b(annual|monthly|quarterly|daily)\b',
            r'\b\d+\s*(year|month|day|week)s?\b'
        ]

        query_lower = query.lower()

        for pattern in medical_patterns:
            entities['medical_procedures'].extend(
                re.findall(pattern, query_lower))

        for pattern in legal_patterns:
            entities['legal_terms'].extend(re.findall(pattern, query_lower))

        for pattern in financial_patterns:
            entities['financial_terms'].extend(
                re.findall(pattern, query_lower))

        for pattern in time_patterns:
            entities['time_periods'].extend(re.findall(pattern, query_lower))

        return entities

    def _expand_domain_terms(self, query: str, domain: Optional[str] = None) -> List[str]:
        """Expand query with domain-specific synonyms and related terms."""
        expanded_terms = []
        query_lower = query.lower()

        if domain == 'insurance':
            insurance_expansions = {
                'surgery': ['surgical procedure', 'operation', 'medical procedure'],
                'coverage': ['benefits', 'protection', 'insurance'],
                'policy': ['plan', 'contract', 'agreement'],
                'claim': ['reimbursement', 'payment', 'settlement']
            }

            for term, expansions in insurance_expansions.items():
                if term in query_lower:
                    expanded_terms.extend(expansions)

        elif domain == 'legal':
            legal_expansions = {
                'contract': ['agreement', 'document', 'terms'],
                'clause': ['provision', 'section', 'paragraph'],
                'liability': ['responsibility', 'obligation', 'duty']
            }

            for term, expansions in legal_expansions.items():
                if term in query_lower:
                    expanded_terms.extend(expansions)

        return list(set(expanded_terms))  # Remove duplicates

    async def _process_insurance_query(self, query: str, results: List[Dict],
                                       processed_query: Dict) -> List[Dict]:
        """Process insurance-specific queries."""
        # Boost results that contain insurance-specific terms
        insurance_boost_terms = ['coverage', 'policy',
                                 'premium', 'deductible', 'claim', 'benefit']

        for result in results:
            content = result['metadata'].get('content', '').lower()
            boost_score = sum(
                1 for term in insurance_boost_terms if term in content)
            result['domain_score'] = boost_score
            result['adjusted_score'] = result['score'] + (boost_score * 0.1)

        # Sort by adjusted score
        results.sort(key=lambda x: x['adjusted_score'], reverse=True)
        return results

    async def _process_legal_query(self, query: str, results: List[Dict],
                                   processed_query: Dict) -> List[Dict]:
        """Process legal-specific queries."""
        legal_boost_terms = ['contract', 'agreement',
                             'clause', 'terms', 'conditions', 'liability']

        for result in results:
            content = result['metadata'].get('content', '').lower()
            boost_score = sum(
                1 for term in legal_boost_terms if term in content)
            result['domain_score'] = boost_score
            result['adjusted_score'] = result['score'] + (boost_score * 0.1)

        results.sort(key=lambda x: x['adjusted_score'], reverse=True)
        return results

    async def _process_hr_query(self, query: str, results: List[Dict],
                                processed_query: Dict) -> List[Dict]:
        """Process HR-specific queries."""
        hr_boost_terms = ['employee', 'employment',
                          'benefits', 'payroll', 'personnel', 'workplace']

        for result in results:
            content = result['metadata'].get('content', '').lower()
            boost_score = sum(1 for term in hr_boost_terms if term in content)
            result['domain_score'] = boost_score
            result['adjusted_score'] = result['score'] + (boost_score * 0.1)

        results.sort(key=lambda x: x['adjusted_score'], reverse=True)
        return results

    async def _process_compliance_query(self, query: str, results: List[Dict],
                                        processed_query: Dict) -> List[Dict]:
        """Process compliance-specific queries."""
        compliance_boost_terms = [
            'regulation', 'compliance', 'audit', 'standards', 'requirements', 'policy']

        for result in results:
            content = result['metadata'].get('content', '').lower()
            boost_score = sum(
                1 for term in compliance_boost_terms if term in content)
            result['domain_score'] = boost_score
            result['adjusted_score'] = result['score'] + (boost_score * 0.1)

        results.sort(key=lambda x: x['adjusted_score'], reverse=True)
        return results

    async def _text_based_search(self, query: str, top_k: int = 10,
                                 document_id: Optional[int] = None,
                                 domain: Optional[str] = None) -> List[Dict[str, Any]]:
        """Perform text-based search through document chunks when embeddings are disabled."""

        async with AsyncSessionLocal() as db:
            try:
                # Prepare search terms
                search_terms = query.lower().split()
                search_terms = [term.strip('.,!?;:"()[]{}')
                                for term in search_terms if len(term) > 2]

                # Build base query
                base_query = select(DocumentChunk, Document).join(
                    Document, DocumentChunk.document_id == Document.id
                ).where(Document.processing_status == 'completed')

                # Apply document filter if specified
                if document_id:
                    base_query = base_query.where(Document.id == document_id)

                # Apply domain filter if specified
                if domain:
                    base_query = base_query.where(Document.domain == domain)

                # Create text search conditions
                search_conditions = []
                for term in search_terms:
                    search_conditions.append(
                        func.lower(DocumentChunk.content).contains(term)
                    )

                # Combine search conditions with OR
                if search_conditions:
                    base_query = base_query.where(or_(*search_conditions))

                # Execute query
                # Get more for scoring
                result = await db.execute(base_query.limit(top_k * 2))
                chunks_and_docs = result.all()

                # Score and rank results
                scored_results = []
                for chunk, document in chunks_and_docs:
                    score = self._calculate_text_score(
                        chunk.content.lower(), search_terms, query.lower())

                    if score > 0:  # Only include results with some relevance
                        scored_results.append({
                            'id': f"chunk_{chunk.id}",
                            'score': score,
                            'metadata': {
                                'document_id': document.id,
                                'document_title': document.title or document.filename,
                                'content': chunk.content,
                                'chunk_index': chunk.chunk_index,
                                'start_char': chunk.start_char,
                                'end_char': chunk.end_char,
                                'domain': document.domain
                            }
                        })

                # Sort by score and return top results
                scored_results.sort(key=lambda x: x['score'], reverse=True)
                return scored_results[:top_k]

            except Exception as e:
                logger.error("Text-based search failed", error=str(e))
                return []

    def _calculate_text_score(self, content: str, search_terms: List[str], original_query: str) -> float:
        """Calculate relevance score for text-based search."""
        score = 0.0

        # Exact phrase match (highest score)
        if original_query in content:
            score += 10.0

        # Individual term matches
        for term in search_terms:
            term_count = content.count(term)
            if term_count > 0:
                # Base score for term presence
                score += 2.0
                # Bonus for multiple occurrences
                score += min(term_count - 1, 3) * 0.5

        # Bonus for multiple terms appearing close together
        if len(search_terms) > 1:
            for i, term1 in enumerate(search_terms):
                for term2 in search_terms[i+1:]:
                    # Find positions of both terms
                    pos1 = content.find(term1)
                    pos2 = content.find(term2)
                    if pos1 != -1 and pos2 != -1:
                        distance = abs(pos1 - pos2)
                        if distance < 100:  # Terms within 100 characters
                            score += 1.0

        # Normalize by content length (prefer shorter, more focused chunks)
        if len(content) > 0:
            score = score * (1000 / (len(content) + 1000))

        return score

    async def _process_general_query(self, query: str, results: List[Dict],
                                     processed_query: Dict) -> List[Dict]:
        """Process general queries without domain-specific boosting."""
        for result in results:
            result['domain_score'] = 0
            result['adjusted_score'] = result['score']

        return results
