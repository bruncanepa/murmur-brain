import sqlite3
import json
import uuid
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime


class VectorDatabase:
    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            # Use same location as before
            home = Path.home()
            db_dir = home / "Library" / "Application Support" / "local-brain"
            db_dir.mkdir(parents=True, exist_ok=True)
            db_path = str(db_dir / "local-brain.db")

        self.db_path = db_path
        self.conn = None
        self.initialize()

    def initialize(self):
        """Initialize database connection and create tables"""
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row

        # Enable WAL mode
        self.conn.execute("PRAGMA journal_mode=WAL")

        self.create_tables()
        print(f"Database initialized at: {self.db_path}")

    def create_tables(self):
        """Create database tables"""
        # Drop existing tables to force UUID migration
        self.conn.execute("DROP TABLE IF EXISTS vectors")
        self.conn.execute("DROP TABLE IF EXISTS documents")

        print("⚠️  Dropped existing tables - migrating to UUID schema")

        # Documents table with UUID
        self.conn.execute("""
            CREATE TABLE documents (
                id TEXT PRIMARY KEY,
                file_name TEXT NOT NULL,
                file_path TEXT,
                file_type TEXT NOT NULL,
                file_size INTEGER,
                upload_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                chunk_count INTEGER DEFAULT 0,
                status TEXT DEFAULT 'pending'
            )
        """)

        # Vectors table with UUID
        self.conn.execute("""
            CREATE TABLE vectors (
                id TEXT PRIMARY KEY,
                doc_id TEXT NOT NULL,
                chunk_index INTEGER NOT NULL,
                chunk_text TEXT NOT NULL,
                embedding BLOB,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (doc_id) REFERENCES documents(id) ON DELETE CASCADE
            )
        """)

        # Create indexes
        self.conn.execute("""
            CREATE INDEX idx_vectors_doc_id ON vectors(doc_id)
        """)
        self.conn.execute("""
            CREATE INDEX idx_documents_upload_date ON documents(upload_date)
        """)

        self.conn.commit()
        print("✅ Database schema migrated to UUIDs")

    def add_document(self, file_info: Dict) -> Dict:
        """Add a document to the database"""
        try:
            doc_id = str(uuid.uuid4())

            self.conn.execute("""
                INSERT INTO documents (id, file_name, file_path, file_type, file_size, chunk_count)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                doc_id,
                file_info.get("fileName"),
                file_info.get("filePath"),
                file_info.get("fileType"),
                file_info.get("fileSize", 0),
                file_info.get("chunkCount", 0)
            ))
            self.conn.commit()

            return {
                "success": True,
                "documentId": doc_id
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def add_vectors(self, doc_id: str, chunks: List[Dict]) -> Dict:
        """Add multiple vectors in a transaction"""
        try:
            for chunk in chunks:
                vector_id = str(uuid.uuid4())
                embedding_blob = None
                if chunk.get("embedding"):
                    embedding_blob = json.dumps(chunk["embedding"]).encode()

                self.conn.execute("""
                    INSERT INTO vectors (id, doc_id, chunk_index, chunk_text, embedding)
                    VALUES (?, ?, ?, ?, ?)
                """, (vector_id, doc_id, chunk["index"], chunk["text"], embedding_blob))

            self.conn.commit()

            return {"success": True, "count": len(chunks)}
        except Exception as e:
            self.conn.rollback()
            return {"success": False, "error": str(e)}

    def get_documents(self) -> Dict:
        """Get all documents"""
        try:
            cursor = self.conn.execute("""
                SELECT * FROM documents ORDER BY upload_date DESC
            """)
            documents = [dict(row) for row in cursor.fetchall()]

            return {
                "success": True,
                "documents": documents
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def get_document(self, doc_id: str) -> Dict:
        """Get document by ID"""
        try:
            cursor = self.conn.execute("""
                SELECT * FROM documents WHERE id = ?
            """, (doc_id,))
            document = cursor.fetchone()

            if document:
                return {
                    "success": True,
                    "document": dict(document)
                }
            else:
                return {
                    "success": False,
                    "error": "Document not found"
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def delete_document(self, doc_id: str) -> Dict:
        """Delete a document and its vectors"""
        try:
            self.conn.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
            self.conn.commit()

            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def update_document_status(self, doc_id: str, status: str) -> Dict:
        """Update document status"""
        try:
            self.conn.execute("""
                UPDATE documents SET status = ? WHERE id = ?
            """, (status, doc_id))
            self.conn.commit()

            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_stats(self) -> Dict:
        """Get database statistics"""
        try:
            doc_count = self.conn.execute("SELECT COUNT(*) as count FROM documents").fetchone()["count"]
            vector_count = self.conn.execute("SELECT COUNT(*) as count FROM vectors").fetchone()["count"]

            return {
                "success": True,
                "stats": {
                    "documentCount": doc_count,
                    "vectorCount": vector_count
                }
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()


# Singleton instance
_db_instance = None

def get_database() -> VectorDatabase:
    global _db_instance
    if _db_instance is None:
        _db_instance = VectorDatabase()
    return _db_instance
