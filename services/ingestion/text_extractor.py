"""
Text Extraction Processor

Extracts text content from various document formats (PDF, HTML, XML) using
multiple libraries for robust processing.
"""

import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
import tempfile
import os
import subprocess
from abc import ABC, abstractmethod

# For PDF processing
try:
    import pypdf2
    PYPDF_AVAILABLE = True
except ImportError:
    PYPDF_AVAILABLE = False

try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False

# For HTML/XML processing
try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False

# For spaCy layout if available
try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False

logger = logging.getLogger(__name__)


class BaseTextExtractor(ABC):
    """Base class for text extractors."""

    @abstractmethod
    def extract_text(self, file_path: str) -> str:
        """Extract text from file."""


class PDFPlumberExtractor(BaseTextExtractor):
    """PDF text extraction using pdfplumber."""

    def extract_text(self, file_path: str) -> str:
        """Extract text from PDF using pdfplumber."""
        if not PDFPLUMBER_AVAILABLE:
            raise RuntimeError("pdfplumber not available")

        with pdfplumber.open(file_path) as pdf:
            pages = []
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    pages.append(text)

        return '\n\n'.join(pages)


class PyPDF2Extractor(BaseTextExtractor):
    """PDF text extraction using PyPDF2."""

    def extract_text(self, file_path: str) -> str:
        """Extract text from PDF using PyPDF2."""
        if not PYPDF_AVAILABLE:
            raise RuntimeError("PyPDF2 not available")

        with open(file_path, 'rb') as file:
            reader = pypdf2.PdfReader(file)
            pages = []
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    pages.append(text)

        return '\n\n'.join(pages)


class HTMLExtractor(BaseTextExtractor):
    """HTML/XML text extraction."""

    def extract_text(self, file_path: str) -> str:
        """Extract text from HTML/XML files."""
        if not BS4_AVAILABLE:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()

        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            soup = BeautifulSoup(f.read(), 'html.parser')

        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.extract()

        # Get text
        text = soup.get_text()

        # Clean up whitespace
        lines = (line.strip() for line in text.splitlines())
        return '\n'.join(line for line in lines if line)


class PlainTextExtractor(BaseTextExtractor):
    """Plain text file extraction."""

    def extract_text(self, file_path: str) -> str:
        """Extract text from plain text files."""
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()


class OCRExtractor(BaseTextExtractor):
    """OCR text extraction using Tesseract."""

    def extract_text(self, file_path: str) -> str:
        """Extract text using OCR (useful for scanned PDFs)."""
        try:
            import pytesseract
            from PIL import Image

            # Convert PDF to images first if needed
            if file_path.lower().endswith('.pdf'):
                import fitz  # PyMuPDF
                doc = fitz.open(file_path)
                text_parts = []

                for page_num in range(min(10, len(doc))):  # Limit to first 10 pages
                    page = doc.load_page(page_num)
                    pix = page.get_pixmap()
                    img_data = pix.tobytes()
                    img = Image.open(io.BytesIO(img_data))

                    text = pytesseract.image_to_string(img)
                    text_parts.append(text)

                return '\n\n'.join(text_parts)
            else:
                # For image files
                img = Image.open(file_path)
                return pytesseract.image_to_string(img)

        except ImportError:
            logger.warning("Tesseract/OCR not available")
            return ""


