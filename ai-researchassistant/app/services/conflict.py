import logging
from typing import Optional, Tuple
from uuid import UUID

from app.config import settings
from app.models.schemas import (
    ConflictDetectionResult,
    MemoryCreate,
    VerificationStatus,
)
from app.storage.vector_store import vector_store
from app.services.embedding import embedding_service
from app.services.llm_provider import get_llm_provider

logger = logging.getLogger(__name__)

CONFLICT_EVALUATION_PROMPT = """
You are an epistemic consistency evaluator.
Compare the following NEW memory statement with an EXISTING stored memory statement in the user's knowledge base.

Determine their relationship:
1. "DUPLICATE": Expresses essentially the same fact or meaning.
2. "SUPERSEDES": Updates or replaces older information with newer information (e.g., changed address, new job title, completed goal).
3. "CONTRADICTS": Directly conflicts with no clear chronological succession.
4. "COMPATIBLE": Coexists naturally as distinct aspects.

Output JSON only:
{
  "relationship": "DUPLICATE | SUPERSEDES | CONTRADICTS | COMPATIBLE",
  "explanation": "Brief explanation",
  "recommended_action": "IGNORE | SUPERSEDE | FLAG_FOR_REVIEW | PROCEED"
}
"""


class ConflictDetector:
    def __init__(self):
        self.threshold = settings.CONFLICT_SIMILARITY_THRESHOLD
        self.llm = get_llm_provider()

    def check_conflict(
        self,
        new_memory: MemoryCreate,
        vector: Optional[list[float]] = None
    ) -> ConflictDetectionResult:
        """Evaluate whether a new memory duplicates, updates, or contradicts existing memories."""
        if vector is None:
            vector = embedding_service.embed_text(new_memory.content)

        # Search for closely related memories in the same category
        candidates = vector_store.search_memories(
            query_vector=vector,
            limit=3,
            categories=[new_memory.category.value],
            is_current_only=True,
            score_threshold=self.threshold
        )

        if not candidates:
            return ConflictDetectionResult(has_conflict=False, action_suggested="PROCEED")

        top_match = candidates[0]
        similarity = top_match["score"]
        existing_id = UUID(top_match["memory_id"])
        existing_text = top_match["payload"].get("content_preview", "")

        # Ask LLM to evaluate the nature of the match
        try:
            user_prompt = (
                f"Existing Memory ({existing_id}):\n\"{existing_text}\"\n\n"
                f"New Candidate Memory:\n\"{new_memory.content}\""
            )
            eval_result = self.llm.generate_json(
                system_prompt=CONFLICT_EVALUATION_PROMPT,
                user_prompt=user_prompt
            )

            rel = eval_result.get("relationship", "COMPATIBLE").upper()
            action = eval_result.get("recommended_action", "PROCEED").upper()

            if rel == "DUPLICATE":
                return ConflictDetectionResult(
                    has_conflict=True,
                    existing_memory_id=existing_id,
                    conflicting_statement=existing_text,
                    similarity_score=similarity,
                    action_suggested="IGNORE"
                )
            elif rel == "SUPERSEDES":
                return ConflictDetectionResult(
                    has_conflict=True,
                    existing_memory_id=existing_id,
                    conflicting_statement=existing_text,
                    similarity_score=similarity,
                    action_suggested="SUPERSEDE"
                )
            elif rel == "CONTRADICTS":
                return ConflictDetectionResult(
                    has_conflict=True,
                    existing_memory_id=existing_id,
                    conflicting_statement=existing_text,
                    similarity_score=similarity,
                    action_suggested="FLAG_FOR_REVIEW"
                )

        except Exception as e:
            logger.warning(f"Error during LLM conflict evaluation: {e}")

        return ConflictDetectionResult(
            has_conflict=False,
            similarity_score=similarity,
            action_suggested="PROCEED"
        )


conflict_detector = ConflictDetector()
