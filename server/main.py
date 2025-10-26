from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import tempfile
import shutil
from typing import Optional
import os
import webbrowser
import threading
import json
import asyncio

from services.database import get_database
from services.file_processor import FileProcessor
from services.ollama_service import get_ollama_service
from services.vector_search import get_vector_search
from services.chat_service import get_chat_service
from services.ollama_checker import get_ollama_checker

app = FastAPI(title="Local Brain API", version="1.0.0")

# CORS middleware for web client
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow web app origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
db = get_database()
file_processor = FileProcessor()
ollama_service = get_ollama_service()
vector_search = get_vector_search()
chat_service = get_chat_service()
ollama_checker = get_ollama_checker()


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    print("Starting Local Brain server...")
    print(f"Database: {db.db_path}")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    print("Shutting down Local Brain server...")
    db.close()


@app.get("/api/health")
async def health_check():
    """Detailed health check"""
    try:
        stats = db.get_stats()
        return {
            "status": "healthy",
            "database": "connected",
            "stats": stats.get("stats", {})
        }
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "error": str(e)}
        )


@app.get("/api/ollama/status")
async def get_ollama_status():
    """Check Ollama installation and running status"""
    try:
        status = ollama_checker.get_status()
        return {
            "success": True,
            **status
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )


@app.get("/api/ollama/library/search")
async def search_ollama_library(q: str = "", category: str = None):
    """Search Ollama library for available models"""
    try:
        from services.ollama_library_scraper import get_scraper

        scraper = get_scraper()
        results = scraper.search_models(query=q, category=category)

        return {
            "success": True,
            "models": results,
            "count": len(results)
        }
    except Exception as e:
        logger.error(f"Error searching Ollama library: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )


@app.get("/api/ollama/library/categories")
async def get_ollama_categories():
    """Get list of model categories"""
    try:
        from services.ollama_library_scraper import get_scraper

        scraper = get_scraper()
        categories = scraper.get_categories()

        return {
            "success": True,
            "categories": categories
        }
    except Exception as e:
        logger.error(f"Error getting categories: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )


@app.post("/api/documents/process")
async def process_document(file: UploadFile = File(...)):
    """
    Process an uploaded document (PDF, CSV, TXT)
    Extracts text, creates chunks, and stores in database
    """
    try:
        # Validate file type
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in ['.pdf', '.csv', '.txt']:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: {file_ext}. Supported: PDF, CSV, TXT"
            )

        # Create temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as temp_file:
            temp_path = temp_file.name
            shutil.copyfileobj(file.file, temp_file)

        try:
            # Validate file
            validation = file_processor.validate_file(temp_path)
            if not validation["valid"]:
                raise HTTPException(status_code=400, detail=validation["error"])

            # Process file based on type
            if file_ext == '.pdf':
                result = file_processor.process_pdf_streaming(temp_path)
            elif file_ext == '.csv':
                result = file_processor.process_csv(temp_path)
            elif file_ext == '.txt':
                result = file_processor.process_text(temp_path)
            else:
                raise HTTPException(status_code=400, detail="Unsupported file type")

            # Generate embeddings for chunks
            print(f"Generating embeddings for {len(result['chunks'])} chunks...")
            chunk_texts = [chunk["text"] for chunk in result["chunks"]]
            embeddings = ollama_service.generate_embeddings_batch(chunk_texts, batch_size=10)

            # Attach embeddings to chunks
            for i, chunk in enumerate(result["chunks"]):
                chunk["embedding"] = embeddings[i] if i < len(embeddings) else []

            print(f"Embeddings generated successfully. Non-empty: {len([e for e in embeddings if e])}")

            # Save document to database
            doc_result = db.add_document({
                "fileName": file.filename,
                "filePath": temp_path,
                "fileType": file_ext,
                "fileSize": validation["size"],
                "chunkCount": len(result["chunks"])
            })

            if not doc_result["success"]:
                raise HTTPException(status_code=500, detail="Failed to save document")

            document_id = doc_result["documentId"]

            # Save chunks to database
            vectors_result = db.add_vectors(document_id, result["chunks"])

            if not vectors_result["success"]:
                # Cleanup: delete document if vectors failed
                db.delete_document(document_id)
                raise HTTPException(status_code=500, detail="Failed to save document chunks")

            # Update document status
            db.update_document_status(document_id, "completed")

            return {
                "success": True,
                "documentId": document_id,
                "metadata": {
                    "fileName": file.filename,
                    "fileType": file_ext,
                    "fileSize": validation["size"],
                    **result["metadata"]
                },
                "chunkCount": len(result["chunks"])
            }

        finally:
            # Cleanup temp file
            Path(temp_path).unlink(missing_ok=True)

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error processing document: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/documents/process-stream")
async def process_document_stream(file: UploadFile = File(...)):
    """
    Process an uploaded document with real-time progress streaming via SSE
    Extracts text, creates chunks, and stores in database while reporting progress
    """
    # Read file contents immediately before the generator starts
    file_contents = await file.read()
    filename = file.filename

    async def generate_progress_events():
        """Generator that yields Server-Sent Events for progress updates"""
        temp_path = None

        try:
            # Helper to send progress event
            def send_progress(phase: str, progress: int, message: str, details: dict = None):
                event_data = {
                    "phase": phase,
                    "progress": progress,
                    "message": message
                }
                if details:
                    event_data["details"] = details
                return f"data: {json.dumps(event_data)}\n\n"

            # Validate file type
            file_ext = Path(filename).suffix.lower()
            if file_ext not in ['.pdf', '.csv', '.txt']:
                yield send_progress("error", 0, f"Unsupported file type: {file_ext}",
                                  {"error": "Supported: PDF, CSV, TXT"})
                return

            # Phase 1: Upload (1-5%)
            yield send_progress("upload", 5, f"Uploading {filename}...")

            # Create temp file with the contents we already read
            with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as temp_file:
                temp_path = temp_file.name
                temp_file.write(file_contents)

            # Phase 2: Validation (5-10%)
            yield send_progress("validation", 10, "Validating file...")
            validation = file_processor.validate_file(temp_path)
            if not validation["valid"]:
                yield send_progress("error", 10, validation["error"])
                return

            # Phase 3: Text Extraction (10-30%)
            yield send_progress("extraction", 15, f"Extracting text from {file_ext.upper()}...")

            if file_ext == '.pdf':
                result = file_processor.process_pdf_streaming(temp_path)
            elif file_ext == '.csv':
                result = file_processor.process_csv(temp_path)
            elif file_ext == '.txt':
                result = file_processor.process_text(temp_path)
            else:
                yield send_progress("error", 15, "Unsupported file type")
                return

            chunk_count = len(result['chunks'])
            yield send_progress("extraction", 30, f"Extracted {chunk_count} chunks",
                              {"chunks": chunk_count})

            # Phase 4: Embedding Generation (30-85%)
            yield send_progress("embedding", 30, f"Generating embeddings for {chunk_count} chunks...")

            chunk_texts = [chunk["text"] for chunk in result["chunks"]]
            embeddings = []
            batch_size = 10
            total_batches = (chunk_count + batch_size - 1) // batch_size

            for i in range(0, chunk_count, batch_size):
                batch = chunk_texts[i:i + batch_size]
                batch_num = i // batch_size + 1
                batch_end = min(i + batch_size, chunk_count)

                # Calculate progress: 30% to 85% (55% range for embedding)
                embedding_progress = 30 + int((i / chunk_count) * 55)
                yield send_progress("embedding", embedding_progress,
                                  f"Processing batch {batch_num}/{total_batches} (chunks {i + 1}-{batch_end})",
                                  {"batch": batch_num, "totalBatches": total_batches})

                # Generate embeddings for this batch
                for text in batch:
                    try:
                        embedding = ollama_service.generate_embedding(text)
                        embeddings.append(embedding)
                        await asyncio.sleep(0.1)  # Small delay
                    except Exception as e:
                        print(f"Error generating embedding: {e}")
                        embeddings.append([])

            yield send_progress("embedding", 85, f"Generated {len([e for e in embeddings if e])} embeddings")

            # Attach embeddings to chunks
            for i, chunk in enumerate(result["chunks"]):
                chunk["embedding"] = embeddings[i] if i < len(embeddings) else []

            # Phase 5: Database Storage (85-95%)
            yield send_progress("storage", 85, "Saving document to database...")

            doc_result = db.add_document({
                "fileName": filename,
                "filePath": temp_path,
                "fileType": file_ext,
                "fileSize": validation["size"],
                "chunkCount": chunk_count
            })

            if not doc_result["success"]:
                yield send_progress("error", 85, "Failed to save document",
                                  {"error": doc_result.get("error", "Unknown error")})
                return

            document_id = doc_result["documentId"]

            yield send_progress("storage", 90, "Saving chunks and vectors...")

            # Save chunks to database
            vectors_result = db.add_vectors(document_id, result["chunks"])

            if not vectors_result["success"]:
                db.delete_document(document_id)
                yield send_progress("error", 90, "Failed to save document chunks",
                                  {"error": vectors_result.get("error", "Unknown error")})
                return

            # Update document status
            db.update_document_status(document_id, "completed")

            # Phase 6: Complete (100%)
            yield send_progress("complete", 100, "Document processed successfully!", {
                "documentId": document_id,
                "fileName": filename,
                "fileType": file_ext,
                "fileSize": validation["size"],
                "chunkCount": chunk_count,
                "characterCount": result["metadata"].get("characterCount", 0),
                "wordCount": result["metadata"].get("wordCount", 0)
            })

        except Exception as e:
            error_msg = str(e)
            print(f"Error processing document: {error_msg}")
            yield f"data: {json.dumps({'phase': 'error', 'progress': 0, 'message': error_msg})}\n\n"

        finally:
            # Cleanup temp file
            if temp_path:
                Path(temp_path).unlink(missing_ok=True)

    return StreamingResponse(
        generate_progress_events(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no"  # Disable buffering in nginx
        }
    )


@app.get("/api/documents")
async def get_documents():
    """Get all documents"""
    try:
        result = db.get_documents()
        if result["success"]:
            return {"success": True, "documents": result["documents"]}
        else:
            raise HTTPException(status_code=500, detail=result.get("error", "Failed to get documents"))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/documents/{doc_id}")
async def get_document(doc_id: str):
    """Get a specific document by ID"""
    try:
        result = db.get_document(doc_id)
        if result["success"]:
            return {"success": True, "document": result["document"]}
        else:
            raise HTTPException(status_code=404, detail="Document not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/documents/{doc_id}")
async def delete_document(doc_id: str):
    """Delete a document and its chunks"""
    try:
        result = db.delete_document(doc_id)
        if result["success"]:
            return {"success": True, "message": "Document deleted"}
        else:
            raise HTTPException(status_code=500, detail=result.get("error", "Failed to delete document"))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/stats")
async def get_stats():
    """Get database statistics"""
    try:
        result = db.get_stats()
        if result["success"]:
            return {"success": True, "stats": result["stats"]}
        else:
            raise HTTPException(status_code=500, detail=result.get("error", "Failed to get stats"))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/search")
async def search_vectors(
    query: str,
    top_k: int = 5,
    threshold: float = 0.0,
    doc_ids: Optional[str] = None
):
    """
    Perform semantic search over document chunks

    Args:
        query: Search query text
        top_k: Number of top results to return (default: 5)
        threshold: Minimum similarity score 0-1 (default: 0.0)
        doc_ids: Optional comma-separated list of document IDs to filter by

    Returns:
        Search results with similarity scores and document metadata
    """
    try:
        if not query or not query.strip():
            raise HTTPException(status_code=400, detail="Query cannot be empty")

        if top_k < 1 or top_k > 100:
            raise HTTPException(status_code=400, detail="top_k must be between 1 and 100")

        if threshold < 0.0 or threshold > 1.0:
            raise HTTPException(status_code=400, detail="threshold must be between 0.0 and 1.0")

        # Parse doc_ids from comma-separated string to list
        parsed_doc_ids = None
        if doc_ids:
            parsed_doc_ids = [id.strip() for id in doc_ids.split(',') if id.strip()]

        result = vector_search.search(
            query=query.strip(),
            top_k=top_k,
            threshold=threshold,
            doc_ids=parsed_doc_ids
        )

        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=500, detail=result.get("error", "Search failed"))

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in search endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============ Chat Endpoints ============

