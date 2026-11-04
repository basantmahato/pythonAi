import os
import uuid
import chromadb
from typing import List, Dict, Any, Optional

class VectorService:
    def __init__(self):
        # Store ChromaDB data in ai-backend/data/chroma_db
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        db_path = os.path.join(base_dir, "data", "chroma_db")
        os.makedirs(db_path, exist_ok=True)
        
        self.client = chromadb.PersistentClient(path=db_path)

    @property
    def collection(self):
        """Always return an active, non-stale collection reference."""
        return self.client.get_or_create_collection(
            name="conversation_memory",
            metadata={"hnsw:space": "cosine"}
        )

    def add_memory(self, text: str, metadata: Optional[Dict[str, Any]] = None, doc_id: Optional[str] = None) -> str:
        """Store an interaction or knowledge snippet in ChromaDB."""
        uid = doc_id or str(uuid.uuid4())
        # ChromaDB 1.5+ requires non-empty dict for metadata if provided
        meta = metadata if (metadata and len(metadata) > 0) else {"type": "memory"}
        
        self.collection.add(
            ids=[uid],
            documents=[text],
            metadatas=[meta]
        )
        return uid

    def search_relevant(self, query: str, top_k: int = 3, max_distance: float = 0.75) -> List[str]:
        """Search for relevant past memories. Filters out irrelevant matches using cosine distance."""
        try:
            count = self.collection.count()
        except Exception:
            return []

        if count == 0:
            return []

        actual_k = min(top_k, count)
        results = self.collection.query(
            query_texts=[query],
            n_results=actual_k
        )

        documents = results.get("documents", [[]])[0]
        distances = results.get("distances", [[]])[0] if "distances" in results else []

        relevant_docs = []
        for i, doc in enumerate(documents):
            # Only include if semantic distance is within the relevant threshold
            dist = distances[i] if i < len(distances) else 0.0
            if dist is None or dist <= max_distance:
                relevant_docs.append(doc)

        return relevant_docs

    def count_memories(self) -> int:
        try:
            return self.collection.count()
        except Exception:
            return 0

    def clear_all(self):
        """Clears all stored memories from the collection safely."""
        try:
            self.client.delete_collection("conversation_memory")
        except Exception:
            pass
        # Force recreation
        _ = self.collection
