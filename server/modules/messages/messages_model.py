"""
Message models and repository.

Defines Pydantic schemas for message API and database repository for message operations.
"""
import uuid
import json
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from core.database import BaseRepository, DatabaseConnection


# ============ Pydantic Schemas ============

class MessageCreate(BaseModel):
    """Schema for creating a new message."""
    message: str
    model: str = "llama3.2"


class MessageResponse(BaseModel):
    """Schema for message response."""
    id: str
    chat_id: str
    role: str
    content: str
    sources: Optional[List[Dict[str, Any]]] = None
    model_used: Optional[str] = None
    created_at: str


class ChatMessageResponse(BaseModel):
    """Schema for chat response with message."""
    success: bool
    response: str
    sources: List[Dict[str, Any]]
    model: str


# ============ Repository ============

class MessageRepository(BaseRepository):
    """Repository for message database operations."""

    def __init__(self, db: DatabaseConnection):
        super().__init__(db)
        self._ensure_tables()

    def _ensure_tables(self):
        """Ensure messages table exists."""
        self.db.execute("""
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

        self.db.execute("""
            CREATE INDEX IF NOT EXISTS idx_messages_chat_id ON messages(chat_id)
        """)

        self.db.commit()

    def create(
        self,
        chat_id: str,
        role: str,
        content: str,
        sources: Optional[List[Dict]] = None,
        model_used: Optional[str] = None
    ) -> str:
        """
        Create a new message in a chat.

        Args:
            chat_id: Chat ID
            role: Message role (user, assistant, system)
            content: Message content
            sources: Optional list of source documents
            model_used: Optional model name used for generation

        Returns:
            Message ID

        Raises:
            Exception: If message creation fails
        """
        message_id = str(uuid.uuid4())
        sources_json = json.dumps(sources) if sources else None

        self.db.execute("""
            INSERT INTO messages (id, chat_id, role, content, sources, model_used)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (message_id, chat_id, role, content, sources_json, model_used))

        # Update chat's updated_at timestamp
        self.db.execute("""
            UPDATE chats SET updated_at = CURRENT_TIMESTAMP WHERE id = ?
        """, (chat_id,))

        self.db.commit()

        return message_id

    def get_by_chat_id(self, chat_id: str) -> List[Dict[str, Any]]:
        """
        Get all messages for a chat.

        Args:
            chat_id: Chat ID

        Returns:
            List of message dictionaries ordered by creation time
        """
        rows = self.db.fetchall("""
            SELECT * FROM messages
            WHERE chat_id = ?
            ORDER BY created_at ASC
        """, (chat_id,))

        messages = self._dicts_from_rows(rows)

        # Parse sources JSON for each message
        for msg in messages:
            if msg.get("sources"):
                try:
                    msg["sources"] = json.loads(msg["sources"])
                except:
                    msg["sources"] = None

        return messages

    def get_by_id(self, message_id: str) -> Optional[Dict[str, Any]]:
        """Get message by ID."""
        row = self.db.fetchone("""
            SELECT * FROM messages WHERE id = ?
        """, (message_id,))

        if not row:
            return None

        msg = self._dict_from_row(row)

        # Parse sources JSON
        if msg.get("sources"):
            try:
                msg["sources"] = json.loads(msg["sources"])
            except:
                msg["sources"] = None

        return msg

    def delete_by_chat_id(self, chat_id: str) -> int:
        """
        Delete all messages for a chat.

        Args:
            chat_id: Chat ID

        Returns:
            Number of messages deleted
        """
        result = self.db.execute("DELETE FROM messages WHERE chat_id = ?", (chat_id,))
        self.db.commit()
        return result.rowcount