@app.post("/api/chats")
async def create_chat(request: dict):
    """
    Create a new chat session

    Args:
        request: JSON body with optional:
            - title: Chat title
            - doc_ids: List of document IDs to link

    Returns:
        Chat ID and success status
    """
    try:
        title = request.get("title")
        doc_ids = request.get("doc_ids", [])

        # Create chat
        result = db.create_chat(title)
        if not result["success"]:
            raise HTTPException(status_code=500, detail=result.get("error", "Failed to create chat"))

        chat_id = result["chatId"]

        # Link documents if provided
        for doc_id in doc_ids:
            db.link_document_to_chat(chat_id, doc_id)

        return {
            "success": True,
            "chatId": chat_id
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error creating chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/chats")
async def get_chats():
    """Get all chats with metadata"""
    try:
        result = db.get_chats()
        if result["success"]:
            return {"success": True, "chats": result["chats"]}
        else:
            raise HTTPException(status_code=500, detail=result.get("error", "Failed to get chats"))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/chats/{chat_id}")
async def get_chat(chat_id: str):
    """Get a specific chat with its messages"""
    try:
        result = db.get_chat(chat_id)
        if result["success"]:
            return {
                "success": True,
                "chat": result["chat"],
                "messages": result["messages"]
            }
        else:
            raise HTTPException(status_code=404, detail="Chat not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/chats/{chat_id}")
async def delete_chat(chat_id: str):
    """Delete a chat and all its messages"""
    try:
        result = db.delete_chat(chat_id)
        if result["success"]:
            return {"success": True, "message": "Chat deleted"}
        else:
            raise HTTPException(status_code=500, detail=result.get("error", "Failed to delete chat"))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/chats/{chat_id}/messages")
async def send_message(chat_id: str, request: dict):
    """
    Send a message and get RAG response

    Args:
        chat_id: Chat ID
        request: JSON body with:
            - message: User's message
            - model: Ollama model to use (default: llama3.2)

    Returns:
        Assistant's response with sources
    """
    try:
        message = request.get("message", "")
        model = request.get("model", "llama3.2")

        if not message or not message.strip():
            raise HTTPException(status_code=400, detail="Message cannot be empty")

        # Generate RAG response
        result = chat_service.generate_response(chat_id, message.strip(), model)

        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=500, detail=result.get("error", "Failed to generate response"))

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error sending message: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/chats/{chat_id}/documents")
async def link_document(chat_id: str, request: dict):
    """
    Link a document to a chat

    Args:
        chat_id: Chat ID
        request: JSON body with:
            - doc_id: Document ID to link

    Returns:
        Success status
    """
    try:
        doc_id = request.get("doc_id")
        if not doc_id:
            raise HTTPException(status_code=400, detail="doc_id is required")

        result = db.link_document_to_chat(chat_id, doc_id)
        if result["success"]:
            return {"success": True, "message": "Document linked"}
        else:
            raise HTTPException(status_code=500, detail=result.get("error", "Failed to link document"))

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/chats/{chat_id}/documents/{doc_id}")
async def unlink_document(chat_id: str, doc_id: str):
    """Unlink a document from a chat"""
    try:
        result = db.unlink_document_from_chat(chat_id, doc_id)
        if result["success"]:
            return {"success": True, "message": "Document unlinked"}
        else:
            raise HTTPException(status_code=500, detail=result.get("error", "Failed to unlink document"))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/chats/{chat_id}/documents")
