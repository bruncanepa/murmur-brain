from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import tempfile
import shutil
from typing import Optional
import os
import webbrowser
import threading

from services.database import get_database
from services.file_processor import FileProcessor
from services.ollama_service import get_ollama_service
from services.vector_search import get_vector_search

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


@app.post("/api/search")
async def search_vectors(
    query: str,
    top_k: int = 5,
    threshold: float = 0.0,
    doc_ids: Optional[list[str]] = None
):
    """
    Perform semantic search over document chunks

    Args:
        query: Search query text
        top_k: Number of top results to return (default: 5)
        threshold: Minimum similarity score 0-1 (default: 0.0)
        doc_ids: Optional list of document IDs to filter by

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

        result = vector_search.search(
            query=query.strip(),
            top_k=top_k,
            threshold=threshold,
            doc_ids=doc_ids
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
