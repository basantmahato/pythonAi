import json
import logging
from typing import List, Dict, Any, Optional
from google import genai
from google.genai import types
from src.config.settings import settings

logger = logging.getLogger(__name__)

class GeminiLLMService:
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model = model or settings.LLM_MODEL

        if not self.api_key or self.api_key == "your_gemini_api_key_here":
            logger.warning("GEMINI_API_KEY is not configured in .env. LLM calls will fail until set.")

        self.client = genai.Client(api_key=self.api_key)

    def _call_json(self, prompt: str) -> Dict[str, Any]:
        """Helper to invoke Gemini with enforced JSON output."""
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.0,
                    response_mime_type="application/json"
                )
            )
            raw_text = response.text.strip()
            return json.loads(raw_text)
        except json.JSONDecodeError:
            # Fallback cleanup for occasional markdown fences
            clean_text = raw_text.replace("```json", "").replace("```", "").strip()
            return json.loads(clean_text)
        except Exception as e:
            logger.error(f"Error calling Gemini LLM (JSON): {e}")
            raise

    def grade_document_relevance(self, query: str, chunk_content: str) -> Dict[str, Any]:
        """
        Evaluate whether a retrieved chunk contains information relevant to the query.
        Returns: {"is_relevant": bool, "reason": str}
        """
        prompt = f"""You are an expert evaluator assessing relevance of retrieved documents for a RAG system.
Evaluate whether the following retrieved document chunk contains information relevant to answering the query.

User Query:
{query}

Retrieved Document Chunk:
{chunk_content}

Respond strictly in JSON format with:
{{
  "is_relevant": true or false,
  "reason": "brief explanation"
}}
"""
        try:
            result = self._call_json(prompt)
            return {
                "is_relevant": bool(result.get("is_relevant", False)),
                "reason": str(result.get("reason", ""))
            }
        except Exception as e:
            logger.warning(f"Grading failed for chunk, defaulting to True: {e}")
            return {"is_relevant": True, "reason": "Evaluator fallback"}

    def rewrite_query(self, original_query: str, failed_queries: List[str] = None) -> str:
        """
        Rewrite user query into an optimized search query for vector retrieval.
        """
        history = ""
        if failed_queries:
            history = f"Previously attempted queries that yielded poor results: {failed_queries}\n"

        prompt = f"""You are a query optimization assistant for a vector search RAG system.
Your job is to rewrite the user's query to improve semantic retrieval quality.
Formulate a clear, specific, keyword-rich search query that captures the core semantic intent.

{history}User Query:
{original_query}

Respond strictly in JSON format with:
{{
  "rewritten_query": "the rewritten query string",
  "rationale": "short explanation of transformation"
}}
"""
        try:
            result = self._call_json(prompt)
            rewritten = result.get("rewritten_query", "").strip()
            return rewritten if rewritten else original_query
        except Exception as e:
            logger.warning(f"Query rewrite failed, falling back to original query: {e}")
            return original_query

    def generate_answer(self, query: str, context_chunks: List[str]) -> str:
        """
        Synthesize a final response based on retrieved and verified context chunks.
        """
        formatted_context = "\n\n---\n\n".join(
            [f"[Document {i+1}]:\n{chunk}" for i, chunk in enumerate(context_chunks)]
        )

        prompt = f"""You are an intelligent knowledge assistant in an Agentic RAG system.
Answer the user's question accurately, concisely, and truthfully using ONLY the provided context.
If the answer cannot be deduced from the provided context, clearly state: "I do not have enough information in the provided documents to answer this question."

Context:
{formatted_context}

Question:
{query}

Answer:"""

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.2
                )
            )
            return response.text.strip()
        except Exception as e:
            logger.error(f"Failed to generate answer with Gemini: {e}")
            raise

    def check_hallucination(self, context_chunks: List[str], answer: str) -> Dict[str, Any]:
        """
        Verify if the generated answer is strictly grounded in the context chunks (factual check).
        """
        context = "\n\n".join(context_chunks)
        prompt = f"""You are a strict hallucination evaluator for a RAG system.
Assess whether the generated answer is strictly supported by and grounded in the provided context facts.
If the answer makes claims NOT supported by the context, flag is_grounded as false.

Context:
{context}

Generated Answer:
{answer}

Respond strictly in JSON format with:
{{
  "is_grounded": true or false,
  "reason": "explanation of whether it is grounded or contains hallucinations"
}}
"""
        try:
            result = self._call_json(prompt)
            return {
                "is_grounded": bool(result.get("is_grounded", True)),
                "reason": str(result.get("reason", ""))
            }
        except Exception as e:
            logger.warning(f"Hallucination check failed, defaulting to True: {e}")
            return {"is_grounded": True, "reason": "Check fallback"}

    def check_answer_quality(self, query: str, answer: str) -> Dict[str, Any]:
        """
        Verify if the generated answer directly addresses the user's original query.
        """
        prompt = f"""You are an answer evaluator for a RAG system.
Assess whether the generated answer directly and satisfactorily addresses the user's query.

User Query:
{query}

Generated Answer:
{answer}

Respond strictly in JSON format with:
{{
  "addresses_query": true or false,
  "reason": "brief explanation"
}}
"""
        try:
            result = self._call_json(prompt)
            return {
                "addresses_query": bool(result.get("addresses_query", True)),
                "reason": str(result.get("reason", ""))
            }
        except Exception as e:
            logger.warning(f"Answer quality check failed, defaulting to True: {e}")
            return {"addresses_query": True, "reason": "Check fallback"}
