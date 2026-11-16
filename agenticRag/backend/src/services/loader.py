import io
import logging
from pypdf import PdfReader

logger = logging.getLogger(__name__)

class DocumentLoader:
    @staticmethod
    def load_pdf(file_bytes: bytes, filename: str) -> str:
        """Extract text from PDF file bytes."""
        try:
            pdf_file = io.BytesIO(file_bytes)
            reader = PdfReader(pdf_file)
            text_parts = []
            for page_idx, page in enumerate(reader.pages):
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text.strip())
            return "\n\n".join(text_parts)
        except Exception as e:
            logger.error(f"Failed to parse PDF '{filename}': {e}")
            raise ValueError(f"Could not read PDF file '{filename}': {e}")

    @staticmethod
    def load_text(file_bytes: bytes, filename: str) -> str:
        """Extract text from plain text or Markdown bytes."""
        try:
            return file_bytes.decode("utf-8", errors="replace")
        except Exception as e:
            logger.error(f"Failed to decode text file '{filename}': {e}")
            raise ValueError(f"Could not read text file '{filename}': {e}")

    @classmethod
    def load_from_bytes(cls, file_bytes: bytes, filename: str) -> str:
        """Route to appropriate extractor based on file extension."""
        lower_name = filename.lower()
        if lower_name.endswith(".pdf"):
            return cls.load_pdf(file_bytes, filename)
        elif lower_name.endswith((".txt", ".md", ".markdown", ".csv", ".json")):
            return cls.load_text(file_bytes, filename)
        else:
            # Fallback to UTF-8 text decoding
            return cls.load_text(file_bytes, filename)
