# Quick Start Guide - Modular Backend

## 🚀 Getting Started

### Start the Server
```bash
cd server
python3 main.py
```

The server will:
- Initialize the database
- Start on http://127.0.0.1:8000 (or next available port)
- Auto-open your browser

## 📁 Project Structure

```
server/
├── main.py                  # App entry point
├── core/                    # Shared infrastructure
│   ├── database.py         # DB connection + BaseRepository
│   ├── config.py           # Settings (Pydantic)
│   ├── ollama_client.py    # Ollama HTTP client
│   └── dependencies.py     # FastAPI DI providers
└── modules/                 # Feature modules
    ├── documents/          # Document management
    ├── search/             # Vector search
    ├── chats/              # Chat + RAG
    ├── messages/           # Messages
    ├── ollama/             # Ollama integration
    └── health/             # Health checks
```

## 🏗️ Module Pattern

Each module follows this structure:

```
modules/my_module/
├── __init__.py
├── model.py        # Pydantic schemas + Repository
├── service.py      # Business logic
└── controller.py   # FastAPI routes (APIRouter)
```

### Layer Responsibilities

| Layer | Purpose | Example |
|-------|---------|---------|
| **Controller** | HTTP concerns, routing | `@router.get("/endpoint")` |
| **Service** | Business logic | `process_document()`, `build_rag_context()` |
| **Model** | Data validation + DB access | `DocumentRepository`, `ChatCreate` schema |

## 🔧 Adding a New Module

### 1. Create Module Directory
```bash
mkdir -p modules/my_feature
touch modules/my_feature/__init__.py
```

### 2. Create Model (`model.py`)
```python
from pydantic import BaseModel
from core.database import BaseRepository, DatabaseConnection

# Pydantic schemas
class MyFeatureCreate(BaseModel):
    name: str
    description: str

class MyFeatureResponse(BaseModel):
    id: str
    name: str
    description: str

# Repository
class MyFeatureRepository(BaseRepository):
    def __init__(self, db: DatabaseConnection):
        super().__init__(db)

    def create(self, feature: MyFeatureCreate) -> str:
        # Database operations
        pass

    def get_by_id(self, feature_id: str) -> dict:
        # Database operations
        pass
```

### 3. Create Service (`service.py`)
```python
from .model import MyFeatureRepository, MyFeatureCreate
from core.ollama_client import OllamaClient

class MyFeatureService:
    def __init__(
        self,
        repo: MyFeatureRepository,
        ollama: OllamaClient
    ):
        self.repo = repo
        self.ollama = ollama

    def create_feature(self, feature: MyFeatureCreate) -> str:
        # Business logic
        feature_id = self.repo.create(feature)
        return feature_id
```

### 4. Create Controller (`controller.py`)
```python
from fastapi import APIRouter, Depends
from .model import MyFeatureRepository, MyFeatureCreate, MyFeatureResponse
from .service import MyFeatureService
from core.dependencies import get_db, get_ollama

router = APIRouter(prefix="/api/my-feature", tags=["my-feature"])

def get_repository(db = Depends(get_db)) -> MyFeatureRepository:
    return MyFeatureRepository(db)

def get_service(
    repo: MyFeatureRepository = Depends(get_repository),
    ollama = Depends(get_ollama)
) -> MyFeatureService:
    return MyFeatureService(repo, ollama)

@router.post("", response_model=dict)
async def create_feature(
    feature: MyFeatureCreate,
    service: MyFeatureService = Depends(get_service)
):
    feature_id = service.create_feature(feature)
    return {"success": True, "id": feature_id}
```

### 5. Register in `main.py`
```python
from modules.my_feature.controller import router as my_feature_router

app.include_router(my_feature_router)
```

## 💉 Dependency Injection

### Available Dependencies

```python
from core.dependencies import get_db, get_ollama, get_config

# In any endpoint
@router.get("/endpoint")
async def endpoint(
    db: DatabaseConnection = Depends(get_db),
    ollama: OllamaClient = Depends(get_ollama),
    config: Settings = Depends(get_config)
):
    # Use dependencies
    pass
```

### Custom Dependencies

```python
# Create a dependency provider
def get_my_service(
    repo: MyRepository = Depends(get_my_repository),
    ollama: OllamaClient = Depends(get_ollama)
) -> MyService:
    return MyService(repo, ollama)

# Use it in routes
@router.post("/endpoint")
async def endpoint(
    service: MyService = Depends(get_my_service)
):
    return service.do_something()
```

## ⚙️ Configuration

### Environment Variables

All settings support environment variables with `LOCAL_BRAIN_` prefix:

