"""
Search models and repository.

Defines Pydantic schemas for search API and vector repository.
"""
import json
import math
import numpy as np
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from core.database import BaseRepository, DatabaseConnection


# ============ Pydantic Schemas ============

class SearchRequest(BaseModel):
    """Schema for search request."""
    query: str
    top_k: int = Field(default=5, ge=1, le=100)
    threshold: float = Field(default=0.0, ge=0.0, le=1.0)
    doc_ids: Optional[List[str]] = None


class SearchResultItem(BaseModel):
    """Schema for a single search result."""
    vector_id: str
    doc_id: str
    chunk_index: int
    chunk_text: str
    similarity: float
    document: Dict[str, Any]


class SearchResponse(BaseModel):
    """Schema for search response."""
    success: bool
    results: List[SearchResultItem]
    query: str
    total_searched: int
    total_matches: int
    returned: int


# ============ Repository ============

class VectorRepository(BaseRepository):
    """Repository for vector operations."""

    def get_vectors_with_documents(
        self,
        doc_ids: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all vectors with their document metadata.

        Args:
            doc_ids: Optional list of document IDs to filter by

        Returns:
            List of vector dictionaries with document info
        """
        if doc_ids:
            placeholders = ','.join(['?'] * len(doc_ids))
            query = f"""
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
                    AND v.doc_id IN ({placeholders})
                ORDER BY v.doc_id, v.chunk_index
            """
            rows = self.db.fetchall(query, tuple(doc_ids))
        else:
            query = """
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
                ORDER BY v.doc_id, v.chunk_index
            """
            rows = self.db.fetchall(query)

        return self._dicts_from_rows(rows)

    def decode_embedding(self, embedding_blob: bytes) -> Optional[List[float]]:
        """
        Decode embedding from BLOB storage.

        Args:
            embedding_blob: Binary embedding data

        Returns:
            List of floats or None if decoding fails
        """
        if not embedding_blob:
            return None

        try:
            return json.loads(embedding_blob.decode('utf-8'))
        except Exception as e:
            print(f"Error decoding embedding: {e}")
            return None

    @staticmethod
    def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
        """
        Calculate cosine similarity between two vectors.

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

        # Normalize to 0-1 range
        return max(0.0, min(1.0, similarity))

