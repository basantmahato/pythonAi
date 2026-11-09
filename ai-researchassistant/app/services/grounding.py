import logging
import re
from typing import List, Tuple
from uuid import UUID

from app.models.schemas import (
    GroundedQueryResponse,
    MemoryCitation,
    VerificationStatus,
)
from app.services.llm_provider import get_llm_provider

logger = logging.getLogger(__name__)

GROUNDING_SYSTEM_PROMPT = """
You are the Personal Intelligence System and external cognitive memory for Basant.
Your role is to act as an accurate, personal learning and career intelligence assistant.

CORE RULES FOR GROUNDED RESPONSES:
1. STRICT ADHERENCE: You may ONLY state personal facts, goals, experiences, and preferences that are directly supported by the retrieved memories provided in the <personal_memories> block.
2. NO INVENTED FACTS: If the requested personal detail is not present in the memories, you MUST state clearly:
   "I do not have verified personal information regarding [topic]."
   NEVER guess, assume, or invent personal biographical, educational, or project details.
3. CITATION SYNTAX: Every time you state a fact derived from a memory, append the exact memory reference in this format: [Memory: <memory_id>].
4. INFERENCES: If offering advice, next steps, or career recommendations based on goals, you MUST explicitly prefix the statement with:
   "[Inference / Recommendation]: ..."
5. TONE: Concise, structured, evidence-grounded, and objective.
"""


class GroundingService:
    def __init__(self):
        self.llm = get_llm_provider()

    def build_memory_context(self, citations: List[MemoryCitation]) -> str:
        """Format retrieved memories into a structured context block with metadata."""
        if not citations:
            return "No relevant personal memories found."

        context_lines = ["<personal_memories>"]
        for c in citations:
            line = (
                f"- [Memory: {c.memory_id}] [CATEGORY: {c.category.value}] "
                f"[STATUS: {c.verification_status.value}] (Score: {c.relevance_score})\n"
                f"  {c.content_snippet}"
            )
            context_lines.append(line)
        context_lines.append("</personal_memories>")
        return "\n".join(context_lines)

    def extract_and_verify_citations(
        self,
        response_text: str,
        valid_citations: List[MemoryCitation]
    ) -> Tuple[List[str], List[str]]:
        """Verify that all cited memories in LLM response correspond to retrieved memories."""
        valid_ids = {str(c.memory_id).lower() for c in valid_citations}
        cited_matches = re.findall(r"\[Memory:\s*([a-f0-9\-]+)\]", response_text, re.IGNORECASE)

        verified = []
        hallucinated_citations = []

        for cite_id in cited_matches:
            cleaned_id = cite_id.strip().lower()
            if cleaned_id in valid_ids:
                verified.append(cleaned_id)
            else:
                hallucinated_citations.append(cleaned_id)

        return verified, hallucinated_citations

    def answer_query(
        self,
        query: str,
        citations: List[MemoryCitation]
    ) -> GroundedQueryResponse:
        """Generate a grounded, cited response to a user query."""
        if not citations:
            return GroundedQueryResponse(
                query=query,
                answer=(
                    "I do not have verified personal memories or records regarding this topic in your knowledge base. "
                    "You can provide this information by ingesting documents or adding memories directly."
                ),
                citations=[],
                inferred_recommendations=[],
                conflicts_detected=[],
                grounded=True,
                model_used=getattr(self.llm, "model", "unknown")
            )

        context_block = self.build_memory_context(citations)
        user_prompt = f"{context_block}\n\nUser Question:\n{query}"

        raw_response = self.llm.generate(
            system_prompt=GROUNDING_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            temperature=0.1
        )

        verified_cites, unverified_cites = self.extract_and_verify_citations(raw_response, citations)

        # Extract explicit inferences if tagged
        inferences = [
            line.strip() for line in raw_response.split("\n")
            if "[inference" in line.lower() or "[recommendation" in line.lower()
        ]

        conflicts = []
        if unverified_cites:
            conflicts.append(f"Model cited ungrounded memory references: {unverified_cites}")

        return GroundedQueryResponse(
            query=query,
            answer=raw_response,
            citations=citations,
            inferred_recommendations=inferences,
            conflicts_detected=conflicts,
            grounded=len(unverified_cites) == 0,
            model_used=getattr(self.llm, "model", "unknown")
        )


grounding_service = GroundingService()
