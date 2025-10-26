# Murmur Brain

**Chat with your library using AI - no Internet, no third parties, just you and your documents.**

A privacy-first, local AI application powered by Ollama. Upload your PDFs, books, and documents, then chat with them using AI - completely private, completely offline, running entirely on your machine.

## Project Status

✅ **Complete and Ready for Distribution**

## Features

- ✅ Upload and process CSV, PDF, and TXT files
- ✅ Store documents in a local SQLite vector database
- ✅ Semantic search across all your documents
- ✅ In-app Ollama model management and downloading
- ✅ Modern, responsive web interface
- ✅ Runs entirely locally with no cloud dependencies
- ✅ Cross-platform support (macOS, Windows, Linux)
- ✅ Auto-opens in your default browser
- ⏳ Interactive chat interface (coming soon)

## Technology Stack

### Backend

- **Python 3.8+** - Core application server
- **FastAPI** - Modern REST API framework
- **Uvicorn** - ASGI server
- **SQLite** - Local document and vector storage

### Frontend

- **React** - UI framework
- **Vite** - Fast build tool and dev server
- **Axios** - HTTP client
- **Tailwind CSS** - Utility-first CSS framework

### AI & RAG

- **Ollama** - Local LLM runtime
- **PyPDF2** - PDF text extraction
- **tiktoken** - Text tokenization and chunking

### Distribution

- **PyInstaller** - Cross-platform executable packaging

## Architecture

Murmur Brain uses a modern web-based architecture:

- **Python Backend (FastAPI)**: Serves the React app as static files and provides REST APIs
- **React Frontend**: Modern web interface with TailwindCSS
- **Ollama**: Local AI service for embeddings and generation
- **SQLite**: Local vector database for document storage

When you run the application, it starts a Python server that automatically opens your default browser to the app.

## Quick Start

### Prerequisites

1. **Ollama** - Download and install from [ollama.ai](https://ollama.ai/)
2. **Python 3.8+** - Required for the backend
3. **Node.js 18+** - Required for building the frontend

### For End Users (Prebuilt Executable)

1. Download the executable for your platform:
   - **macOS**: `MurmurBrain.app`
   - **Windows**: `MurmurBrain.exe`
   - **Linux**: `MurmurBrain`

2. Make sure Ollama is running:

   ```bash
   ollama serve
   ```

3. Double-click the executable - it will auto-open in your browser!

4. Download required AI models (if you haven't already):
   - Use the Model Manager tab in the app, or
   - Via command line:
     ```bash
     ollama pull nomic-embed-text  # Required for embeddings
     ollama pull llama3.2           # Optional for chat
     ```

### For Developers

#### Setup

```bash
# Clone the repository
git clone https://github.com/bruncanepa/murmur-brain.git
cd murmur-brain

# Install Node dependencies
npm install

# Install Python dependencies
cd server
pip3 install -r requirements.txt
cd ..
```

#### Development Mode

```bash
# Terminal 1: Start Python backend
cd server && python3 main.py

# Terminal 2: Start Vite dev server (with hot reload)
npm run dev
```

Then open http://localhost:5173 in your browser.

#### Build for Distribution

```bash
# Build everything (React + Executable)
./build.sh  # macOS/Linux
# or
build.bat   # Windows
```

Output will be in `dist/MurmurBrain` (or `MurmurBrain.app` on macOS)

## How It Works

1. **Start**: Run the executable (or `python3 server/main.py` in development)
2. **Server Launches**: Python FastAPI server starts on an available port
3. **Browser Opens**: Your default browser automatically opens to the app
4. **Upload Documents**: Drag and drop PDF, CSV, or TXT files
5. **Processing**: Documents are chunked and embedded using Ollama
6. **Search**: Perform semantic search across all your documents
7. **Manage Models**: Download and manage Ollama AI models

## Features in Detail

### Document Upload

- Supports PDF, CSV, and TXT files
- Drag-and-drop interface
- Progress tracking
- Automatic text extraction and chunking

### Semantic Search

- Vector similarity search using embeddings
- Configurable result count (top-k)
- Adjustable similarity threshold
- Results show similarity scores and source documents

### Model Management

- Browse available Ollama models
- Download models with progress tracking
- View installed models
- Delete unwanted models
- Automatic status checking

## Documentation

- **[BUILD.md](BUILD.md)** - Comprehensive build and distribution guide
- **[MIGRATION_SUMMARY.md](MIGRATION_SUMMARY.md)** - Architecture migration details
- **[START_GUIDE.md](START_GUIDE.md)** - Getting started guide

## Troubleshooting

### "Ollama not running"

- Start Ollama: `ollama serve`
- Or launch the Ollama desktop app
- Check it's running at http://127.0.0.1:11434

### "Browser doesn't open automatically"

- Manually navigate to the URL shown in the console
- Example: http://127.0.0.1:8000

### "Port already in use"

- The server automatically finds an available port
- Check the console output for the actual port being used

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT

## Author

To be filled