async def get_chat_documents(chat_id: str):
    """Get all documents linked to a chat"""
    try:
        result = db.get_chat_documents(chat_id)
        if result["success"]:
            return {"success": True, "documents": result["documents"]}
        else:
            raise HTTPException(status_code=500, detail=result.get("error", "Failed to get documents"))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/chat/models")
async def get_chat_models():
    """Get available chat models from Ollama"""
    try:
        models = ollama_service.list_chat_models()
        return {
            "success": True,
            "models": models
        }
    except Exception as e:
        print(f"Error getting chat models: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.patch("/api/chats/{chat_id}/title")
async def update_chat_title(chat_id: str, request: dict):
    """Update chat title"""
    try:
        title = request.get("title")
        if not title:
            raise HTTPException(status_code=400, detail="title is required")

        result = db.update_chat_title(chat_id, title)
        if result["success"]:
            return {"success": True, "message": "Title updated"}
        else:
            raise HTTPException(status_code=500, detail=result.get("error", "Failed to update title"))

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def find_free_port(start_port=8000):
    """Find a free port starting from start_port"""
    import socket
    port = start_port
    while port < start_port + 100:  # Try up to 100 ports
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('127.0.0.1', port))
                return port
        except OSError:
            port += 1
    raise RuntimeError(f"Could not find a free port in range {start_port}-{start_port + 100}")


