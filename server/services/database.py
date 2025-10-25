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
        """Create database tables if they don't exist"""
        # Documents table with UUID
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS documents (
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
            CREATE TABLE IF NOT EXISTS vectors (
                id TEXT PRIMARY KEY,
                doc_id TEXT NOT NULL,
                chunk_index INTEGER NOT NULL,
                chunk_text TEXT NOT NULL,
                embedding BLOB,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (doc_id) REFERENCES documents(id) ON DELETE CASCADE
            )
        """)

        # Chats table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS chats (
                id TEXT PRIMARY KEY,
                title TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Chat documents (many-to-many relationship)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS chat_documents (
                id TEXT PRIMARY KEY,
                chat_id TEXT NOT NULL,
                doc_id TEXT NOT NULL,
                added_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (chat_id) REFERENCES chats(id) ON DELETE CASCADE,
                FOREIGN KEY (doc_id) REFERENCES documents(id) ON DELETE CASCADE,
                UNIQUE(chat_id, doc_id)
            )
        """)

        # Messages table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                chat_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                sources TEXT,
                model_used TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (chat_id) REFERENCES chats(id) ON DELETE CASCADE
            )
        """)

        # Create indexes if they don't exist
        self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_vectors_doc_id ON vectors(doc_id)
        """)
        self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_documents_upload_date ON documents(upload_date)
        """)
        self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_messages_chat_id ON messages(chat_id)
        """)
        self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_chat_documents_chat_id ON chat_documents(chat_id)
        """)
        self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_chats_updated_at ON chats(updated_at)
        """)

        self.conn.commit()

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

    # ============ Chat Management Methods ============

    def create_chat(self, title: Optional[str] = None) -> Dict:
        """Create a new chat session"""
        try:
            chat_id = str(uuid.uuid4())
            self.conn.execute("""
                INSERT INTO chats (id, title)
                VALUES (?, ?)
            """, (chat_id, title))
            self.conn.commit()

            return {
                "success": True,
                "chatId": chat_id
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def get_chats(self) -> Dict:
        """Get all chats with message count"""
        try:
            cursor = self.conn.execute("""
                SELECT
                    c.*,
                    COUNT(m.id) as message_count,
                    MAX(m.created_at) as last_message_at
                FROM chats c
                LEFT JOIN messages m ON c.id = m.chat_id
                GROUP BY c.id
                ORDER BY c.updated_at DESC
            """)
            chats = [dict(row) for row in cursor.fetchall()]

            return {
                "success": True,
                "chats": chats
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def get_chat(self, chat_id: str) -> Dict:
        """Get chat by ID with its messages"""
        try:
            # Get chat info
            chat_cursor = self.conn.execute("""
                SELECT * FROM chats WHERE id = ?
            """, (chat_id,))
            chat = chat_cursor.fetchone()

            if not chat:
                return {
                    "success": False,
                    "error": "Chat not found"
                }

            # Get messages
            messages_cursor = self.conn.execute("""
                SELECT * FROM messages
                WHERE chat_id = ?
                ORDER BY created_at ASC
            """, (chat_id,))
            messages = [dict(row) for row in messages_cursor.fetchall()]

            # Parse sources JSON for each message
            for msg in messages:
                if msg.get("sources"):
                    try:
                        msg["sources"] = json.loads(msg["sources"])
                    except:
                        msg["sources"] = None

            return {
                "success": True,
                "chat": dict(chat),
                "messages": messages
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def delete_chat(self, chat_id: str) -> Dict:
        """Delete a chat and all its messages"""
        try:
            self.conn.execute("DELETE FROM chats WHERE id = ?", (chat_id,))
            self.conn.commit()

            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def add_message(self, chat_id: str, role: str, content: str,
                   sources: Optional[List[Dict]] = None,
                   model_used: Optional[str] = None) -> Dict:
        """Add a message to a chat"""
        try:
            message_id = str(uuid.uuid4())
            sources_json = json.dumps(sources) if sources else None

            self.conn.execute("""
                INSERT INTO messages (id, chat_id, role, content, sources, model_used)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (message_id, chat_id, role, content, sources_json, model_used))

            # Update chat's updated_at timestamp
            self.conn.execute("""
                UPDATE chats SET updated_at = CURRENT_TIMESTAMP WHERE id = ?
            """, (chat_id,))

            self.conn.commit()

            return {
                "success": True,
                "messageId": message_id
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def get_messages(self, chat_id: str) -> Dict:
        """Get all messages for a chat"""
        try:
            cursor = self.conn.execute("""
                SELECT * FROM messages
                WHERE chat_id = ?
                ORDER BY created_at ASC
            """, (chat_id,))
            messages = [dict(row) for row in cursor.fetchall()]

            # Parse sources JSON
            for msg in messages:
                if msg.get("sources"):
                    try:
                        msg["sources"] = json.loads(msg["sources"])
                    except:
                        msg["sources"] = None

            return {
                "success": True,
                "messages": messages
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def link_document_to_chat(self, chat_id: str, doc_id: str) -> Dict:
        """Link a document to a chat"""
        try:
            link_id = str(uuid.uuid4())
            self.conn.execute("""
                INSERT OR IGNORE INTO chat_documents (id, chat_id, doc_id)
                VALUES (?, ?, ?)
            """, (link_id, chat_id, doc_id))
            self.conn.commit()

            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def unlink_document_from_chat(self, chat_id: str, doc_id: str) -> Dict:
        """Remove document link from a chat"""
        try:
            self.conn.execute("""
                DELETE FROM chat_documents
                WHERE chat_id = ? AND doc_id = ?
            """, (chat_id, doc_id))
            self.conn.commit()

            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_chat_documents(self, chat_id: str) -> Dict:
        """Get all documents linked to a chat"""
        try:
            cursor = self.conn.execute("""
                SELECT d.*, cd.added_at
                FROM documents d
                JOIN chat_documents cd ON d.id = cd.doc_id
                WHERE cd.chat_id = ?
                ORDER BY cd.added_at DESC
            """, (chat_id,))
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

    def update_chat_title(self, chat_id: str, title: str) -> Dict:
        """Update chat title"""
        try:
            self.conn.execute("""
                UPDATE chats SET title = ? WHERE id = ?
            """, (title, chat_id))
            self.conn.commit()

            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def update_chat_timestamp(self, chat_id: str) -> Dict:
        """Update chat's updated_at timestamp"""
        try:
            self.conn.execute("""
                UPDATE chats SET updated_at = CURRENT_TIMESTAMP WHERE id = ?
            """, (chat_id,))
            self.conn.commit()

            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}


# Singleton instance
_db_instance = None

def get_database() -> VectorDatabase:
    global _db_instance
    if _db_instance is None:
        _db_instance = VectorDatabase()
    return _db_instance
