"""Domain-specific query processing service."""

import re
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import structlog

from app.services.search_engine import SemanticSearchEngine
from app.services.llm_engine import LLMEngine
from app.models.document import Query
from app.core.database import AsyncSessionLocal

logger = structlog.get_logger()


class QueryProcessor:
    """Main service for processing queries with domain-specific intelligence."""

    def __init__(self):
        self.search_engine = SemanticSearchEngine()
        self.llm_engine = LLMEngine()

        # Domain-specific processors
        self.domain_processors = {
            'insurance': InsuranceQueryProcessor(),
            'legal': LegalQueryProcessor(),
            'hr': HRQueryProcessor(),
            'compliance': ComplianceQueryProcessor()
        }

    async def process_query(self, query: str, document_id: Optional[int] = None,
                            domain: Optional[str] = None) -> Dict[str, Any]:
        """Process a query with full pipeline including search and LLM analysis."""

        start_time = datetime.now()

        try:
            # Auto-detect domain if not provided
            if not domain:
                domain = self._detect_query_domain(query)

            # Perform semantic search
            search_results = await self.search_engine.search(
                query=query,
                domain=domain,
                document_id=document_id,
                top_k=10
            )

            # Apply domain-specific processing
            if domain in self.domain_processors:
                search_results = await self.domain_processors[domain].enhance_results(
                    query, search_results
                )

            # Generate LLM response
            llm_response = await self.llm_engine.process_query(
                query=query,
                search_results=search_results['results'],
                domain=domain
            )

            # Calculate total processing time
            total_time = (datetime.now() - start_time).total_seconds() * 1000

            # Prepare final response
            response = {
                'query': query,
                'domain': domain,
                'answer': llm_response['answer'],
                'reasoning': llm_response['reasoning'],
                'confidence_score': llm_response['confidence_score'],
                'supporting_evidence': llm_response['supporting_evidence'],
                'limitations': llm_response['limitations'],
                'follow_up_questions': llm_response['follow_up_questions'],
                # Top 5 for response
                'search_results': search_results['results'][:5],
                'total_processing_time_ms': int(total_time),
                'metadata': {
                    'search_time_ms': search_results['processing_time_ms'],
                    'llm_model': llm_response['llm_model'],
                    'total_chunks_found': search_results['total_results']
                }
            }

            # Store query in database
            await self._store_query(query, document_id, domain, response)

            logger.info("Query processed successfully",
                        query_length=len(query),
                        domain=domain,
                        confidence=llm_response['confidence_score'],
                        processing_time_ms=int(total_time))

            return response

        except Exception as e:
            logger.error("Query processing failed", query=query, error=str(e))
            raise

    def _detect_query_domain(self, query: str) -> str:
        """Auto-detect query domain based on keywords and patterns."""
        query_lower = query.lower()

        # Domain keyword patterns
        domain_patterns = {
            'insurance': [
                r'\b(policy|coverage|premium|claim|deductible|beneficiary)\b',
                r'\b(insurance|insured|insurer|underwriter)\b',
                r'\b(medical|health|dental|vision|disability)\b'
            ],
            'legal': [
                r'\b(contract|agreement|clause|terms|conditions)\b',
                r'\b(legal|court|lawsuit|attorney|jurisdiction)\b',
                r'\b(liability|obligation|breach|damages)\b'
            ],
            'hr': [
                r'\b(employee|employment|hr|human resources)\b',
                r'\b(payroll|benefits|personnel|workplace)\b',
                r'\b(vacation|sick leave|performance|disciplinary)\b'
            ],
            'compliance': [
                r'\b(compliance|regulation|audit|regulatory)\b',
                r'\b(standards|requirements|policy|procedure)\b',
                r'\b(sox|gdpr|hipaa|iso|certification)\b'
            ]
        }

        # Count matches for each domain
        domain_scores = {}
        for domain, patterns in domain_patterns.items():
            score = sum(len(re.findall(pattern, query_lower))
                        for pattern in patterns)
            domain_scores[domain] = score

        # Return domain with highest score, default to 'general'
        if max(domain_scores.values()) > 0:
            return max(domain_scores, key=domain_scores.get)

        return 'general'

    async def _store_query(self, query: str, document_id: Optional[int],
                           domain: str, response: Dict[str, Any]):
        """Store query and response in database."""
        try:
            async with AsyncSessionLocal() as db:
                query_record = Query(
                    document_id=document_id,
                    query_text=query,
                    query_type='semantic_search',
                    domain=domain,
                    response=response,
                    confidence_score=response['confidence_score'],
                    processing_time_ms=response['total_processing_time_ms'],
                    retrieved_chunks=[
                        {
                            'vector_id': r.get('vector_id', r.get('id', 'unknown')),
                            'score': r.get('score', 0.0)
                        } for r in response['search_results']
                    ],
                    llm_reasoning=response['reasoning']
                )

                db.add(query_record)
                await db.commit()

        except Exception as e:
            logger.error("Failed to store query", error=str(e))
            # Don't raise - this shouldn't break the main flow


