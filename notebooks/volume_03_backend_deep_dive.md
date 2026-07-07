# 📙 Volume 3: Nexora AI — Backend Architecture Deep Dive

> **Focus:** FastAPI server, 42 endpoints, services, database ORM models, repository pattern  
> **Path:** `D:\Nexora-AI\apps\backend\app\`

---

## 🏛️ Backend Folder Structure (Complete)

```
app/
├── main.py                      ← FastAPI app entry point
├── config.py                    ← Pydantic settings (all env vars)
│
├── api/v1/endpoints/            ← 42 route files
│   ├── auth.py                  ← /auth/register, /auth/login
│   ├── users.py                 ← /users/me
│   ├── workspaces.py            ← /workspaces CRUD
│   ├── folders.py               ← /folders CRUD
│   ├── conversations.py         ← /conversations CRUD + share
│   ├── chat.py                  ← /chat/stream (MAIN SSE ENDPOINT)
│   ├── messages.py              ← /messages/{conv_id}
│   ├── knowledge.py             ← /knowledge/* (KB + RAG)
│   ├── agents.py                ← /agents/* orchestration
│   ├── analytics.py             ← /analytics/dashboard
│   ├── eval.py                  ← /eval/* evaluation
│   ├── training_projects.py     ← /training-projects CRUD
│   ├── dataset_projects.py      ← /dataset-projects CRUD
│   ├── ml.py                    ← /ml/* fine-tuning
│   ├── health.py                ← /health check
│   ├── benchmark.py             ← /benchmark
│   ├── reports.py               ← /reports/*
│   ├── search.py                ← /search
│   ├── advanced_search.py       ← /advanced-search
│   ├── monitoring.py            ← /monitoring/metrics
│   ├── rag_debug.py             ← /rag-debug/pipeline
│   ├── python_agent.py          ← /python-agent/run
│   ├── sql_agent.py             ← (via agents.py)
│   ├── email_agent.py           ← /email-agent/send
│   ├── calendar_agent.py        ← /calendar-agent/event
│   ├── workspace_members.py     ← /workspaces/{id}/members
│   ├── workspace_invitations.py ← /workspaces/{id}/invitations
│   ├── workspace_templates.py   ← /workspace-templates
│   ├── workspace_exports.py     ← /workspaces/{id}/export
│   ├── workspace_imports.py     ← /workspaces/{id}/import
│   ├── notifications.py         ← /notifications
│   ├── feedback.py              ← /feedback
│   ├── reactions.py             ← /reactions
│   ├── comments.py              ← /comments
│   ├── favorites.py             ← /favorites
│   ├── shared_conversations.py  ← /shared/{token}
│   ├── dashboard.py             ← /dashboard
│   ├── cost.py                  ← /cost
│   ├── quality.py               ← /quality
│   ├── replay.py                ← /replay
│   ├── mcp.py                   ← /mcp (Model Context Protocol)
│   └── agent_metrics.py         ← /agent-metrics
│
├── models/                      ← 24 SQLAlchemy ORM models
├── schemas/                     ← Pydantic schemas (input/output)
├── repositories/                ← 20 DB repository files
├── services/                    ← Business logic
├── providers/                   ← AI model providers
├── prompts/                     ← Prompt text files
├── core/                        ← DB session, base model
├── security/                    ← JWT utilities
├── db/                          ← Alembic migration files
└── utils/                       ← Helper utilities
```

---

## ⚡ main.py — Startup Sequence

```python
app = FastAPI(title="Nexora AI API")

# 1. Rate Limiter
limiter = Limiter(key_func=get_remote_address, default_limits=["30/minute"])
app.state.limiter = limiter

# 2. CORS (allows all for dev)
app.add_middleware(CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. All 42 routers included
app.include_router(auth_router, prefix="/api/v1")
app.include_router(chat_router, prefix="/api/v1")
# ... 40 more routers

# 4. Startup: DB create + Model preload
@app.on_event("startup")
async def startup():
    Base.metadata.create_all(bind=engine)        # Create DB tables
    NexoraProvider.preload_model()               # Load LLM ONCE (key fix!)
```

---

## 🗄️ Database Models (24 SQLAlchemy Models)

### Core Models

```python
# users
class User(Base):
    id, full_name, email, password_hash
    is_active, created_at, updated_at

# workspaces
class Workspace(Base):
    id, name, description, owner_id (FK: users)
    plan, icon, color, visibility
    is_active, created_at

# folders
class Folder(Base):
    id, name, workspace_id, user_id
    color, position, is_archived

# conversations
class Conversation(Base):
    id, user_id, workspace_id, folder_id
    title, summary          ← MEMORY: compressed conversation history
    is_pinned, is_archived, is_deleted
    share_token             ← for public sharing

# messages
class Message(Base):
    id, conversation_id, role ("user" | "assistant")
    content, sources        ← sources = JSON array of RAG citations
    created_at
```

### Knowledge Base Models

```python
# knowledge_bases
class KnowledgeBase(Base):
    id, workspace_id, user_id
    title, description, icon, color

# knowledge_documents
class KnowledgeDocument(Base):
    id, kb_id, workspace_id
    filename, file_type, file_size
    status ("processing" | "ready" | "failed")
    chunk_count, page_count

# document_chunks
class DocumentChunk(Base):
    id, document_id, kb_id, workspace_id
    content         ← raw text stored in PostgreSQL
    chunk_index, page_number
    # Vector embedding stored separately in Qdrant
```

### ML/Training Models

```python
# training_projects
class TrainingProject(Base):
    id, workspace_id, user_id
    name, base_model_id, adapter_id
    status, config (JSON), metrics (JSON)

# dataset_projects  
class DatasetProject(Base):
    id, workspace_id, user_id
    name, domain, num_samples
    status, dataset_path
```

---

## 🔧 Services Layer (Business Logic)

### chat_service.py — Main Chat Orchestrator

```python
async def handle_chat_stream(db, user, conversation_id, message, ...):
    
    # Step 1: Validate ownership
    conv = ConversationRepo.get_by_id_and_user(db, conv_id, user.id)
    
    # Step 2: Fetch history (last MAX_HISTORY_MESSAGES = 10)
    history = MessageRepo.get_recent(db, conv_id, limit=10)
    
    # Step 3: Save user message
    MessageRepo.create(db, conv_id, "user", message_text)
    db.commit()
    
    # Step 4: RAG (if grounded + Qdrant configured)
    context = ""
    if grounded and kb_id:
        rag_result = RAGService.retrieve_context(db, query, workspace_id, kb_id)
        context = rag_result.formatted_context
    
    # Step 5: Build prompt
    messages = PromptService.build_prompt(
        history=history,
        current_user_message=message_text,
        retrieved_knowledge=context,
        grounded=grounded
    )
    
    # Step 6: Stream generator
    def generator():
        full = ""
        for token in AIService.generate_stream_response(messages):
            full += token
            yield f"data: {json.dumps({'content': token})}\n\n"
        
        # Step 7: Save full assistant response
        MessageRepo.create(db, conv_id, "assistant", full)
        db.commit()
    
    return StreamingResponse(generator(), media_type="text/event-stream")
```

### ai_service.py — Provider Delegation

```python
class AIService:
    @staticmethod
    def generate_stream_response(messages):
        provider = ProviderFactory.get_provider()  # Gets NexoraProvider
        yield from provider.generate_stream_response(messages)
        # KEY: "yield from" not "return" — chains the generator
```

### prompt_service.py + context_builder.py

```
Final prompt payload assembly order:
① system_prompt.txt content
② developer_prompt.txt content  → "[Developer Instructions]..."
③ [GROUNDING POLICY]            → only if grounded=True + has_context
④ [Conversation Summary]        → compressed memory
⑤ [Retrieved Context]           → RAG chunks
⑥ Recent History                → last 10 messages
⑦ Current user message
```

---

## 📦 Repository Pattern

Each repository has standard CRUD + domain-specific queries:

```python
# Example: conversation_repository.py
class ConversationRepository:
    def get_by_id(db, id) → Conversation
    def get_by_id_and_user(db, id, user_id) → Conversation  ← ownership check
    def list_by_workspace(db, workspace_id, user_id) → List[Conversation]
    def create(db, user_id, workspace_id, title) → Conversation
    def update(db, id, **kwargs) → Conversation
    def delete(db, id) → None
    def search(db, query, workspace_id) → List[Conversation]
```

**Why Repository Pattern?**  
- Service layer never touches SQLAlchemy directly
- Easy to swap DB (PostgreSQL → SQLite for testing)
- Clean separation of concerns

---

## 🔐 Security (security/ folder)

```python
# JWT creation
def create_access_token(data: dict) → str:
    payload = data.copy()
    payload["exp"] = datetime.utcnow() + timedelta(minutes=60)
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

# JWT verification (FastAPI dependency)
async def get_current_user(token: str = Depends(oauth2_scheme), db = Depends(get_db)):
    payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    user = UserRepo.get_by_email(db, payload["sub"])
    return user  # Injected into every protected endpoint
```

---

## ⚙️ config.py — Complete Settings Reference

```python
class Settings(BaseSettings):
    APP_NAME = "Nexora AI"
    DATABASE_URL = "postgresql://nexora:nexora123@localhost:5432/nexora_ai"
    SECRET_KEY = "CHANGE_THIS"
    ACCESS_TOKEN_EXPIRE_MINUTES = 60
    
    # AI
    AI_PROVIDER = "openai"           # Set to "nexora" for local
    NEXORA_MODEL_ID = "vishvam26/nexora-qwen3.5-4b-merged"
    NEXORA_BASE_MODEL_ID = "Qwen/Qwen2.5-1.5B-Instruct"
    NEXORA_MAX_NEW_TOKENS = 512
    NEXORA_TEMPERATURE = 0.7
    NEXORA_TOP_P = 0.9
    NEXORA_DEVICE = "auto"           # cuda / cpu / auto
    
    # RAG
    QDRANT_URL = ""
    QDRANT_API_KEY = ""
    QDRANT_COLLECTION = "nexora_chunks"
    EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
    RAG_TOP_K = 10
    SIMILARITY_THRESHOLD = 0.1
    ENABLE_RERANKING = True
    HYBRID_VECTOR_WEIGHT = 0.70
    HYBRID_KEYWORD_WEIGHT = 0.30
    
    # Prompts
    SYSTEM_PROMPT_PATH = "app/prompts/system_prompt.txt"
    DEVELOPER_PROMPT_PATH = "app/prompts/developer_prompt.txt"
    
    # Memory
    MAX_HISTORY_MESSAGES = 10
    SUMMARY_TRIGGER = 20
    
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
```

---

## 📝 Prompt Files

### system_prompt.txt
```
You are Nexora AI, a helpful, intelligent, and friendly virtual assistant. 
Keep your answers concise and focused. Use clear headings and bullet points 
for complex topics. Avoid unnecessary preamble, filler text, or repetition. 
Answer directly and stop when done.
```

### developer_prompt.txt
```
You must output clean, robust, and concise answers. 
When writing code, always specify the programming language.
```

---

*Volume 3 of 5 | Next → Volume 4: AI Pipeline & Local LLM*
