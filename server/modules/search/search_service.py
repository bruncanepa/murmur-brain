"""
Vector search service.

Performs semantic search over document embeddings using cosine similarity.
"""
from typing import List, Dict, Optional
from .search_model import VectorRepository, SearchResponse, SearchResultItem
from core.ollama_client import OllamaClient
from core.config import get_settings


class SearchService:
    """Service for semantic vector search with dependency injection."""

    def __init__(
        self,
        vector_repo: VectorRepository,
        ollama_client: OllamaClient
    ):
        self.vector_repo = vector_repo
        self.ollama = ollama_client
        self.settings = get_settings()

    def search(
        self,
        query: str,
        top_k: int = None,
        threshold: float = None,
        doc_ids: Optional[List[str]] = None
    ) -> SearchResponse:
        """
        Perform semantic search over stored document chunks.

        Args:
            query: Search query text
            top_k: Number of top results to return
            threshold: Minimum similarity score (0-1)
            doc_ids: Optional list of document IDs to filter by

        Returns:
            SearchResponse with results and metadata

        Raises:
            Exception: If search fails
        """
        # Use defaults from settings if not provided
        if top_k is None:
            top_k = self.settings.default_top_k
        if threshold is None:
            threshold = self.settings.default_similarity_threshold

        # Validate parameters
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")

        if top_k < 1 or top_k > 100:
            raise ValueError("top_k must be between 1 and 100")

        if threshold < 0.0 or threshold > 1.0:
            raise ValueError("threshold must be between 0.0 and 1.0")

        try:
            # Generate embedding for query
            print(f"Generating embedding for query: '{query}'")
            query_embedding = self.ollama.generate_embedding(query)

            if not query_embedding:
                raise Exception("Failed to generate query embedding")

            # Fetch vectors from database
            vectors = self.vector_repo.get_vectors_with_documents(doc_ids)

            if not vectors:
                return SearchResponse(
                    success=True,
                    results=[],
                    query=query,
                    total_searched=0,
                    total_matches=0,
                    returned=0
                )

            # Calculate similarities
            results = []
            for row in vectors:
                # Decode embedding
                embedding_blob = row.get("embedding")
                if not embedding_blob:
                    continue

                stored_embedding = self.vector_repo.decode_embedding(embedding_blob)
                if not stored_embedding:
                    continue

                # Calculate cosine similarity
                similarity = self.vector_repo.cosine_similarity(query_embedding, stored_embedding)

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

            return SearchResponse(
                success=True,
                results=[SearchResultItem(**r) for r in top_results],
                query=query,
                total_searched=len(vectors),
                total_matches=len(results),
                returned=len(top_results)
            )

        except Exception as e:
            print(f"Error during vector search: {e}")
            raise e
