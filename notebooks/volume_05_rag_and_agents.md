# 📒 Volume 5: Nexora AI — RAG Pipeline, Knowledge Base & Multi-Agent System

> **Focus:** Qdrant vector DB, RAG pipeline, embedding service, multi-agent orchestration  
> **Path:** `D:\Nexora-AI\apps\backend\app\services\`

---

## 📚 Knowledge Base System Overview

```
User uploads PDF/DOCX/TXT
        ↓
/knowledge/upload endpoint
        ↓
DocumentProcessingService
  1. Extract text (PyPDF2 / python-docx)
  2. Split into chunks (~512 tokens each)
  3. Save chunks text in PostgreSQL (document_chunks table)
  4. Embed each chunk → vector via SentenceTransformers
  5. Store vector in Qdrant cloud
        ↓
Knowledge Document status = "ready"
        ↓
User selects KB in chat → Grounded Mode ON
        ↓
RAGService.retrieve_context()
        ↓
Hybrid search (Vector + BM25)
        ↓
Reranked results injected into prompt
        ↓
Model answers from document context
```

---

## 🔍 RAG Pipeline (7 Steps)

### rag_service.py — RAGService.retrieve_context()

```python
# Step 1: Intent Detection
intent = IntentService.detect_intent(user_query)
# intent.category: "factual" | "comparison" | "code" | "summary"

# Step 2: Query Expansion
expanded_terms = IntentService.expand_query(user_query)
# "PEFT" → ["PEFT", "parameter efficient", "fine-tuning", "LoRA", "adapter"]

# Step 3: Hybrid Search
chunks = HybridSearchService.search(
    query=user_query,
    expanded_terms=expanded_terms,
    kb_id=knowledge_base_id,
    vector_weight=0.70,    # 70% vector similarity
    keyword_weight=0.30,   # 30% BM25 keyword match
    top_k=10
)

# Step 4: Knowledge Graph Expansion
related_concepts = KnowledgeGraphService.get_related_concepts(
    chunks=chunks, max_depth=2
)
# Finds conceptually related chunks even if not directly matched

# Step 5: DB Enrichment
enriched_chunks = KnowledgeSearchRepository.enrich_with_metadata(chunks)
# Adds filename, page_number, section info

# Step 6: Multi-Factor Reranking
reranked = RankingService.rerank(
    query=user_query,
    chunks=enriched_chunks,
    # Factors: semantic similarity, recency, source diversity, intent match
)

# Step 7: Context window budget
final_chunks = ContextService.fit_to_budget(
    chunks=reranked,
    max_tokens=settings.MAX_CONTEXT_TOKENS  # 4000 tokens
)

return RAGContext(
    chunks=final_chunks,
    formatted_context=format_chunks_for_prompt(final_chunks),
    metrics=RetrievalMetrics(...)
)
```

---

## 🔢 Embedding Service

```python
# embedding_service.py
class EmbeddingService:
    _model = None  # Singleton (like NexoraProvider)
    
    @classmethod
    def get_model(cls):
        if not cls._model:
            from sentence_transformers import SentenceTransformer
            cls._model = SentenceTransformer(
                "sentence-transformers/all-MiniLM-L6-v2"
            )
            # Dimension: 384 vectors
        return cls._model
    
    @classmethod
    def embed(cls, texts: List[str]) -> List[List[float]]:
        model = cls.get_model()
        return model.encode(texts, show_progress_bar=False).tolist()
        # Returns: 384-dimensional float vectors
```

---

## 🔵 Qdrant Vector Database

### Setup Required

```python
# .env configuration needed:
QDRANT_URL = "https://xxx.us-east-1.aws.cloud.qdrant.io"
QDRANT_API_KEY = "your-api-key"
QDRANT_COLLECTION = "nexora_chunks"
```

### How Vectors are Stored

```python
# Each document chunk → one Qdrant point:
{
    "id": chunk.id,              # UUID
    "vector": [0.123, -0.456, ...],  # 384-dim embedding
    "payload": {
        "chunk_id": chunk.id,
        "document_id": chunk.document_id,
        "kb_id": chunk.kb_id,
        "workspace_id": chunk.workspace_id,
        "content": chunk.content,    # Raw text
        "page_number": chunk.page_number,
        "chunk_index": chunk.chunk_index,
    }
}
```

### Hybrid Search Logic

```python
# HybridSearchService.search():

# 1. Vector search (Qdrant)
vector_results = qdrant_client.search(
    collection_name="nexora_chunks",
    query_vector=EmbeddingService.embed([query])[0],
    query_filter=Filter(must=[FieldCondition(key="kb_id", match=MatchValue(value=kb_id))]),
    limit=top_k,
    with_payload=True,
    score_threshold=0.1
)

# 2. BM25 keyword search (PostgreSQL full-text)
keyword_results = db.query(DocumentChunk)\
    .filter(DocumentChunk.kb_id == kb_id)\
    .filter(text(f"content ILIKE '%{query}%'"))\
    .limit(top_k).all()

# 3. Merge and score
combined = {}
for r in vector_results:
    combined[r.id] = vector_weight * r.score
for r in keyword_results:
    if r.id in combined:
        combined[r.id] += keyword_weight * keyword_score(r, query)
    else:
        combined[r.id] = keyword_weight * keyword_score(r, query)

