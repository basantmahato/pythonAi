import uuid
import logging
from typing import List, Optional
from src.models.schemas import DocumentChunk
from src.config.settings import settings

logger = logging.getLogger(__name__)

class RecursiveChunker:
    def __init__(
        self,
        chunk_size: int = settings.CHUNK_SIZE,
        chunk_overlap: int = settings.CHUNK_OVERLAP,
        separators: Optional[List[str]] = None
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = separators or ["\n\n", "\n", ". ", " ", ""]

    def _split_text(self, text: str, separators: List[str]) -> List[str]:
        """Recursively split text by separators until pieces fit within chunk_size."""
        final_chunks: List[str] = []
        if not separators:
            return [text]

        separator = separators[-1]
        for s in separators:
            if s == "" or s in text:
                separator = s
                break

        splits = text.split(separator) if separator else list(text)

        merged_chunk = ""
        for piece in splits:
            if not piece:
                continue

            candidate = f"{merged_chunk}{separator}{piece}" if merged_chunk else piece
            if len(candidate) <= self.chunk_size:
                merged_chunk = candidate
            else:
                if merged_chunk:
                    final_chunks.append(merged_chunk.strip())

                # If single piece exceeds chunk size and we have finer separators, split recursively
                if len(piece) > self.chunk_size and len(separators) > 1:
                    sub_chunks = self._split_text(piece, separators[1:])
                    final_chunks.extend(sub_chunks)
                    merged_chunk = ""
                else:
                    merged_chunk = piece

        if merged_chunk.strip():
            final_chunks.append(merged_chunk.strip())

        return [c for c in final_chunks if c]

    def chunk_document(
        self,
        text: str,
        source_name: str,
        base_metadata: Optional[dict] = None
    ) -> List[DocumentChunk]:
        """Split text and wrap into DocumentChunk objects with deterministic IDs."""
        raw_chunks = self._split_text(text, self.separators)
        chunks: List[DocumentChunk] = []
        base_meta = base_metadata or {}

        for idx, chunk_text in enumerate(raw_chunks):
            # Deterministic UUID prevents duplicate entries if same document is re-ingested
            chunk_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{source_name}_{idx}"))
            metadata = {
                **base_meta,
                "source": source_name,
                "chunk_index": idx,
                "total_chunks": len(raw_chunks),
                "char_count": len(chunk_text)
            }
            chunks.append(
                DocumentChunk(
                    chunk_id=chunk_id,
                    content=chunk_text,
                    metadata=metadata
                )
            )

        logger.info(f"Generated {len(chunks)} chunks for '{source_name}'.")
        return chunks
