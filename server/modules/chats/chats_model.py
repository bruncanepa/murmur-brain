"""
Chat models and repository.

Defines Pydantic schemas for chat API and database repository for chat operations.
"""
import uuid
import json
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from core.database import BaseRepository, DatabaseConnection


# ============ Pydantic Schemas ============

class ChatCreate(BaseModel):
    """Schema for creating a new chat."""
    title: Optional[str] = None
    doc_ids: List[str] = Field(default_factory=list)


class ChatResponse(BaseModel):
    """Schema for chat response."""
    id: str
    title: Optional[str] = None
    documents: str  # JSON string
    created_at: str
    updated_at: str
    message_count: Optional[int] = None
    last_message_at: Optional[str] = None


class ChatWithMessages(ChatResponse):
    """Schema for chat with its messages."""
    messages: List[Dict[str, Any]] = []


class ChatTitleUpdate(BaseModel):
    """Schema for updating chat title."""
    title: str


class DocumentLink(BaseModel):
    """Schema for linking a document to a chat."""
    doc_id: str


# ============ Repository ============

class ChatRepository(BaseRepository):
    """Repository for chat database operations."""

    def __init__(self, db: DatabaseConnection):
        super().__init__(db)
        self._ensure_tables()
        self._migrate_chat_documents()

    def _ensure_tables(self):
        """Ensure chats table exists."""
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS chats (
                id TEXT PRIMARY KEY,
                title TEXT,
                documents TEXT DEFAULT '[]',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        self.db.execute("""
            CREATE INDEX IF NOT EXISTS idx_chats_updated_at ON chats(updated_at)
        """)

        self.db.commit()

    def _migrate_chat_documents(self):
        """
        Migrate data from chat_documents junction table to documents JSONB column.
        This is a one-time migration that safely handles the transition.
        """
        try:
            # Check if chat_documents table exists
            cursor = self.db.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name='chat_documents'
            """)
            if not cursor.fetchone():
                return  # Table doesn't exist, nothing to migrate

            # Check if we need to add documents column to existing chats table
            cursor = self.db.execute("PRAGMA table_info(chats)")
            columns = [row[1] for row in cursor.fetchall()]
            if 'documents' not in columns:
                # Add documents column with default empty array
                self.db.execute("""
                    ALTER TABLE chats ADD COLUMN documents TEXT DEFAULT '[]'
                """)
                self.db.commit()

            # Migrate data from chat_documents to chats.documents
            cursor = self.db.execute("""
                SELECT chat_id, doc_id, added_at
                FROM chat_documents
                ORDER BY chat_id, added_at
            """)

            # Group by chat_id
            chat_docs = {}
            for row in cursor.fetchall():
                chat_id, doc_id, added_at = row
                if chat_id not in chat_docs:
                    chat_docs[chat_id] = []
                chat_docs[chat_id].append({
                    "document_id": doc_id,
                    "created_at": added_at
                })

            # Update each chat with its documents array
            for chat_id, docs in chat_docs.items():
                docs_json = json.dumps(docs)
                self.db.execute("""
                    UPDATE chats SET documents = ? WHERE id = ?
                """, (docs_json, chat_id))

            self.db.commit()

            # Drop the old chat_documents table
            self.db.execute("DROP TABLE IF EXISTS chat_documents")
            self.db.commit()

            if chat_docs:
                print(f"Migrated {len(chat_docs)} chats from chat_documents to JSONB")

        except Exception as e:
            print(f"Migration warning: {e}")
            # Don't fail initialization if migration has issues
            pass

    def create(self, title: Optional[str] = None) -> str:
        """
        Create a new chat session.

        Args:
            title: Optional chat title

        Returns:
            Chat ID

        Raises:
            Exception: If chat creation fails
        """
        chat_id = str(uuid.uuid4())
        self.db.execute("""
            INSERT INTO chats (id, title)
            VALUES (?, ?)
        """, (chat_id, title))
        self.db.commit()

        return chat_id

    def get_by_id(self, chat_id: str) -> Optional[Dict[str, Any]]:
        """Get chat by ID."""
        row = self.db.fetchone("""
            SELECT * FROM chats WHERE id = ?
        """, (chat_id,))

        return self._dict_from_row(row)

    def get_all(self) -> List[Dict[str, Any]]:
        """Get all chats with message count and last message timestamp."""
        rows = self.db.fetchall("""
            SELECT
                c.*,
                COUNT(m.id) as message_count,
                MAX(m.created_at) as last_message_at
            FROM chats c
            LEFT JOIN messages m ON c.id = m.chat_id
            GROUP BY c.id
            ORDER BY c.updated_at DESC
        """)

        return self._dicts_from_rows(rows)

    def delete(self, chat_id: str) -> bool:
        """
        Delete a chat and all its messages.

        Args:
            chat_id: Chat ID

        Returns:
            True if deleted, False if not found
        """
        result = self.db.execute("DELETE FROM chats WHERE id = ?", (chat_id,))
        self.db.commit()
        return result.rowcount > 0

    def update_title(self, chat_id: str, title: str):
        """Update chat title."""
        self.db.execute("""
            UPDATE chats SET title = ? WHERE id = ?
        """, (title, chat_id))
        self.db.commit()

    def update_timestamp(self, chat_id: str):
        """Update chat's updated_at timestamp."""
        self.db.execute("""
            UPDATE chats SET updated_at = CURRENT_TIMESTAMP WHERE id = ?
        """, (chat_id,))
        self.db.commit()

    def link_document(self, chat_id: str, doc_id: str) -> bool:
        """
        Link a document to a chat by adding it to the documents JSONB array.

        Args:
            chat_id: Chat ID
            doc_id: Document ID

        Returns:
            True if successful

        Raises:
            ValueError: If chat not found
        """
        # Get current documents array
        row = self.db.fetchone("""
            SELECT documents FROM chats WHERE id = ?
        """, (chat_id,))

        if not row:
            raise ValueError("Chat not found")

        # Parse existing documents
        current_docs = json.loads(row[0] or '[]')

        # Check if document is already linked
        if any(doc['document_id'] == doc_id for doc in current_docs):
            return True  # Already linked

        # Add new document with timestamp
        current_docs.append({
            "document_id": doc_id,
            "created_at": datetime.now().isoformat()
        })

        # Update the chat
        self.db.execute("""
            UPDATE chats SET documents = ? WHERE id = ?
        """, (json.dumps(current_docs), chat_id))
        self.db.commit()

        return True

    def unlink_document(self, chat_id: str, doc_id: str) -> bool:
        """
        Remove document link from a chat by filtering the documents JSONB array.

        Args:
            chat_id: Chat ID
            doc_id: Document ID

        Returns:
            True if successful

        Raises:
            ValueError: If chat not found
        """
        # Get current documents array
        row = self.db.fetchone("""
            SELECT documents FROM chats WHERE id = ?
        """, (chat_id,))

        if not row:
            raise ValueError("Chat not found")

        # Parse existing documents
        current_docs = json.loads(row[0] or '[]')

        # Filter out the document to unlink
        updated_docs = [doc for doc in current_docs if doc['document_id'] != doc_id]

        # Update the chat
        self.db.execute("""
            UPDATE chats SET documents = ? WHERE id = ?
        """, (json.dumps(updated_docs), chat_id))
        self.db.commit()

        return True

    def get_chat_documents(self, chat_id: str) -> List[Dict[str, Any]]:
        """
        Get all documents linked to a chat from the documents JSONB array.

        Args:
            chat_id: Chat ID

        Returns:
            List of document dictionaries with added_at timestamps

        Raises:
            ValueError: If chat not found
        """
        # Get the chat's documents array
        row = self.db.fetchone("""
            SELECT documents FROM chats WHERE id = ?
        """, (chat_id,))

        if not row:
            raise ValueError("Chat not found")

        # Parse the documents array
        docs_array = json.loads(row[0] or '[]')

        if not docs_array:
            return []

        # Extract document IDs and create a mapping for created_at
        doc_ids = [doc['document_id'] for doc in docs_array]
        created_at_map = {doc['document_id']: doc['created_at'] for doc in docs_array}

        # Fetch document details
        placeholders = ','.join('?' * len(doc_ids))
        rows = self.db.fetchall(f"""
            SELECT * FROM documents
            WHERE id IN ({placeholders})
        """, doc_ids)

        documents = []
        for row in rows:
            doc = dict(row)
            # Add the created_at from the JSONB array (renamed to added_at for compatibility)
            doc['added_at'] = created_at_map.get(doc['id'])
            documents.append(doc)

        # Sort by added_at descending
        documents.sort(key=lambda d: d.get('added_at', ''), reverse=True)

        return documents
