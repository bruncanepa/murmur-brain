"""
Vector search service.

Performs semantic search over document embeddings using cosine similarity.
"""
from typing import List, Dict, Optional
from .search_model import VectorRepository, SearchResponse, SearchResultItem
from core.ollama_client import OllamaClient
from core.config import get_settings
from core.faiss_manager import FaissIndexManager


class SearchService:
    """Service for semantic vector search with dependency injection."""

    def __init__(
        self,
        vector_repo: VectorRepository,
        ollama_client: OllamaClient,
        faiss_manager: FaissIndexManager
    ):
        self.vector_repo = vector_repo
        self.ollama = ollama_client
        self.faiss_manager = faiss_manager
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

            # Initialize tracking variables
            total_searched = 0
            filtered_results = []

            # Try FAISS search first (50-100x faster), fallback to Python loop
            try:
                print(f"Attempting FAISS search (top_k={top_k}, threshold={threshold})")

                # Get vector IDs filter if doc_ids provided
                vector_ids_filter = None
                if doc_ids:
                    # Get all vector IDs for the specified documents
                    vectors = self.vector_repo.get_vectors_with_documents(doc_ids)
                    vector_ids_filter = [v["vector_id"] for v in vectors]

                # Search with FAISS
                faiss_results = self.faiss_manager.search(
                    query_embedding=query_embedding,
                    top_k=top_k * 2,  # Get more to filter by threshold
                    vector_ids_filter=vector_ids_filter
                )

                if not faiss_results:
                    return SearchResponse(
                        success=True,
                        results=[],
                        query=query,
                        total_searched=0,
                        total_matches=0,
                        returned=0
                    )

                # Get document metadata for results
                vector_ids = [vid for vid, _ in faiss_results]
                placeholders = ','.join(['?'] * len(vector_ids))
                query_sql = f"""
                    SELECT
                        v.id as vector_id,
                        v.doc_id,
                        v.chunk_index,
                        v.chunk_text,
                        d.file_name,
                        d.file_type,
                        d.upload_date
                    FROM vectors v
                    JOIN documents d ON v.doc_id = d.id
                    WHERE v.id IN ({placeholders})
                """
                rows = self.vector_repo.db.fetchall(query_sql, tuple(vector_ids))

                # Create lookup for metadata
                metadata_lookup = {row["vector_id"]: row for row in rows}

                total_searched = len(faiss_results)

                # Filter by threshold and format results
                for vector_id, similarity in faiss_results:
                    # Apply threshold
                    if similarity >= threshold:
                        metadata = metadata_lookup.get(vector_id)
                        if metadata:
                            filtered_results.append({
                                "vector_id": vector_id,
                                "doc_id": metadata["doc_id"],
                                "chunk_index": metadata["chunk_index"],
                                "chunk_text": metadata["chunk_text"],
                                "similarity": round(similarity, 4),
                                "document": {
                                    "file_name": metadata["file_name"],
                                    "file_type": metadata["file_type"],
                                    "upload_date": metadata["upload_date"]
                                }
                            })

                    # Stop if we have enough results
                    if len(filtered_results) >= top_k:
                        break

                print(f"FAISS search complete: {len(filtered_results)} results above threshold {threshold}")

            except Exception as search_error:
                # Fallback to Python loop if FAISS search fails
                print(f"FAISS search failed, falling back to Python loop: {search_error}")
                import traceback
                traceback.print_exc()

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

                total_searched = len(vectors)

                # Calculate similarities with Python
                for row in vectors:
                    embedding_blob = row.get("embedding")
                    if not embedding_blob:
                        continue

                    stored_embedding = self.vector_repo.decode_embedding(embedding_blob)
                    if not stored_embedding:
                        continue

                    similarity = self.vector_repo.cosine_similarity(query_embedding, stored_embedding)

                    if similarity >= threshold:
                        filtered_results.append({
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

                # Sort by similarity
                filtered_results.sort(key=lambda x: x["similarity"], reverse=True)
                filtered_results = filtered_results[:top_k]

                print(f"Python fallback complete: {len(filtered_results)} results from {total_searched} vectors")

            return SearchResponse(
                success=True,
                results=[SearchResultItem(**r) for r in filtered_results],
                query=query,
                total_searched=total_searched,
                total_matches=len(filtered_results),
                returned=len(filtered_results)
            )

        except Exception as e:
            print(f"Error during vector search: {e}")
            raise e
