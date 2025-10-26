"""
Chat service with RAG functionality.

Handles chat operations and RAG-based response generation.
"""
from typing import List, Dict, Optional, Tuple
from .chats_model import ChatRepository, ChatResponse, ChatWithMessages
from modules.messages.messages_model import MessageRepository
from modules.search.search_service import SearchService
from core.ollama_client import OllamaClient
from core.config import get_settings


class ChatService:
    """Service for chat operations with RAG support."""

    def __init__(
        self,
        chat_repo: ChatRepository,
        message_repo: MessageRepository,
        search_service: SearchService,
        ollama_client: OllamaClient
    ):
        self.chat_repo = chat_repo
        self.message_repo = message_repo
        self.search_service = search_service
        self.ollama = ollama_client
        self.settings = get_settings()

    def create_chat(self, title: Optional[str] = None, doc_ids: List[str] = None) -> str:
        """
        Create a new chat session.

        Args:
            title: Optional chat title
            doc_ids: Optional list of document IDs to link

        Returns:
            Chat ID
        """
        chat_id = self.chat_repo.create(title)

        # Link documents if provided
        if doc_ids:
            for doc_id in doc_ids:
                try:
                    self.chat_repo.link_document(chat_id, doc_id)
                except Exception as e:
                    print(f"Warning: Failed to link document {doc_id}: {e}")

        return chat_id

    def get_chat(self, chat_id: str) -> Optional[ChatWithMessages]:
        """Get chat by ID with its messages."""
        chat = self.chat_repo.get_by_id(chat_id)
        if not chat:
            return None

        messages = self.message_repo.get_by_chat_id(chat_id)

        return ChatWithMessages(**chat, messages=messages)

    def get_all_chats(self) -> List[ChatResponse]:
        """Get all chats."""
        chats = self.chat_repo.get_all()
        return [ChatResponse(**chat) for chat in chats]

    def delete_chat(self, chat_id: str) -> bool:
        """Delete chat and all its messages."""
        return self.chat_repo.delete(chat_id)

    def update_chat_title(self, chat_id: str, title: str) -> bool:
        """Update chat title."""
        try:
            self.chat_repo.update_title(chat_id, title)
            return True
        except Exception as e:
            print(f"Error updating chat title: {e}")
            return False

    def link_document(self, chat_id: str, doc_id: str) -> bool:
        """Link a document to a chat."""
        try:
            return self.chat_repo.link_document(chat_id, doc_id)
        except ValueError as e:
            raise e
        except Exception as e:
            print(f"Error linking document: {e}")
            return False

    def unlink_document(self, chat_id: str, doc_id: str) -> bool:
        """Unlink a document from a chat."""
        try:
            return self.chat_repo.unlink_document(chat_id, doc_id)
        except ValueError as e:
            raise e
        except Exception as e:
            print(f"Error unlinking document: {e}")
            return False

    def get_chat_documents(self, chat_id: str) -> List[Dict]:
        """Get all documents linked to a chat."""
        try:
            return self.chat_repo.get_chat_documents(chat_id)
        except ValueError as e:
            raise e

    def build_rag_context(
        self,
        query: str,
        chat_id: str,
        top_k: int = None
    ) -> Tuple[str, List[Dict]]:
        """
        Build RAG context by retrieving relevant document chunks.

        Args:
            query: User's question
            chat_id: Chat ID to filter documents
            top_k: Number of chunks to return (default from config)

        Returns:
            Tuple of (formatted_context_string, sources_list)
        """
        if top_k is None:
            top_k = self.settings.rag_context_limit

        # Get linked documents for this chat
        try:
            documents = self.chat_repo.get_chat_documents(chat_id)
        except ValueError:
            return "", []

        if not documents:
            return "", []

        doc_ids = [doc["id"] for doc in documents]

        # Retrieve top-10 candidates with higher threshold
        try:
            search_result = self.search_service.search(
                query=query,
                top_k=10,  # Retrieve more candidates
                threshold=0.5,  # Higher threshold for better quality
                doc_ids=doc_ids
            )
        except Exception as e:
            print(f"Error during RAG search: {e}")
            return "", []

        if not search_result.success or not search_result.results:
            return "", []

        # Take only top_k after re-ranking
        top_results = search_result.results[:top_k]

        if not top_results:
            return "", []

        # Build context string and sources list
        context_parts = []
        sources = []

        for idx, result in enumerate(top_results, 1):
            # Add to context with metadata
            doc_name = result.document["file_name"]
            chunk_text = result.chunk_text
            similarity = result.similarity

            # Enhanced context format with metadata
            context_parts.append(
                f"[Source {idx}: {doc_name} (Relevance: {similarity:.1%})]\n{chunk_text}\n"
            )

            # Track source for citation
            sources.append({
                "doc_id": result.doc_id,
                "vector_id": result.vector_id,
                "file_name": doc_name,
                "chunk_index": result.chunk_index,
                "similarity": result.similarity,
                "chunk_text": chunk_text[:200] + "..." if len(chunk_text) > 200 else chunk_text
            })

        context_string = "\n".join(context_parts)

        # Log retrieval quality
        avg_similarity = sum(r.similarity for r in top_results) / len(top_results)
        print(f"RAG Context: Retrieved {len(top_results)} chunks, "
              f"avg similarity: {avg_similarity:.2%}")

        return context_string, sources

    def build_prompt(
        self,
        context: str,
        user_message: str,
        conversation_history: List[Dict]
    ) -> List[Dict]:
        """
        Build prompt messages for Ollama chat API.

        Args:
            context: RAG context from document chunks
            user_message: Current user message
            conversation_history: Previous messages in the conversation

        Returns:
            List of message dicts for Ollama API
        """
        messages = []

        # System message with instructions
        system_prompt = """You are a knowledgeable AI assistant specializing in answering questions based on provided document context.

INSTRUCTIONS:
1. **Analyze the Context**: Carefully read all provided source materials with their relevance scores
2. **Answer Accuracy**: Base your answer STRICTLY on the provided context - do not add external knowledge
3. **Handle Uncertainty**: If the context lacks sufficient information, explicitly state: "Based on the provided documents, I don't have enough information to answer this fully"
4. **Cite Sources**: Reference specific sources (e.g., "According to Source 1...") when making claims
5. **Synthesize Information**: If multiple sources discuss the topic, synthesize them into a coherent answer
6. **Identify Conflicts**: If sources contradict each other, acknowledge this: "Source 1 suggests X, while Source 2 indicates Y"

RESPONSE FORMAT:
- Start with a direct answer to the question
- Support claims with specific source citations
- Use clear, structured formatting (bullet points, paragraphs as appropriate)
- Be concise but complete - avoid unnecessary elaboration

QUALITY STANDARDS:
- Prioritize information from higher relevance sources
- Distinguish between facts from the documents and your interpretation
- If asked about something not in the context, state this clearly
- Maintain professional, informative tone"""

        messages.append({
            "role": "system",
            "content": system_prompt
        })

        # Add recent conversation history (last 10 messages)
        if conversation_history:
            recent_history = conversation_history[-10:]
            for msg in recent_history:
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })

        # Add current user message with context
        user_prompt = f"""Context from documents:

{context}

---

Question: {user_message}

Please answer based on the context provided above."""

        messages.append({
            "role": "user",
            "content": user_prompt
        })

        return messages

    def generate_response(
        self,
        chat_id: str,
        user_message: str,
        model: str = None
    ) -> Dict:
        """
        Generate RAG response for a user message.

        Args:
            chat_id: Chat ID
            user_message: User's message
            model: Ollama model to use (default from config)

        Returns:
            Dict with success status, response, and sources
        """
        if model is None:
            model = self.settings.ollama_default_chat_model

        try:
            # Get conversation history
            conversation_history = self.message_repo.get_by_chat_id(chat_id)

            # Build RAG context
            context, sources = self.build_rag_context(user_message, chat_id)

            if not context:
                return {
                    "success": False,
                    "error": "No relevant information found in linked documents. "
                            "Please ensure documents are linked to this chat."
                }

            # Build prompt with conversation history
            messages = self.build_prompt(context, user_message, conversation_history)

            # Generate response using Ollama
            response = self.ollama.generate_chat_response(messages, model)

            if not response:
                return {
                    "success": False,
                    "error": "Failed to generate response from Ollama"
                }

            # Save user message
            self.message_repo.create(chat_id, "user", user_message)

            # Save assistant response with sources
            self.message_repo.create(chat_id, "assistant", response, sources, model)

            # If this is the first message, use it as the chat title (truncated)
            if len(conversation_history) == 0 and self.settings.chat_title_generation:
                title = user_message.strip()
                if len(title) > 50:
                    title = title[:47] + '...'
                self.chat_repo.update_title(chat_id, title)

            return {
                "success": True,
                "response": response,
                "sources": sources,
                "model": model
            }

        except Exception as e:
            print(f"Error generating chat response: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e)
            }