return sorted(combined.items(), key=lambda x: x[1], reverse=True)
```

---

## 🤖 Multi-Agent System

### Agent Architecture (15 Agent Files)

```
services/agents/
├── base_agent.py          ← Abstract base (all agents inherit)
├── manager_agent.py       ← Routes tasks to specialized agents
├── agent_orchestrator.py  ← Manages multi-step agent workflows
├── agent_session.py       ← Session state management
├── rag_agent.py           ← Document search + answer
├── sql_agent.py           ← Natural language → SQL → execute
├── python_agent.py        ← Code generation + execution
├── analytics_agent.py     ← Data analysis, charts
├── email_agent.py         ← Email drafting + sending
├── calendar_agent.py      ← Event scheduling
├── ml_agent.py            ← Fine-tuning, dataset management
├── memory_agent.py        ← Cross-conversation memory
├── report_agent.py        ← Report generation
├── metrics_service.py     ← Agent performance tracking
└── manager_agent.py       ← Master orchestrator (19KB)
```

### Agent Orchestration Flow

```python
# User sends task via /agents/run
{
    "session_id": "...",
    "task": "Analyze sales data and send summary email"
}

# manager_agent.py:
1. Parse task → identify required agents
   → ["analytics_agent", "email_agent"]

2. Create execution plan:
   Step 1: analytics_agent → analyze_data(query)
   Step 2: email_agent → draft_email(analysis_result)
   Step 3: email_agent → send_email(draft)

3. Execute sequentially with context passing
4. Return final result + execution trace
```

### base_agent.py Structure

```python
class BaseAgent:
    def __init__(self, db, user, workspace_id):
        self.db = db
        self.user = user
        self.workspace_id = workspace_id
        self.ai_service = AIService()
    
    async def run(self, task: str, context: dict = {}) -> AgentResult:
        """Override in each agent"""
        raise NotImplementedError
    
    def _call_llm(self, prompt: str) -> str:
        """Convenience method to call AI"""
        messages = [{"role": "user", "content": prompt}]
        return self.ai_service.generate_response(messages)
```

---

## 📊 Analytics & Monitoring

### What's Tracked

```python
# retrieval_log.py model:
class RetrievalLog(Base):
    conversation_id
    query_text
    num_results
    top_score
    retrieval_time_ms
    reranking_applied
    created_at

# Used in /analytics/dashboard to show:
# - Total queries, avg response time
# - RAG hit rate (% queries with context found)
# - Token usage per workspace
# - Model performance over time
```

---

## 🔬 ML Studio & Fine-Tuning

### Training Project Flow

```python
# /ml/train endpoint:
1. User selects: base_model, dataset, LoRA config
2. TrainingProject created in DB (status="pending")
3. Background task starts:
   - Load base model
   - Load dataset from datasets/ folder
   - Configure LoRA (r=16, alpha=32, target_modules)
   - Start training loop
   - Save adapter weights
4. Status updates: pending → training → completed
5. Adapter uploaded to HuggingFace (optional)
```

### Dataset Factory

```python
# dataset_factory/ folder
# Generates synthetic Q&A pairs for fine-tuning:
# 1. Provide domain (e.g., "AI, Machine Learning")
# 2. Specify num_samples (e.g., 1000)
# 3. AI generates question-answer pairs
# 4. Saved as JSONL: {"prompt": "...", "completion": "..."}
```

---

## 🛠️ Setup Steps for RAG (Next Priority)

```python
# Step 1: Create Qdrant Cloud account (free)
# → https://cloud.qdrant.io
# → Create cluster "nexora" → copy URL + API Key

# Step 2: Colab environment variables
os.environ["QDRANT_URL"] = "https://xxx.qdrant.io"
os.environ["QDRANT_API_KEY"] = "your-key"

# Step 3: Install client
!pip install qdrant-client sentence-transformers -q

# Step 4: Restart backend → Collection auto-created on first upload

# Step 5: Upload PDF via Knowledge Base UI → test RAG chat
```

---

## 📋 Current Project Status

### ✅ Working Features
- JWT Authentication (register/login)
- Multi-workspace system
- Folder organization
- Real-time SSE streaming chat
- Multi-turn conversation memory
- Conversation isolation (new chat = clean slate)
- Markdown rendering (headings, code, tables, bold)
- EOS token filtering
- Qwen3 thinking mode disabled
- Concise system prompt

### ⏳ Pending Setup
- RAG/Knowledge Base (needs Qdrant Cloud URL)
- Multi-agent (needs testing)
- Fine-tuning UI (needs GPU with enough RAM)
- Email agent (needs SMTP config)
- Calendar agent (needs Google Calendar API)

### 🔮 Future Enhancements
- WebSocket support (instead of SSE)
- Voice input/output
- Image understanding (multimodal)
- Team collaboration features
- Production deployment (Docker + cloud)

---

*Volume 5 of 5 | Series Complete*

---

## 📚 Volume Series Index

| Volume | Title | File |
|--------|-------|------|
| 1 | Project Introduction & Setup | `volume_01_project_intro_and_setup.md` |
| 2 | Frontend Architecture | `volume_02_frontend_deep_dive.md` |
| 3 | Backend Architecture | `volume_03_backend_deep_dive.md` |
| 4 | AI Pipeline & Local LLM | `volume_04_ai_pipeline_and_llm.md` |
| 5 | RAG & Multi-Agent System | `volume_05_rag_and_agents.md` |
