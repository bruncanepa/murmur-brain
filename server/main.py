"""
Local Brain API - Main application entry point.

A modular FastAPI application for RAG-based document Q&A using local Ollama models.
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
import os
import webbrowser
import threading

# Import module routers
from modules.documents.documents_controller import router as documents_router
from modules.search.search_controller import router as search_router
from modules.chats.chats_controller import router as chats_router
from modules.ollama.ollama_controller import router as ollama_router
from modules.health.health_controller import router as health_router

# Import core services for lifecycle management
from core.database import get_db_connection, close_db_connection
from core.config import get_settings


# Initialize settings
settings = get_settings()

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug
)

# CORS middleware for web client
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    print(f"Starting {settings.app_name} v{settings.app_version}...")

    # Initialize database connection
    db = get_db_connection()
    print(f"Database: {db.db_path}")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    print(f"Shutting down {settings.app_name}...")
    close_db_connection()


# Register module routers
app.include_router(health_router)      # /api/health, /api/stats
app.include_router(documents_router)   # /api/documents/*
app.include_router(search_router)      # /api/search
app.include_router(chats_router)       # /api/chats/*
app.include_router(ollama_router)      # /api/ollama/*

# Legacy endpoint for backwards compatibility
@app.get("/api/chat/models")
async def get_chat_models_legacy():
    """Legacy endpoint - redirects to /api/ollama/chat/models"""
    from modules.ollama.ollama_service import OllamaService
    from core.ollama_client import get_ollama_client

    try:
        service = OllamaService(get_ollama_client())
        models = service.get_chat_models()
        return {
            "success": True,
            "models": models
        }
    except Exception as e:
        print(f"Error getting chat models: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def find_free_port(start_port=8000):
    """Find a free port starting from start_port."""
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
    """Open the default browser after a delay."""
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
        @app.get("/{full_path:path}")
        async def serve_frontend(full_path: str):
            """Serve the React app for all non-API routes."""
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
