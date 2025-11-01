"""
Chat API controller.

FastAPI routes for chat management.
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List
from .chats_model import ChatRepository, ChatCreate, ChatResponse, ChatWithMessages, ChatTitleUpdate, DocumentLink
from .chats_service import ChatService
from modules.messages.messages_model import MessageRepository, MessageCreate, ChatMessageResponse
from modules.search.search_model import VectorRepository
from modules.search.search_service import SearchService
from core.dependencies import get_db, get_ollama, get_faiss
from core.database import DatabaseConnection
from core.ollama_client import OllamaClient
from core.faiss_manager import FaissIndexManager


router = APIRouter(prefix="/api/chats", tags=["chats"])


def get_chat_repository(db: DatabaseConnection = Depends(get_db)) -> ChatRepository:
    """Dependency that provides chat repository."""
    return ChatRepository(db)


def get_message_repository(db: DatabaseConnection = Depends(get_db)) -> MessageRepository:
    """Dependency that provides message repository."""
    return MessageRepository(db)


def get_vector_repository(db: DatabaseConnection = Depends(get_db)) -> VectorRepository:
    """Dependency that provides vector repository."""
    return VectorRepository(db)


def get_search_service(
    vector_repo: VectorRepository = Depends(get_vector_repository),
    ollama: OllamaClient = Depends(get_ollama),
    faiss_manager: FaissIndexManager = Depends(get_faiss)
) -> SearchService:
    """Dependency that provides search service."""
    return SearchService(vector_repo, ollama, faiss_manager)


def get_chat_service(
    chat_repo: ChatRepository = Depends(get_chat_repository),
    message_repo: MessageRepository = Depends(get_message_repository),
    search_service: SearchService = Depends(get_search_service),
    ollama: OllamaClient = Depends(get_ollama)
) -> ChatService:
    """Dependency that provides chat service."""
    return ChatService(chat_repo, message_repo, search_service, ollama)


@router.post("", response_model=dict)
async def create_chat(
    request: ChatCreate,
    service: ChatService = Depends(get_chat_service)
):
    """
    Create a new chat session.

    Optionally provide title and document IDs to link.
    """
    try:
        chat_id = service.create_chat(request.title, request.doc_ids)
        return {
            "success": True,
            "chatId": chat_id
        }
    except Exception as e:
        print(f"Error creating chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=dict)
async def get_chats(service: ChatService = Depends(get_chat_service)):
    """Get all chats with metadata."""
    try:
        chats = service.get_all_chats()
        return {
            "success": True,
            "chats": [chat.model_dump() for chat in chats]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{chat_id}", response_model=dict)
async def get_chat(
    chat_id: str,
    service: ChatService = Depends(get_chat_service)
):
    """Get a specific chat with its messages."""
    try:
        chat = service.get_chat(chat_id)
        if chat:
            chat_dict = chat.model_dump()
            return {
                "success": True,
                "chat": {k: v for k, v in chat_dict.items() if k != 'messages'},
                "messages": chat_dict['messages']
            }
        else:
            raise HTTPException(status_code=404, detail="Chat not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{chat_id}", response_model=dict)
async def delete_chat(
    chat_id: str,
    service: ChatService = Depends(get_chat_service)
):
    """Delete a chat and all its messages."""
    try:
        success = service.delete_chat(chat_id)
        if success:
            return {"success": True, "message": "Chat deleted"}
        else:
            raise HTTPException(status_code=404, detail="Chat not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{chat_id}/title", response_model=dict)
async def update_chat_title(
    chat_id: str,
    request: ChatTitleUpdate,
    service: ChatService = Depends(get_chat_service)
):
    """Update chat title."""
    try:
        success = service.update_chat_title(chat_id, request.title)
        if success:
            return {"success": True, "message": "Title updated"}
        else:
            raise HTTPException(status_code=500, detail="Failed to update title")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{chat_id}/messages", response_model=ChatMessageResponse)
async def send_message(
    chat_id: str,
    request: MessageCreate,
    service: ChatService = Depends(get_chat_service)
):
    """
    Send a message and get RAG response.

    The system will retrieve relevant context from linked documents
    and generate a response using the specified model.
    """
    try:
        if not request.message or not request.message.strip():
            raise HTTPException(status_code=400, detail="Message cannot be empty")

        result = service.generate_response(chat_id, request.message.strip(), request.model)

        if result["success"]:
            return ChatMessageResponse(**result)
        else:
            # Check if this is a "no documents" error (user-facing, not server error)
            if result.get("error_type") == "no_documents":
                raise HTTPException(status_code=404, detail=result.get("error", "No relevant information found"))
            else:
                raise HTTPException(status_code=500, detail=result.get("error", "Failed to generate response"))

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error sending message: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{chat_id}/documents", response_model=dict)
async def get_chat_documents(
    chat_id: str,
    service: ChatService = Depends(get_chat_service)
):
    """Get all documents linked to a chat."""
    try:
        documents = service.get_chat_documents(chat_id)
        return {"success": True, "documents": documents}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{chat_id}/documents", response_model=dict)
async def link_document(
    chat_id: str,
    request: DocumentLink,
    service: ChatService = Depends(get_chat_service)
):
    """Link a document to a chat."""
    try:
        success = service.link_document(chat_id, request.doc_id)
        if success:
            return {"success": True, "message": "Document linked"}
        else:
            raise HTTPException(status_code=500, detail="Failed to link document")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{chat_id}/documents/{doc_id}", response_model=dict)
async def unlink_document(
    chat_id: str,
    doc_id: str,
    service: ChatService = Depends(get_chat_service)
):
    """Unlink a document from a chat."""
    try:
        success = service.unlink_document(chat_id, doc_id)
        if success:
            return {"success": True, "message": "Document unlinked"}
        else:
            raise HTTPException(status_code=500, detail="Failed to unlink document")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