```bash
# .env file or export
LOCAL_BRAIN_APP_NAME="My Brain"
LOCAL_BRAIN_PORT=9000
LOCAL_BRAIN_OLLAMA_BASE_URL="http://localhost:11434"
LOCAL_BRAIN_CHUNK_SIZE=2000
LOCAL_BRAIN_CHUNK_OVERLAP=400
```

### Accessing Settings

```python
from core.config import get_settings

settings = get_settings()
print(settings.chunk_size)  # 1500 (or from env)
print(settings.ollama_base_url)  # http://127.0.0.1:11434
```

### Available Settings

| Setting | Default | Description |
|---------|---------|-------------|
| `app_name` | "Murmur Brain" | Application name |
| `app_version` | "1.0.0" | Version |
| `debug` | False | Debug mode |
| `host` | "127.0.0.1" | Server host |
| `port` | 8000 | Server port |
| `ollama_base_url` | "http://127.0.0.1:11434" | Ollama URL |
| `ollama_embedding_model` | "nomic-embed-text" | Embedding model |
| `ollama_default_chat_model` | "llama3.2" | Default chat model |
| `chunk_size` | 1500 | Document chunk size |
| `chunk_overlap` | 300 | Chunk overlap |
| `max_file_size` | 52428800 | Max upload (50MB) |

## 🗄️ Database Operations

### Using Repository Pattern

```python
from modules.documents.model import DocumentRepository
from core.dependencies import get_db

# In a service or endpoint
@router.get("/documents")
async def get_documents(
    doc_repo: DocumentRepository = Depends(get_document_repository)
):
    documents = doc_repo.get_all()
    return {"documents": documents}
```

### Creating a Repository

```python
from core.database import BaseRepository

class MyRepository(BaseRepository):
    def create(self, data: dict) -> str:
        doc_id = str(uuid.uuid4())
        self.db.execute("""
            INSERT INTO my_table (id, name) VALUES (?, ?)
        """, (doc_id, data["name"]))
        self.db.commit()
        return doc_id

    def get_by_id(self, id: str) -> Optional[dict]:
        row = self.db.fetchone("""
            SELECT * FROM my_table WHERE id = ?
        """, (id,))
        return self._dict_from_row(row)
```

## 🧪 Testing (Future)

### Unit Tests

```python
from modules.documents.service import DocumentService
from unittest.mock import Mock

def test_document_service():
    # Mock dependencies
    mock_repo = Mock()
    mock_ollama = Mock()
    mock_processor = Mock()

    # Create service with mocks
    service = DocumentService(mock_repo, mock_ollama, mock_processor)

    # Test methods
    # ...
```

### Integration Tests

```python
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_create_document():
    response = client.post("/api/documents/process", files={"file": ...})
    assert response.status_code == 200
```

## 📚 Common Tasks

### Add New Endpoint
1. Add route in `modules/*/controller.py`
2. Implement logic in `modules/*/service.py`
3. Add database operations in `modules/*/model.py` if needed

### Add New Table
1. Add creation SQL in `Repository.__init__()` or `_ensure_tables()`
2. Add repository methods for CRUD operations
3. Create Pydantic schemas for validation

### Use External Service
1. Create client in `core/` if reusable
2. Add to `dependencies.py` if needed everywhere
3. Or inject directly in service constructor

## 🐛 Debugging

### Enable Debug Mode
```python
# In core/config.py or env
LOCAL_BRAIN_DEBUG=true
```

### Check Logs
```bash
# Server logs show:
- Database initialization
- Route registration
- Request handling
- Errors with stack traces
```

### Test Database Connection
```python
python3 -c "
from core.database import get_db_connection
db = get_db_connection()
print(f'DB: {db.db_path}')
print('Connected!')
"
```

## 📖 Documentation

- **Architecture**: `ARCHITECTURE.md` - Full architecture documentation
- **Migration**: `MIGRATION_GUIDE.md` - Migration from old architecture
- **Quick Start**: This file - Quick reference guide

## 🔗 Useful Links

- FastAPI Docs: https://fastapi.tiangolo.com/
- Pydantic Docs: https://docs.pydantic.dev/
- Ollama Docs: https://ollama.com/

## 💡 Tips

1. **Use Type Hints**: All functions should have type hints
2. **Pydantic for Validation**: Use Pydantic models for all API schemas
3. **Repository for DB**: Never write SQL in controllers or services directly
4. **Async Where Possible**: Use async/await for I/O operations
5. **Document Your Code**: Add docstrings to all classes and methods
6. **Follow Module Pattern**: Keep consistent structure across modules

## ❓ Need Help?

1. Check `ARCHITECTURE.md` for detailed architecture
2. Check `MIGRATION_GUIDE.md` if migrating code
3. Look at existing modules for examples
4. Review FastAPI and Pydantic documentation
