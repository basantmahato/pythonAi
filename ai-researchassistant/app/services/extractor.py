import hashlib
import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from app.models.schemas import (
    MemoryCategory,
    MemoryCreate,
    VerificationStatus,
    PrivacyLevel,
    SourceType,
)
from app.services.llm_provider import get_llm_provider

logger = logging.getLogger(__name__)

EXTRACTION_SYSTEM_PROMPT = """
You are a precise personal knowledge extraction and classification engine.
Your task is to analyze user-provided text, documents, or conversation notes, and extract individual atomic units of personal memory.

Every memory unit MUST belong to one of these 7 categories:
1. IDENTITY: Core personal facts (name, background, education, location, core values).
2. SEMANTIC_KNOWLEDGE: Concepts, domain insights, technical knowledge learned or referenced.
3. EPISODIC: Specific past events, key decisions, meetings, breakthroughs, or challenges.
4. PROCEDURAL: How the user works, preferences in code architecture, communication habits.
5. GOAL_CAREER: Desired achievements, career targets, learning objectives, milestones.
6. PROJECT: Software systems, apps, repositories the user builds or contributes to.
7. PREFERENCE: Subjective likes, dislikes, favorite tools, reading styles.

RULES:
- Split complex paragraphs into atomic, independent memory statements.
- Assign verification_status:
  - "USER_STATED" if directly stated by the user.
  - "AI_INFERRED" if it is a deduction or pattern not explicitly confirmed.
- Assign confidence_score between 0.50 and 1.0 (capped at 0.85 for AI_INFERRED).
- Extract temporal context (e.g. valid_from year/date, is_current bool).
- Output must strictly match this JSON schema:
{
  "memories": [
    {
      "category": "IDENTITY | SEMANTIC_KNOWLEDGE | EPISODIC | PROCEDURAL | GOAL_CAREER | PROJECT | PREFERENCE",
      "content": "Clear, standalone statement of the memory",
      "summary": "Brief 5-10 word title or summary",
      "verification_status": "USER_STATED | AI_INFERRED",
      "confidence_score": 0.95,
      "privacy_level": "PUBLIC | INTERNAL | CONFIDENTIAL",
      "is_current": true,
      "tags": ["keyword1", "keyword2"],
      "structured_payload": {"key": "value"}
    }
  ]
}
"""


class MemoryExtractor:
    def __init__(self):
        self.llm = get_llm_provider()

    @staticmethod
    def compute_hash(text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    def chunk_text(self, text: str, max_chars: int = 2000, overlap: int = 200) -> List[str]:
        """Split large text into overlapping chunks along paragraph boundaries."""
        paragraphs = text.split("\n\n")
        chunks = []
        current_chunk = []
        current_len = 0

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            if current_len + len(para) > max_chars and current_chunk:
                chunks.append("\n\n".join(current_chunk))
                # retain last paragraph for overlap if within reasonable length
                current_chunk = [para]
                current_len = len(para)
            else:
                current_chunk.append(para)
                current_len += len(para)

        if current_chunk:
            chunks.append("\n\n".join(current_chunk))

        return chunks if chunks else [text]

    def extract_memories(
        self,
        raw_text: str,
        source_id: Optional[UUID] = None,
        default_status: VerificationStatus = VerificationStatus.USER_STATED
    ) -> List[MemoryCreate]:
        """Extract atomic memories from input text."""
        chunks = self.chunk_text(raw_text)
        extracted_memories: List[MemoryCreate] = []

        for chunk in chunks:
            try:
                data = self.llm.generate_json(
                    system_prompt=EXTRACTION_SYSTEM_PROMPT,
                    user_prompt=f"Text to extract memories from:\n\n{chunk}"
                )

                raw_list = data.get("memories", [])
                for item in raw_list:
                    # Validate Category
                    try:
                        cat = MemoryCategory(item.get("category", "SEMANTIC_KNOWLEDGE"))
                    except ValueError:
                        cat = MemoryCategory.SEMANTIC_KNOWLEDGE

                    # Validate Status
                    status_str = item.get("verification_status", default_status.value)
                    try:
                        status = VerificationStatus(status_str)
                    except ValueError:
                        status = default_status

                    # Enforce rule: inferences capped
                    confidence = float(item.get("confidence_score", 0.90))
                    if status == VerificationStatus.AI_INFERRED and confidence > 0.85:
                        confidence = 0.85

                    mem = MemoryCreate(
                        source_id=source_id,
                        category=cat,
                        content=item.get("content", "").strip(),
                        summary=item.get("summary"),
                        verification_status=status,
                        confidence_score=confidence,
                        privacy_level=PrivacyLevel(item.get("privacy_level", "INTERNAL")),
                        is_current=item.get("is_current", True),
                        structured_payload=item.get("structured_payload", {}),
                        tags=item.get("tags", [])
                    )

                    if mem.content:
                        extracted_memories.append(mem)

            except Exception as e:
                logger.warning(f"LLM extraction failed on chunk: {e}. Falling back to raw chunk representation.")
                # Fallback: store chunk directly as semantic knowledge
                fallback_mem = MemoryCreate(
                    source_id=source_id,
                    category=MemoryCategory.SEMANTIC_KNOWLEDGE,
                    content=chunk.strip(),
                    summary=chunk.strip()[:60] + "...",
                    verification_status=default_status,
                    confidence_score=0.90,
                    privacy_level=PrivacyLevel.INTERNAL,
                    is_current=True,
                    tags=["raw_chunk"]
                )
                extracted_memories.append(fallback_mem)

        return extracted_memories


memory_extractor = MemoryExtractor()
