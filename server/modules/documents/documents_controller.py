"""
Document API controller.

FastAPI routes for document management.
"""
import json
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import JSONResponse, StreamingResponse
from typing import List
from .documents_model import DocumentRepository, DocumentResponse
from .documents_service import DocumentService
from .documents_processor import FileProcessor
from core.dependencies import get_db, get_ollama, get_faiss
from core.database import DatabaseConnection
from core.ollama_client import OllamaClient
from core.faiss_manager import FaissIndexManager


router = APIRouter(prefix="/api/documents", tags=["documents"])


def get_document_repository(
    db: DatabaseConnection = Depends(get_db),
    faiss_manager: FaissIndexManager = Depends(get_faiss)
) -> DocumentRepository:
    """Dependency that provides document repository."""
    return DocumentRepository(db, faiss_manager)


def get_file_processor() -> FileProcessor:
    """Dependency that provides file processor."""
    return FileProcessor()


def get_document_service(
    doc_repo: DocumentRepository = Depends(get_document_repository),
    ollama: OllamaClient = Depends(get_ollama),
    processor: FileProcessor = Depends(get_file_processor)
) -> DocumentService:
    """Dependency that provides document service."""
    return DocumentService(doc_repo, ollama, processor)


@router.post("/process", response_model=dict)
async def process_document(
    file: UploadFile = File(...),
    service: DocumentService = Depends(get_document_service)
):
    """
    Process an uploaded document (PDF, TXT).
    Extracts text, creates chunks, and stores in database.
    """
    try:
        result = await service.process_document(file)
        return result

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        import traceback
        print(f"Error processing document: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/process-stream")
async def process_document_stream(
    file: UploadFile = File(...),
    service: DocumentService = Depends(get_document_service)
):
    """
    Process an uploaded document with real-time progress streaming via SSE.
    Extracts text, creates chunks, and stores in database while reporting progress.
    """

    # Read file contents before creating generator (while file is still open)
    file_contents = await file.read()
    filename = file.filename

    async def generate_progress_events():
        """Generator that yields Server-Sent Events for progress updates in real-time."""
        import asyncio
        from asyncio import Queue

        def format_event(phase: str, progress: int, message: str, details: dict = None):
            """Format progress data as SSE event."""
            event_data = {
                "phase": phase,
                "progress": progress,
                "message": message
            }
            if details:
                event_data["details"] = details
            return f"data: {json.dumps(event_data)}\n\n"

        try:
            # Create queue for real-time progress events
            queue = Queue()

            async def capture_progress(phase, progress, message, details=None):
                """Callback that queues progress events."""
                await queue.put((phase, progress, message, details))

            # Start document processing in background task
            task = asyncio.create_task(
                service.process_document_stream_bytes(file_contents, filename, progress_callback=capture_progress)
            )

            # Yield progress events in real-time as they arrive
            while not task.done() or not queue.empty():
                try:
                    # Wait for next event with short timeout
                    phase, progress, message, details = await asyncio.wait_for(queue.get(), timeout=0.1)
                    yield format_event(phase, progress, message, details)
                except asyncio.TimeoutError:
                    # No event yet, check if task is done
                    continue

            # Ensure task completes and raise any exceptions
            await task

        except Exception as e:
            import traceback
            error_msg = str(e)
            print(f"Error processing document: {error_msg}")
            traceback.print_exc()
            yield f"data: {json.dumps({'phase': 'error', 'progress': 0, 'message': error_msg})}\n\n"

    return StreamingResponse(
        generate_progress_events(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no"
        }
    )


@router.get("", response_model=dict)
async def get_documents(service: DocumentService = Depends(get_document_service)):
    """Get all documents."""
    try:
        documents = service.get_all_documents()
        return {
            "success": True,
            "documents": [doc.model_dump() for doc in documents]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{doc_id}", response_model=dict)
async def get_document(
    doc_id: str,
    service: DocumentService = Depends(get_document_service)
):
    """Get a specific document by ID."""
    try:
        document = service.get_document(doc_id)
        if document:
            return {
                "success": True,
                "document": document.model_dump()
            }
        else:
            raise HTTPException(status_code=404, detail="Document not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{doc_id}", response_model=dict)
async def delete_document(
    doc_id: str,
    service: DocumentService = Depends(get_document_service)
):
    """Delete a document and its chunks."""
    try:
        success = service.delete_document(doc_id)
        if success:
            return {"success": True, "message": "Document deleted"}
        else:
            raise HTTPException(status_code=404, detail="Document not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
