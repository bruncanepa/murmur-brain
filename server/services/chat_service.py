from typing import List, Dict, Optional
from services.database import get_database
from services.ollama_service import get_ollama_service
from services.vector_search import get_vector_search


class ChatService:
    """Service for RAG-based chat functionality"""

    def __init__(self):
        self.db = get_database()
        self.ollama = get_ollama_service()
        self.vector_search = get_vector_search()

    def generate_chat_title(self, first_message: str) -> str:
        """
        Generate a short title from the first message

        Args:
            first_message: The user's first message in the chat

        Returns:
            A short title (max 50 chars)
        """
        # Simple title generation: use first 50 chars or first sentence
        title = first_message.strip()

        # Take first sentence if available
        if '?' in title:
            title = title.split('?')[0] + '?'
        elif '.' in title:
            title = title.split('.')[0] + '.'

        # Limit to 50 characters
        if len(title) > 50:
            title = title[:47] + '...'

        return title

    def build_rag_context(self, query: str, chat_id: str, top_k: int = 5) -> tuple[str, List[Dict]]:
        """
        Build RAG context by retrieving relevant document chunks

        Args:
            query: User's question
            chat_id: Chat ID to filter documents
            top_k: Number of chunks to return (default: 5)

        Returns:
            Tuple of (formatted_context_string, sources_list)
        """
        # Get linked documents for this chat
        docs_result = self.db.get_chat_documents(chat_id)
        if not docs_result["success"] or not docs_result["documents"]:
            return "", []

        doc_ids = [doc["id"] for doc in docs_result["documents"]]

        # Retrieve top-10 candidates with higher threshold
        search_result = self.vector_search.search(
            query=query,
            top_k=10,  # Retrieve more candidates
            threshold=0.5,  # Higher threshold for better quality
            doc_ids=doc_ids
        )

        if not search_result["success"] or not search_result["results"]:
            return "", []

        # Re-rank and select top-k results
        # Sort by similarity score (already sorted, but ensure it)
        results = sorted(search_result["results"], key=lambda x: x["similarity"], reverse=True)

        # Take only top_k after re-ranking
        top_results = results[:top_k]

        if not top_results:
            return "", []

        # Build context string and sources list
        context_parts = []
        sources = []

        for idx, result in enumerate(top_results, 1):
            # Add to context with metadata
            doc_name = result["document"]["file_name"]
            chunk_text = result["chunk_text"]
            similarity = result["similarity"]

            # Enhanced context format with metadata
            context_parts.append(
                f"[Source {idx}: {doc_name} (Relevance: {similarity:.1%})]\n{chunk_text}\n"
            )

            # Track source for citation
            sources.append({
                "doc_id": result["doc_id"],
                "vector_id": result["vector_id"],
                "file_name": doc_name,
                "chunk_index": result["chunk_index"],
                "similarity": result["similarity"],
                "chunk_text": chunk_text[:200] + "..." if len(chunk_text) > 200 else chunk_text
            })

        context_string = "\n".join(context_parts)

        # Log retrieval quality
        avg_similarity = sum(r["similarity"] for r in top_results) / len(top_results)
        print(f"RAG Context: Retrieved {len(top_results)} chunks, avg similarity: {avg_similarity:.2%}")

        return context_string, sources

    def build_prompt(self, context: str, user_message: str, conversation_history: List[Dict]) -> List[Dict]:
        """
        Build prompt messages for Ollama chat API

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

        # Add recent conversation history (last 5 exchanges to maintain context)
        if conversation_history:
            recent_history = conversation_history[-10:]  # Last 10 messages (5 exchanges)
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

    def generate_response(self, chat_id: str, user_message: str, model: str = "llama3.2") -> Dict:
        """
        Generate RAG response for a user message

        Args:
            chat_id: Chat ID
            user_message: User's message
            model: Ollama model to use

        Returns:
            Dict with success status, response, and sources
        """
        try:
            # Get conversation history
            messages_result = self.db.get_messages(chat_id)
            if not messages_result["success"]:
                return {
                    "success": False,
                    "error": "Failed to load conversation history"
                }

            conversation_history = messages_result["messages"]

            # Build RAG context
            context, sources = self.build_rag_context(user_message, chat_id)

            if not context:
                return {
                    "success": False,
                    "error": "No relevant information found in linked documents. Please ensure documents are linked to this chat."
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
            self.db.add_message(chat_id, "user", user_message)

            # Save assistant response with sources
            self.db.add_message(chat_id, "assistant", response, sources, model)

            # If this is the first message, generate title
            if len(conversation_history) == 0:
                title = self.generate_chat_title(user_message)
                self.db.update_chat_title(chat_id, title)

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


# Singleton instance
_chat_service_instance = None

def get_chat_service() -> ChatService:
    global _chat_service_instance
    if _chat_service_instance is None:
        _chat_service_instance = ChatService()
    return _chat_service_instance