def open_browser(port: int):
    """Open the default browser after a delay"""
    import time
    time.sleep(1.5)  # Wait for server to be ready
    url = f"http://127.0.0.1:{port}"
    print(f"\nOpening browser at {url}...")
    try:
        webbrowser.open(url)
    except Exception as e:
        print(f"Could not auto-open browser: {e}")
        print(f"Please manually open: {url}")


if __name__ == "__main__":
    import uvicorn

    # Get port from environment variable or find a free one
    port = int(os.environ.get('API_PORT', 0))
    if port == 0:
        port = find_free_port(8000)

    # Setup static files serving for production build
    dist_path = Path(__file__).parent.parent / "dist"
    if dist_path.exists():
        print(f"Serving static files from: {dist_path}")

        # Mount static files - API routes take precedence
        app.mount("/assets", StaticFiles(directory=str(dist_path / "assets")), name="assets")

        # Serve index.html for all non-API routes
        from fastapi.responses import FileResponse

        @app.get("/{full_path:path}")
        async def serve_frontend(full_path: str):
            """Serve the React app for all non-API routes"""
            if full_path.startswith("api/"):
                raise HTTPException(status_code=404, detail="API endpoint not found")

            # Serve index.html for all frontend routes
            index_path = dist_path / "index.html"
            if index_path.exists():
                return FileResponse(index_path)
            raise HTTPException(status_code=404, detail="Frontend not found")
    else:
        print("Warning: dist folder not found. Run 'npm run build' first.")
        print("Server will only serve API endpoints.")

    print(f"Starting server on http://127.0.0.1:{port}")
    print("Press CTRL+C to quit")

    # Auto-open browser in a separate thread
    browser_thread = threading.Thread(target=open_browser, args=(port,), daemon=True)
    browser_thread.start()

    uvicorn.run(app, host="127.0.0.1", port=port)
