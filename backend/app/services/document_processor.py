"""Document processing service for extracting text and metadata from various file formats."""

import hashlib
import re
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import structlog

import PyPDF2
from docx import Document as DocxDocument
import email
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.config import settings

logger = structlog.get_logger()


class DocumentProcessor:
    """Service for processing documents and extracting text content."""

    def __init__(self):
        self.chunk_size = settings.chunk_size
        self.chunk_overlap = settings.chunk_overlap

    async def process_document(self, file_path: str, file_type: str) -> Dict[str, Any]:
        """Process a document and extract text, metadata, and chunks."""
        try:
            # Extract text and metadata based on file type
            if file_type.lower() == 'pdf':
                text, metadata = await self._process_pdf(file_path)
            elif file_type.lower() in ['docx', 'doc']:
                text, metadata = await self._process_docx(file_path)
            elif file_type.lower() in ['eml', 'email']:
                text, metadata = await self._process_email(file_path)
            else:
                raise ValueError(f"Unsupported file type: {file_type}")

            # Generate file hash
            file_hash = self._generate_file_hash(file_path)

            # Create text chunks
            chunks = self._create_chunks(text)

            # Detect domain
            domain = self._detect_domain(text, metadata)

            return {
                'text': text,
                'metadata': metadata,
                'chunks': chunks,
                'file_hash': file_hash,
                'domain': domain
            }

        except Exception as e:
            logger.error("Error processing document",
                         file_path=file_path, error=str(e))
            raise

    async def _process_pdf(self, file_path: str) -> Tuple[str, Dict[str, Any]]:
        """Extract text and metadata from PDF file."""
        text = ""
        metadata = {}

        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)

                # Extract metadata
                if pdf_reader.metadata:
                    metadata = {
                        'title': pdf_reader.metadata.get('/Title', ''),
                        'author': pdf_reader.metadata.get('/Author', ''),
                        'subject': pdf_reader.metadata.get('/Subject', ''),
                        'creator': pdf_reader.metadata.get('/Creator', ''),
                        'producer': pdf_reader.metadata.get('/Producer', ''),
                        'creation_date': str(pdf_reader.metadata.get('/CreationDate', '')),
                        'modification_date': str(pdf_reader.metadata.get('/ModDate', ''))
                    }

                # Extract text from all pages
                for page_num, page in enumerate(pdf_reader.pages):
                    page_text = page.extract_text()
                    if page_text:
                        text += f"\n--- Page {page_num + 1} ---\n{page_text}\n"

                metadata['total_pages'] = len(pdf_reader.pages)

        except Exception as e:
            logger.error("Error processing PDF",
                         file_path=file_path, error=str(e))
            raise

        return text.strip(), metadata

    async def _process_docx(self, file_path: str) -> Tuple[str, Dict[str, Any]]:
        """Extract text and metadata from DOCX file."""
        text = ""
        metadata = {}

        try:
            doc = DocxDocument(file_path)

            # Extract metadata
            core_props = doc.core_properties
            metadata = {
                'title': core_props.title or '',
                'author': core_props.author or '',
                'subject': core_props.subject or '',
                'keywords': core_props.keywords or '',
                'category': core_props.category or '',
                'comments': core_props.comments or '',
                'created': str(core_props.created) if core_props.created else '',
                'modified': str(core_props.modified) if core_props.modified else '',
                'last_modified_by': core_props.last_modified_by or ''
            }

            # Extract text from paragraphs
            paragraphs = []
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    paragraphs.append(paragraph.text.strip())

            text = '\n\n'.join(paragraphs)
            metadata['total_paragraphs'] = len(paragraphs)

        except Exception as e:
            logger.error("Error processing DOCX",
                         file_path=file_path, error=str(e))
            raise

        return text, metadata

    async def _process_email(self, file_path: str) -> Tuple[str, Dict[str, Any]]:
        """Extract text and metadata from email file."""
        text = ""
        metadata = {}

        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                email_content = file.read()

            # Parse email
            msg = email.message_from_string(email_content)

            # Extract metadata
            metadata = {
                'subject': msg.get('Subject', ''),
                'from': msg.get('From', ''),
                'to': msg.get('To', ''),
                'date': msg.get('Date', ''),
                'message_id': msg.get('Message-ID', ''),
                'content_type': msg.get_content_type()
            }

            # Extract text content
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        text += part.get_payload(decode=True).decode(
                            'utf-8', errors='ignore')
            else:
                text = msg.get_payload(decode=True).decode(
                    'utf-8', errors='ignore')

        except Exception as e:
            logger.error("Error processing email",
                         file_path=file_path, error=str(e))
            raise

        return text, metadata

    def _create_chunks(self, text: str) -> List[Dict[str, Any]]:
        """Create overlapping text chunks from document text."""
        chunks = []

        # Clean and normalize text
        text = re.sub(r'\s+', ' ', text).strip()

        if len(text) <= self.chunk_size:
            chunks.append({
                'content': text,
                'chunk_index': 0,
                'start_char': 0,
                'end_char': len(text)
            })
            return chunks

        # Create overlapping chunks
        start = 0
        chunk_index = 0

        while start < len(text):
            end = min(start + self.chunk_size, len(text))

            # Try to break at sentence boundaries
            if end < len(text):
                # Look for sentence endings within the overlap region
                sentence_end = text.rfind('.', start, end)
                if sentence_end > start + self.chunk_size // 2:
                    end = sentence_end + 1

            chunk_content = text[start:end].strip()
            if chunk_content:
                chunks.append({
                    'content': chunk_content,
                    'chunk_index': chunk_index,
                    'start_char': start,
                    'end_char': end
                })
                chunk_index += 1

            # Move start position with overlap
            start = max(start + self.chunk_size - self.chunk_overlap, end)

        return chunks

    def _generate_file_hash(self, file_path: str) -> str:
        """Generate SHA-256 hash of file content."""
        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()

    def _detect_domain(self, text: str, metadata: Dict[str, Any]) -> str:
        """Detect document domain based on content and metadata."""
        text_lower = text.lower()
        title_lower = metadata.get('title', '').lower()
        subject_lower = metadata.get('subject', '').lower()

        # Domain keywords
        insurance_keywords = ['policy', 'coverage', 'premium',
                              'claim', 'deductible', 'beneficiary', 'insurance']
        legal_keywords = ['contract', 'agreement', 'clause',
                          'legal', 'court', 'lawsuit', 'attorney', 'jurisdiction']
        hr_keywords = ['employee', 'employment', 'hr',
                       'human resources', 'payroll', 'benefits', 'personnel']
        compliance_keywords = ['compliance', 'regulation',
                               'audit', 'regulatory', 'standards', 'requirements']

        # Count keyword matches
        domains = {
            'insurance': sum(1 for keyword in insurance_keywords if keyword in text_lower or keyword in title_lower),
            'legal': sum(1 for keyword in legal_keywords if keyword in text_lower or keyword in title_lower),
            'hr': sum(1 for keyword in hr_keywords if keyword in text_lower or keyword in title_lower),
            'compliance': sum(1 for keyword in compliance_keywords if keyword in text_lower or keyword in title_lower)
        }

        # Return domain with highest score, default to 'general'
        if max(domains.values()) > 0:
            return max(domains, key=domains.get)
        return 'general'
