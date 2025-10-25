import json
import math
from typing import List, Dict, Optional
from services.database import get_database
from services.ollama_service import get_ollama_service


class VectorSearch:
    """Service for performing semantic search over vector embeddings"""

    def __init__(self):
        self.db = get_database()
        self.ollama = get_ollama_service()

    def cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """
        Calculate cosine similarity between two vectors

        Args:
            vec1: First vector
            vec2: Second vector

        Returns:
            Similarity score between 0 and 1 (1 = identical, 0 = orthogonal)
        """
        if not vec1 or not vec2 or len(vec1) != len(vec2):
            return 0.0

        # Calculate dot product
        dot_product = sum(a * b for a, b in zip(vec1, vec2))

        # Calculate magnitudes
        magnitude1 = math.sqrt(sum(a * a for a in vec1))
        magnitude2 = math.sqrt(sum(b * b for b in vec2))

        # Avoid division by zero
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0

        # Cosine similarity = dot product / (magnitude1 * magnitude2)
        similarity = dot_product / (magnitude1 * magnitude2)

        # Normalize to 0-1 range (cosine similarity can be -1 to 1)
        # For embeddings, we typically get 0-1, but normalize just in case
        return max(0.0, min(1.0, similarity))

    def search(
        self,
        query: str,
        top_k: int = 5,
        threshold: float = 0.0,
        doc_ids: Optional[List[str]] = None
    ) -> Dict:
        """
        Perform semantic search over stored document chunks

        Args:
            query: Search query text
            top_k: Number of top results to return
            threshold: Minimum similarity score (0-1)
            doc_ids: Optional list of document IDs to filter by

        Returns:
            Dict with results and metadata
        """
        try:
            # Generate embedding for query
            print(f"Generating embedding for query: '{query}'")
            query_embedding = self.ollama.generate_embedding(query)

            if not query_embedding:
                return {
                    "success": False,
                    "error": "Failed to generate query embedding"
                }

            # Fetch all vectors from database
            cursor = self.db.conn.execute("""
                SELECT
                    v.id as vector_id,
                    v.doc_id,
                    v.chunk_index,
                    v.chunk_text,
                    v.embedding,
                    d.file_name,
                    d.file_type,
                    d.upload_date
                FROM vectors v
                JOIN documents d ON v.doc_id = d.id
                WHERE v.embedding IS NOT NULL
                    {}
                ORDER BY v.doc_id, v.chunk_index
            """.format(
                "AND v.doc_id IN ({})".format(','.join(['?'] * len(doc_ids)))
                if doc_ids else ""
            ), tuple(doc_ids) if doc_ids else ())

            vectors = cursor.fetchall()

            if not vectors:
                return {
                    "success": True,
                    "results": [],
                    "query": query,
                    "total_searched": 0
                }

            # Calculate similarities
            results = []
            for row in vectors:
                # Decode embedding from BLOB
                embedding_blob = row["embedding"]
                if not embedding_blob:
                    continue

                try:
                    stored_embedding = json.loads(embedding_blob.decode('utf-8'))
                except Exception as e:
                    print(f"Error decoding embedding for vector {row['vector_id']}: {e}")
                    continue

                # Calculate cosine similarity
                similarity = self.cosine_similarity(query_embedding, stored_embedding)

                # Apply threshold
                if similarity >= threshold:
                    results.append({
                        "vector_id": row["vector_id"],
                        "doc_id": row["doc_id"],
                        "chunk_index": row["chunk_index"],
                        "chunk_text": row["chunk_text"],
                        "similarity": round(similarity, 4),
                        "document": {
                            "file_name": row["file_name"],
                            "file_type": row["file_type"],
                            "upload_date": row["upload_date"]
                        }
                    })

            # Sort by similarity (descending) and take top_k
            results.sort(key=lambda x: x["similarity"], reverse=True)
            top_results = results[:top_k]

            print(f"Search complete: {len(top_results)} results from {len(vectors)} vectors")

            return {
                "success": True,
                "results": top_results,
                "query": query,
                "total_searched": len(vectors),
                "total_matches": len(results),
                "returned": len(top_results)
            }

        except Exception as e:
            print(f"Error during vector search: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e)
            }


# Singleton instance
_search_instance = None

def get_vector_search() -> VectorSearch:
    global _search_instance
    if _search_instance is None:
        _search_instance = VectorSearch()
    return _search_instance