class DomainQueryProcessor:
    """Base class for domain-specific query processors."""

    async def enhance_results(self, query: str, search_results: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance search results with domain-specific logic."""
        return search_results


class InsuranceQueryProcessor(DomainQueryProcessor):
    """Insurance domain query processor."""

    async def enhance_results(self, query: str, search_results: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance results for insurance queries."""

        # Identify query type
        query_type = self._identify_insurance_query_type(query)

        # Apply insurance-specific boosting
        for result in search_results['results']:
            content = result['metadata'].get('content', '').lower()

            # Boost based on query type
            if query_type == 'coverage':
                boost = self._calculate_coverage_boost(content)
            elif query_type == 'claim':
                boost = self._calculate_claim_boost(content)
            elif query_type == 'exclusion':
                boost = self._calculate_exclusion_boost(content)
            else:
                boost = 0

            result['insurance_boost'] = boost
            result['adjusted_score'] = result.get(
                'adjusted_score', result['score']) + boost

        # Re-sort by adjusted score
        search_results['results'].sort(
            key=lambda x: x['adjusted_score'], reverse=True)

        return search_results

    def _identify_insurance_query_type(self, query: str) -> str:
        """Identify the type of insurance query."""
        query_lower = query.lower()

        if any(word in query_lower for word in ['cover', 'coverage', 'covered', 'include']):
            return 'coverage'
        elif any(word in query_lower for word in ['claim', 'reimbursement', 'payment']):
            return 'claim'
        elif any(word in query_lower for word in ['exclude', 'exclusion', 'not covered']):
            return 'exclusion'
        else:
            return 'general'

    def _calculate_coverage_boost(self, content: str) -> float:
        """Calculate boost for coverage-related content."""
        coverage_terms = ['coverage', 'covered',
                          'benefits', 'eligible', 'included']
        return sum(0.05 for term in coverage_terms if term in content)

    def _calculate_claim_boost(self, content: str) -> float:
        """Calculate boost for claim-related content."""
        claim_terms = ['claim', 'reimbursement',
                       'payment', 'settlement', 'process']
        return sum(0.05 for term in claim_terms if term in content)

    def _calculate_exclusion_boost(self, content: str) -> float:
        """Calculate boost for exclusion-related content."""
        exclusion_terms = ['exclusion', 'excluded',
                           'not covered', 'limitation', 'restriction']
        return sum(0.05 for term in exclusion_terms if term in content)


class LegalQueryProcessor(DomainQueryProcessor):
    """Legal domain query processor."""

    async def enhance_results(self, query: str, search_results: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance results for legal queries."""

        # Boost results containing legal structure indicators
        for result in search_results['results']:
            content = result['metadata'].get('content', '')

            # Look for legal document structure
            legal_boost = 0
            if re.search(r'\b(section|clause|paragraph|article)\s+\d+', content.lower()):
                legal_boost += 0.1
            if re.search(r'\b(whereas|therefore|notwithstanding)\b', content.lower()):
                legal_boost += 0.05
            if re.search(r'\b(shall|must|required|prohibited)\b', content.lower()):
                legal_boost += 0.05

            result['legal_boost'] = legal_boost
            result['adjusted_score'] = result.get(
                'adjusted_score', result['score']) + legal_boost

        search_results['results'].sort(
            key=lambda x: x['adjusted_score'], reverse=True)
        return search_results


class HRQueryProcessor(DomainQueryProcessor):
    """HR domain query processor."""

    async def enhance_results(self, query: str, search_results: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance results for HR queries."""

        # Boost HR policy and procedure content
        for result in search_results['results']:
            content = result['metadata'].get('content', '').lower()

            hr_boost = 0
            hr_terms = ['policy', 'procedure',
                        'employee', 'manager', 'supervisor', 'hr']
            hr_boost += sum(0.03 for term in hr_terms if term in content)

            result['hr_boost'] = hr_boost
            result['adjusted_score'] = result.get(
                'adjusted_score', result['score']) + hr_boost

        search_results['results'].sort(
            key=lambda x: x['adjusted_score'], reverse=True)
        return search_results


class ComplianceQueryProcessor(DomainQueryProcessor):
    """Compliance domain query processor."""

    async def enhance_results(self, query: str, search_results: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance results for compliance queries."""

        # Boost compliance and regulatory content
        for result in search_results['results']:
            content = result['metadata'].get('content', '').lower()

            compliance_boost = 0
            compliance_terms = ['regulation', 'compliance',
                                'audit', 'standard', 'requirement']
            compliance_boost += sum(
                0.04 for term in compliance_terms if term in content)

            result['compliance_boost'] = compliance_boost
            result['adjusted_score'] = result.get(
                'adjusted_score', result['score']) + compliance_boost

        search_results['results'].sort(
            key=lambda x: x['adjusted_score'], reverse=True)
        return search_results
