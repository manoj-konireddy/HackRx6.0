"""LLM integration and decision engine for contextual understanding and reasoning."""

import json
import re
from typing import List, Dict, Any, Optional
from datetime import datetime
import structlog
import requests

from openai import OpenAI
from app.config import settings

logger = structlog.get_logger()


class LLMEngine:
    """Service for LLM-powered contextual understanding and decision making."""

    def __init__(self):
        self.client = OpenAI(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url
        )
        self.model = settings.openai_model

        # Domain-specific system prompts
        self.system_prompts = {
            'insurance': self._get_insurance_system_prompt(),
            'legal': self._get_legal_system_prompt(),
            'hr': self._get_hr_system_prompt(),
            'compliance': self._get_compliance_system_prompt(),
            'general': self._get_general_system_prompt()
        }

    async def process_query(self, query: str, search_results: List[Dict[str, Any]],
                            domain: str = 'general') -> Dict[str, Any]:
        """Process query with contextual understanding and generate response."""

        try:
            # Prepare context from search results
            context = self._prepare_context(search_results)

            # Check if we have relevant document content
            has_document_context = len(search_results) > 0 and any(
                result.get('metadata', {}).get('content', '').strip()
                for result in search_results
            )

            # If no relevant documents found, try web search
            web_context = ""
            if not has_document_context:
                logger.info(
                    "No relevant documents found, attempting web search", query=query)
                web_context = await self._web_search(query)

            # Get domain-specific system prompt
            system_prompt = self.system_prompts.get(
                domain, self.system_prompts['general'])

            # Create user prompt
            user_prompt = self._create_user_prompt(
                query, context, domain, web_context, has_document_context)

            # Generate response using GPT-4
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,
                max_tokens=2000
            )

            # Parse structured response
            llm_response = response.choices[0].message.content
            parsed_response = self._parse_llm_response(llm_response)

            # Calculate confidence score
            confidence_score = self._calculate_confidence(
                parsed_response, search_results)

            return {
                'answer': parsed_response.get('answer', ''),
                'reasoning': parsed_response.get('reasoning', ''),
                'confidence_score': confidence_score,
                'supporting_evidence': parsed_response.get('evidence', []),
                'limitations': parsed_response.get('limitations', []),
                'follow_up_questions': parsed_response.get('follow_up', []),
                'domain': domain,
                'llm_model': self.model
            }

        except Exception as e:
            logger.error("LLM processing failed", query=query, error=str(e))
            raise

    def _prepare_context(self, search_results: List[Dict[str, Any]]) -> str:
        """Prepare context from search results for LLM processing."""
        context_parts = []

        for i, result in enumerate(search_results[:5]):  # Use top 5 results
            metadata = result.get('metadata', {})
            content = metadata.get('content', '')
            score = result.get('score', 0)

            context_parts.append(f"""
Document Chunk {i+1} (Relevance Score: {score:.3f}):
{content}
---
""")

        return "\n".join(context_parts)

    def _create_user_prompt(self, query: str, context: str, domain: str,
                            web_context: str = "", has_document_context: bool = True) -> str:
        """Create user prompt with query and context."""

        if has_document_context:
            return f"""
Query: {query}

Context from relevant documents:
{context}

Please analyze the query in the context of the provided documents and provide a structured response following the format specified in the system prompt.
"""
        elif web_context:
            return f"""
Query: {query}

No relevant information was found in the uploaded documents for this query.

Web search results:
{web_context}

Since no relevant documents were found, I've searched online for information. Please provide a response based on the web search results, but clearly indicate that this information comes from online sources, not from the uploaded documents.
"""
        else:
            return f"""
Query: {query}

No relevant information was found in the uploaded documents for this query, and web search was not available.

Please provide a response indicating that the information is not available in the uploaded documents and suggest that the user might need to upload relevant documents or search online.
"""

    def _parse_llm_response(self, response: str) -> Dict[str, Any]:
        """Parse structured LLM response."""
        try:
            # Try to parse as JSON first
            if response.strip().startswith('{'):
                return json.loads(response)

            # Fallback to text parsing
            parsed = {
                'answer': '',
                'reasoning': '',
                'evidence': [],
                'limitations': [],
                'follow_up': []
            }

            # Simple text parsing logic
            lines = response.split('\n')
            current_section = None

            for line in lines:
                line = line.strip()
                if line.lower().startswith('answer:'):
                    current_section = 'answer'
                    parsed['answer'] = line[7:].strip()
                elif line.lower().startswith('reasoning:'):
                    current_section = 'reasoning'
                    parsed['reasoning'] = line[10:].strip()
                elif current_section and line:
                    parsed[current_section] += ' ' + line

            return parsed

        except Exception as e:
            logger.error("Failed to parse LLM response", error=str(e))
            return {
                'answer': response,
                'reasoning': 'Unable to parse structured response',
                'evidence': [],
                'limitations': ['Response parsing failed'],
                'follow_up': []
            }

    def _calculate_confidence(self, parsed_response: Dict[str, Any],
                              search_results: List[Dict[str, Any]]) -> float:
        """Calculate confidence score based on response and search results."""

        # Base confidence from search result scores
        if search_results:
            avg_search_score = sum(r.get('score', 0)
                                   for r in search_results) / len(search_results)
        else:
            avg_search_score = 0.0

        # Adjust based on response characteristics
        answer_length = len(parsed_response.get('answer', ''))
        reasoning_length = len(parsed_response.get('reasoning', ''))

        # Confidence factors
        search_factor = min(avg_search_score, 1.0)
        content_factor = min((answer_length + reasoning_length) / 500, 1.0)
        evidence_factor = min(
            len(parsed_response.get('evidence', [])) / 3, 1.0)

        # Weighted confidence score
        confidence = (search_factor * 0.4 + content_factor *
                      0.3 + evidence_factor * 0.3)

        return round(confidence, 3)

    def _get_insurance_system_prompt(self) -> str:
        """Get system prompt for insurance domain."""
        return """You are an expert insurance policy analyst. Your task is to analyze insurance-related queries and provide accurate, helpful responses based on the provided document context.

When responding to queries about insurance policies, coverage, claims, or benefits:

1. Provide clear, direct answers about coverage, exclusions, and conditions
2. Explain the reasoning behind your conclusions
3. Cite specific policy sections or clauses when available
4. Highlight any limitations or conditions that apply
5. Suggest follow-up questions if the query needs clarification

Response format (JSON):
{
  "answer": "Direct answer to the query",
  "reasoning": "Detailed explanation of how you arrived at this conclusion",
  "evidence": ["List of specific document excerpts that support your answer"],
  "limitations": ["Any limitations, exclusions, or conditions that apply"],
  "follow_up": ["Suggested follow-up questions for clarification"]
}

Be precise about coverage details and always mention if additional information is needed for a complete assessment."""

    def _get_legal_system_prompt(self) -> str:
        """Get system prompt for legal domain."""
        return """You are an expert legal document analyst. Your task is to analyze legal queries and provide accurate responses based on the provided document context.

When responding to queries about contracts, agreements, legal clauses, or obligations:

1. Provide clear interpretations of legal language and terms
2. Explain the legal implications and requirements
3. Reference specific clauses, sections, or provisions
4. Highlight any ambiguities or areas requiring legal counsel
5. Suggest areas where professional legal advice may be needed

Response format (JSON):
{
  "answer": "Clear interpretation of the legal question",
  "reasoning": "Legal analysis and interpretation methodology",
  "evidence": ["Specific contract clauses or legal provisions cited"],
  "limitations": ["Legal disclaimers and areas requiring professional counsel"],
  "follow_up": ["Questions to clarify legal requirements or implications"]
}

Always include appropriate legal disclaimers and recommend consulting with qualified legal counsel for important decisions."""

    def _get_hr_system_prompt(self) -> str:
        """Get system prompt for HR domain."""
        return """You are an expert HR policy analyst. Your task is to analyze HR-related queries and provide accurate responses based on the provided document context.

When responding to queries about employment policies, benefits, procedures, or workplace regulations:

1. Provide clear guidance on HR policies and procedures
2. Explain employee rights, benefits, and obligations
3. Reference specific policy sections or employee handbook provisions
4. Highlight compliance requirements and best practices
5. Suggest appropriate next steps or escalation procedures

Response format (JSON):
{
  "answer": "Clear guidance on the HR matter",
  "reasoning": "Analysis of relevant policies and procedures",
  "evidence": ["Specific policy sections or handbook references"],
  "limitations": ["Areas requiring manager approval or HR consultation"],
  "follow_up": ["Next steps or additional information needed"]
}

Ensure responses comply with employment law and organizational policies."""

    def _get_compliance_system_prompt(self) -> str:
        """Get system prompt for compliance domain."""
        return """You are an expert compliance analyst. Your task is to analyze compliance-related queries and provide accurate responses based on the provided document context.

When responding to queries about regulations, standards, audit requirements, or compliance procedures:

1. Provide clear guidance on regulatory requirements
2. Explain compliance obligations and procedures
3. Reference specific regulations, standards, or policy sections
4. Highlight risk areas and mitigation strategies
5. Suggest compliance monitoring and reporting requirements

Response format (JSON):
{
  "answer": "Clear compliance guidance",
  "reasoning": "Analysis of regulatory requirements and standards",
  "evidence": ["Specific regulatory citations or policy references"],
  "limitations": ["Areas requiring legal or compliance officer review"],
  "follow_up": ["Additional compliance considerations or requirements"]
}

Always emphasize the importance of staying current with regulatory changes and consulting compliance officers for complex matters."""

    def _get_general_system_prompt(self) -> str:
        """Get system prompt for general domain."""
        return """You are an expert document analyst. Your task is to analyze queries and provide accurate, helpful responses based on the provided document context.

When responding to document-related queries:

1. Provide clear, direct answers based on the available information
2. Explain your reasoning and methodology
3. Cite specific document sections that support your conclusions
4. Acknowledge limitations in the available information
5. Suggest areas where additional information might be helpful

Response format (JSON):
{
  "answer": "Direct answer based on available information",
  "reasoning": "Explanation of analysis methodology and conclusions",
  "evidence": ["Specific document excerpts supporting the answer"],
  "limitations": ["Information gaps or areas of uncertainty"],
  "follow_up": ["Suggested questions for additional clarity"]
}

Be thorough in your analysis while acknowledging the boundaries of the available information."""

    async def _web_search(self, query: str) -> str:
        """Perform web search when no relevant documents are found."""
        try:
            # Simple web search using DuckDuckGo (no API key required)
            search_url = "https://api.duckduckgo.com/"
            params = {
                'q': query,
                'format': 'json',
                'no_html': '1',
                'skip_disambig': '1'
            }

            response = requests.get(search_url, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()

                # Extract relevant information
                results = []

                # Add abstract if available
                if data.get('Abstract'):
                    results.append(f"Summary: {data['Abstract']}")

                # Add related topics
                if data.get('RelatedTopics'):
                    for topic in data['RelatedTopics'][:3]:  # Limit to 3 topics
                        if isinstance(topic, dict) and topic.get('Text'):
                            results.append(f"Related: {topic['Text']}")

                # Add answer if available
                if data.get('Answer'):
                    results.append(f"Direct Answer: {data['Answer']}")

                if results:
                    return "\n\n".join(results)
                else:
                    return "Web search completed but no specific information was found."

            else:
                logger.warning("Web search failed",
                               status_code=response.status_code)
                return "Web search was attempted but encountered an error."

        except requests.exceptions.Timeout:
            logger.warning("Web search timed out")
            return "Web search timed out. Please try again later."
        except Exception as e:
            logger.error("Web search failed", error=str(e))
            return "Web search encountered an error and could not be completed."
