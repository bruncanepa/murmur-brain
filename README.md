# Local Brain - RAG Desktop Application

A cross-platform Electron desktop application that enables local RAG (Retrieval-Augmented Generation) with Ollama.

## Project Status

✅ **Step 1: Project Setup - COMPLETED**

## Features (Planned)

- Upload and process CSV, PDF, and TXT files
- Store documents in a local SQLite vector database
- Interactive chat interface for querying documents
- In-app Ollama model management and downloading
- Runs entirely locally with no cloud dependencies
- Cross-platform support (Linux, Windows, macOS)

## Technology Stack

### Core Framework
- **Electron** - Desktop application framework
- **Vite** - Fast build tool and dev server
- **React** - UI framework

### AI & RAG
- **Ollama** - Local LLM runtime
- **@langchain/community** - RAG pipeline implementation
- **sqlite-vec** - Vector storage and similarity search
- **sqlite3** - Local database

### File Processing
- **pdf-parse** - PDF text extraction
- **csv-parse** - CSV parsing
- **fs** (Node.js) - TXT file reading

### UI & Styling
- **Tailwind CSS v4** - Utility-first CSS framework
- **PostCSS** - CSS processing

### Build Tools
- **electron-builder** - Cross-platform packaging

## Project Structure

```
local-brain/
├── src/
│   ├── main/           # Electron main process
│   │   └── main.js     # Main application entry
│   ├── preload/        # Electron preload scripts
│   │   └── preload.js  # IPC bridge
│   ├── renderer/       # React frontend
│   │   ├── App.jsx     # Main React component
│   │   ├── main.jsx    # React entry point
│   │   ├── App.css     # Component styles
│   │   └── index.css   # Global styles with Tailwind
│   ├── components/     # React components (future)
│   ├── services/       # Business logic (future)
│   └── utils/          # Utility functions (future)
├── resources/
│   └── ollama/         # Ollama binaries (to be added)
├── public/             # Static assets
├── dist/               # Vite build output
└── release/            # Electron build output (future)
```

## Installation

### Prerequisites
- Node.js 18+
- npm 9+

### Setup

1. Clone the repository
2. Install dependencies:
```bash
npm install --legacy-peer-deps
```

## Development

### Run Development Server

**Note:** The dev server is configured but Electron integration needs to be refined. For now, build and test separately:

```bash
# Build the React app
npm run build

# Start Electron (after build)
npm start
```

### Build for Production

```bash
# Build React app
npm run build

# Package Electron app
npm run build:electron
```

## Step 1 Completed Tasks

✅ Project initialization with Electron + Vite + React
✅ All core dependencies installed:
  - Electron & electron-builder
  - React & React DOM
  - Vite & @vitejs/plugin-react
  - Tailwind CSS v4 with PostCSS
  - sqlite3 & sqlite-vec
  - pdf-parse & csv-parse
  - @langchain/community & ollama
  - axios for HTTP requests

✅ Tailwind CSS v4 configured with PostCSS
✅ electron-builder configured for Linux, Windows, and macOS
✅ Project directory structure created
✅ Git repository initialized with comprehensive .gitignore
✅ Build verification completed successfully

## Known Configuration Notes

- Using `--legacy-peer-deps` due to peer dependency conflicts between @langchain/community and pdf-parse versions
- Tailwind CSS v4 requires `@tailwindcss/postcss` plugin instead of direct tailwindcss PostCSS plugin
- Electron main and preload scripts use CommonJS (require/module.exports)
- React app uses ES modules (import/export)
- Config files (.mjs extension) use ES modules

## Next Steps (From Product Memo)

**Step 2: Bundle and Start Ollama**
- Download and bundle Ollama binaries
- Implement Ollama server startup on app launch
- Configure Ollama to run on localhost:11434

**Step 3: Model Management**
- Create React component for model downloading
- Implement model listing and installation UI
- Store models in app user data directory

**Step 4: File Upload Handling**
- Create drag-and-drop file upload component
- Implement IPC communication for file processing
- Parse CSV, PDF, and TXT files

**Step 5+: Continue per product memo...**

## License

MIT

## Author

To be filled
