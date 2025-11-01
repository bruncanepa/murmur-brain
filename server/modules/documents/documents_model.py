"""
Document models and repository.

Defines Pydantic schemas for API validation and database repository for document operations.
"""
import uuid
import json
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from core.database import BaseRepository, DatabaseConnection


# ============ Pydantic Schemas ============

class DocumentCreate(BaseModel):
    """Schema for creating a new document."""
    file_name: str
    file_type: str
    file_size: int
    file_path: Optional[str] = None
    chunk_count: int = 0


class DocumentResponse(BaseModel):
    """Schema for document response."""
    id: str
    file_name: str
    file_type: str
    file_size: int
    file_path: Optional[str] = None
    upload_date: str
    chunk_count: int
    status: str


class DocumentWithVectors(DocumentResponse):
    """Schema for document with its vectors."""
    vectors: List[Dict[str, Any]] = []


class VectorCreate(BaseModel):
    """Schema for creating a vector chunk."""
    doc_id: str
    chunk_index: int
    chunk_text: str
    embedding: List[float] = []


class VectorResponse(BaseModel):
    """Schema for vector response."""
    id: str
    doc_id: str
    chunk_index: int
    chunk_text: str
    created_at: str


# ============ Repository ============

class DocumentRepository(BaseRepository):
    """Repository for document database operations."""

    def __init__(self, db: DatabaseConnection, faiss_manager=None):
        super().__init__(db)
        self.faiss_manager = faiss_manager

    def create(self, document: DocumentCreate) -> str:
        """
        Create a new document record.

        Args:
            document: Document creation data

        Returns:
            Document ID

        Raises:
            Exception: If document creation fails
        """
        doc_id = str(uuid.uuid4())

        self.db.execute("""
            INSERT INTO documents (id, file_name, file_path, file_type, file_size, chunk_count)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            doc_id,
            document.file_name,
            document.file_path,
            document.file_type,
            document.file_size,
            document.chunk_count
        ))
        self.db.commit()

        return doc_id

    def get_by_id(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Get document by ID."""
        row = self.db.fetchone("""
            SELECT * FROM documents WHERE id = ?
        """, (doc_id,))

        return self._dict_from_row(row)

    def get_all(self) -> List[Dict[str, Any]]:
        """Get all documents ordered by upload date."""
        rows = self.db.fetchall("""
            SELECT * FROM documents ORDER BY upload_date DESC
        """)

        return self._dicts_from_rows(rows)

    def delete(self, doc_id: str) -> bool:
        """
        Delete a document and its vectors (including FAISS index).

        Args:
            doc_id: Document ID

        Returns:
            True if deleted, False if not found
        """
        try:
            # Get all vector IDs for this document
            vectors = self.db.fetchall(
                "SELECT id FROM vectors WHERE doc_id = ?",
                (doc_id,)
            )
            vector_ids = [v["id"] for v in vectors]

            # Remove from FAISS index
            if vector_ids and self.faiss_manager:
                try:
                    self.faiss_manager.remove_vectors(vector_ids)
                    self.faiss_manager.save()
                except Exception as e:
                    print(f"Warning: Could not remove vectors from FAISS index: {e}")

            # Delete document (vectors cascade delete)
            result = self.db.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
            self.db.commit()
            return result.rowcount > 0

        except Exception as e:
            self.db.rollback()
            raise e

    def update_status(self, doc_id: str, status: str):
        """Update document processing status."""
        self.db.execute("""
            UPDATE documents SET status = ? WHERE id = ?
        """, (status, doc_id))
        self.db.commit()

    def add_vectors(self, doc_id: str, chunks: List[Dict]) -> int:
        """
        Add vector chunks for a document and index in FAISS.

        Args:
            doc_id: Document ID
            chunks: List of chunks with text and embedding

        Returns:
            Number of vectors added

        Raises:
            Exception: If adding vectors fails
        """
        try:
            count = 0
            vector_ids = []
            embeddings = []

            for chunk in chunks:
                vector_id = str(uuid.uuid4())
                embedding_blob = None
                if chunk.get("embedding"):
                    embedding_blob = json.dumps(chunk["embedding"]).encode()

                # Insert into vectors table
                self.db.execute("""
                    INSERT INTO vectors (id, doc_id, chunk_index, chunk_text, embedding)
                    VALUES (?, ?, ?, ?, ?)
                """, (vector_id, doc_id, chunk["index"], chunk["text"], embedding_blob))

                # Collect for FAISS indexing
                if chunk.get("embedding"):
                    vector_ids.append(vector_id)
                    embeddings.append(chunk["embedding"])

                count += 1

            self.db.commit()

            # Add to FAISS index
            if vector_ids and embeddings and self.faiss_manager:
                try:
                    self.faiss_manager.add_vectors(vector_ids, embeddings)
                    self.faiss_manager.save()
                    print(f"Added {len(vector_ids)} vectors to FAISS index")
                except Exception as e:
                    print(f"Warning: Could not add vectors to FAISS index: {e}")

            return count

        except Exception as e:
            self.db.rollback()
            raise e

    def get_vectors_by_doc_id(self, doc_id: str) -> List[Dict[str, Any]]:
        """Get all vectors for a document."""
        rows = self.db.fetchall("""
            SELECT id, doc_id, chunk_index, chunk_text, created_at
            FROM vectors
            WHERE doc_id = ?
            ORDER BY chunk_index ASC
        """, (doc_id,))

        return self._dicts_from_rows(rows)

    def get_stats(self) -> Dict[str, int]:
        """Get document and vector statistics."""
        doc_count = self.db.fetchone("SELECT COUNT(*) as count FROM documents")["count"]
        vector_count = self.db.fetchone("SELECT COUNT(*) as count FROM vectors")["count"]

        return {
            "document_count": doc_count,
            "vector_count": vector_count
        }