class TextExtractor:
    """Main text extraction orchestrator."""

    def __init__(self):
        """Initialize text extractor with available methods."""
        self.extractors = {
            '.pdf': [PDFPlumberExtractor(), PyPDF2Extractor(), OCRExtractor()],
            '.html': [HTMLExtractor()],
            '.htm': [HTMLExtractor()],
            '.xml': [HTMLExtractor()],  # Treat XML as HTML-like
            '.txt': [PlainTextExtractor()],
            '.md': [PlainTextExtractor()],
        }

        # Default extractor for unrecognized extensions
        self.default_extractor = PlainTextExtractor()

        # SpaCy layout processor for PDFs if available
        self.layout_extractor = None
        if SPACY_AVAILABLE:
            try:
                import spacy_layout
                # Load spaCy model with layout
                # self.nlp = spacy.load("en_core_web_md")  # Example
                # self.layout_extractor = spacy_layout.LayoutParser(self.nlp)
                pass
            except ImportError:
                pass

    def extract_text(self, file_path: str) -> str:
        """
        Extract text from document.

        Args:
            file_path: Path to the document file

        Returns:
            Extracted text content
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        file_ext = Path(file_path).suffix.lower()

        # Get appropriate extractors
        extractors = self.extractors.get(file_ext, [self.default_extractor])

        last_error = None
        text_results = []

        # Try each extractor
        for extractor in extractors:
            try:
                extracted_text = extractor.extract_text(file_path)

                if extracted_text and len(extracted_text.strip()) > 10:  # Minimum content
                    text_results.append((extracted_text, len(extracted_text)))

            except Exception as e:
                logger.warning(f"Extractor {extractor.__class__.__name__} failed: {e}")
                last_error = e
                continue

        if text_results:
            # Return the longest extracted text (usually most complete)
            text_results.sort(key=lambda x: x[1], reverse=True)
            return text_results[0][0]

        # If no extractor worked, raise the last error
        if last_error:
            raise last_error

        return ""

    def extract_text_with_metadata(self, file_path: str) -> Dict[str, Any]:
        """
        Extract text with metadata.

        Args:
            file_path: Path to the document file

        Returns:
            Dict with text, word_count, char_count, etc.
        """
        text = self.extract_text(file_path)

        # Calculate basic metadata
        words = text.split()
        word_count = len(words)
        char_count = len(text)
        line_count = text.count('\n') + 1

        # Estimate reading time (words per minute)
        reading_time_min = word_count / 200  # Assuming 200 words per minute

        return {
            'text': text,
            'word_count': word_count,
            'char_count': char_count,
            'line_count': line_count,
            'reading_time_minutes': round(reading_time_min, 1),
            'file_path': file_path,
            'file_size': os.path.getsize(file_path) if os.path.exists(file_path) else 0
        }

    def extract_sections(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Extract document sections with headings.

        Args:
            file_path: Path to the document file

        Returns:
            List of section dictionaries with title and content
        """
        text = self.extract_text(file_path)

        # Simple section detection based on line patterns
        lines = text.split('\n')
        sections = []
        current_section = None

        for i, line in enumerate(lines):
            line = line.strip()

            # Detect potential section headers (all caps, numbered, etc.)
            if (line and (line.isupper() or
                         (len(line) < 100 and
                          any(char.isdigit() for char in line[:10])) or
                         line.startswith(('Chapter', 'Section', 'Article')))):

                # Save previous section
                if current_section:
                    sections.append(current_section)

                # Start new section
                current_section = {
                    'title': line,
                    'content': '',
                    'start_line': i,
                    'file_path': file_path
                }
            elif current_section:
                current_section['content'] += line + '\n'

        # Add final section
        if current_section:
            sections.append(current_section)

        # If no sections found, create one section with entire text
        if not sections:
            sections = [{
                'title': 'Document Content',
                'content': text,
                'start_line': 0,
                'file_path': file_path
            }]

        return sections


# Utility functions
def clean_text(text: str) -> str:
    """
    Clean and normalize extracted text.

    Args:
        text: Raw extracted text

    Returns:
        Cleaned text
    """
    import re

    # Remove excessive whitespace
    text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)

    # Remove trailing/leading whitespace per line
    lines = [line.strip() for line in text.split('\n')]
    text = '\n'.join(lines)

    # Remove excessive spaces
    text = re.sub(r' +', ' ', text)

    return text.strip()


def estimate_quality(text: str) -> float:
    """
    Estimate text extraction quality (0-1 scale).

    Args:
        text: Extracted text

    Returns:
        Quality score
    """
    if not text:
        return 0.0

    words = text.split()
    avg_word_length = sum(len(word) for word in words) / len(words) if words else 0

    # Factors: length, word length, punctuation balance
    length_score = min(len(text) / 10000, 1.0)  # Favor longer texts
    word_score = min(avg_word_length / 8, 1.0)  # Favor reasonable word lengths
    uppercase_ratio = sum(1 for c in text if c.isupper()) / len(text) if text else 0
    punctuation_score = 1.0 if 0.01 < text.count('.') / len(text) < 0.1 else 0.5

    # Penalize all-caps or unusual patterns
    pattern_penalty = 1.0 if uppercase_ratio < 0.8 else 0.5

    return (length_score + word_score + punctuation_score + pattern_penalty) / 4.0


# Test function
def main():
    """Test text extraction."""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python text_extractor.py <file_path>")
        return

    file_path = sys.argv[1]
    extractor = TextExtractor()

    try:
        result = extractor.extract_text_with_metadata(file_path)
        print("Extraction successful:")
        print(f"File: {result['file_path']}")
        print(f"Words: {result['word_count']}")
        print(f"Reading time: {result['reading_time_minutes']} minutes")
        print(f"Quality: {estimate_quality(result['text']):.2f}")
        print("\nFirst 500 characters:")
        print(result['text'][:500])

    except Exception as e:
        print(f"Extraction failed: {e}")


if __name__ == "__main__":
    main()
