# 📚 Nexora AI — Complete Technical Deep Dive & System Architecture Guide

Welcome to the comprehensive technical guide for **Nexora AI**. This document consolidates all core system design, architecture, setup instructions, AI model pipeline, RAG execution, multi-agent frameworks, and real-world user journeys into a single structured manual.

---

## 📑 Table of Contents

- [Volume 1: Project Introduction & Setup Guide](#-volume-1-project-introduction--setup-guide)
- [Volume 2: Frontend Architecture Deep Dive](#-volume-2-frontend-architecture-deep-dive)
- [Volume 3: Backend Architecture Deep Dive](#-volume-3-backend-architecture-deep-dive)
- [Volume 4: AI Pipeline & Local LLM Deep Dive](#-volume-4-ai-pipeline--local-llm-deep-dive)
- [Volume 5: RAG Pipeline, Knowledge Base & Multi-Agent System](#-volume-5-rag-pipeline-knowledge-base--multi-agent-system)
- [Volume 6: User Journey & Real-World Use Cases](#-volume-6-user-journey--real-world-use-cases)

---

# 📘 Volume 1: Project Introduction & Setup Guide

> **Project:** Nexora AI — Enterprise AI & Fine-Tuning Workspace  
> **GitHub:** `https://github.com/vishvam26/Nexora-AI`  
> **Author:** Vishu (vishvam26)  
> **Local LLM:** `vishvam26/nexora-qwen3.5-4b-merged` (Qwen3 4B, fine-tuned)

---

## 🎯 Nexora AI Overview

Nexora AI is a **self-hosted, enterprise-grade AI platform** designed for local and cloud execution — eliminating reliance on mandatory third-party paid APIs. It provides a unified workspace combining real-time streaming chat, retrieval-augmented generation (RAG), autonomous multi-agent orchestration, fine-tuning tools, and data analytics.

### Platform Core Capabilities

| Feature | Description |
|---------|---------------|
| 💬 **Chat Workspace** | Real-time streaming chat powered by Qwen3/Gemini/OpenAI |
| 📚 **Knowledge Base** | Multi-document upload (PDF, DOCX, TXT) with hybrid RAG retrieval |
| 🤖 **Agent Studio** | Multi-agent orchestration — SQL, Python, Email, and Calendar agents |
| 📊 **Analytics Engine** | Real-time monitoring of token consumption, response latency, and costs |
| 🔬 **ML Studio** | QLoRA fine-tuning, synthetic dataset generation, and adapter evaluation |
| 📋 **AI Evaluation** | Model benchmarking and quality auditing dashboard |
| 📝 **Report Studio** | Automated AI-driven document and business report generator |

---

## 🏗️ Technology Stack

```
Frontend:  Next.js 15 (App Router) + TypeScript + Tailwind CSS
           Zustand (state management) + react-markdown + Axios

Backend:   FastAPI (Python 3.11) + Uvicorn ASGI server
           SQLAlchemy ORM + Alembic database migrations
           PostgreSQL / SQLite

AI Layer:  Local: Qwen3 4B (4-bit quantized via BitsAndBytes)
           Cloud: OpenAI / Gemini / OpenRouter / HuggingFace / Ollama

Vector DB: Qdrant — for RAG embeddings
Embedding: sentence-transformers/all-MiniLM-L6-v2

Deploy:    Google Colab T4 GPU + ngrok tunnel / Docker Compose
```

---

## 🚀 Setup Instructions

### 🖥️ Local Development Setup (Windows / Linux)

```powershell
# 1. Clone Repository
git clone https://github.com/vishvam26/Nexora-AI.git
cd Nexora-AI

# 2. Setup Backend Environment
cd apps/backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

# 3. Create .env file & Run Database Migrations
cp .env.example .env
alembic upgrade head

# 4. Start Backend Server
uvicorn app.main:app --reload --port 8000

# 5. Start Frontend Application (New Terminal)
cd apps/frontend
npm install
npm run dev
# Open http://localhost:3000 in your browser
```

---

# 📗 Volume 2: Frontend Architecture Deep Dive

> **Focus:** Next.js 15, App Router, Zustand State, Streaming Chat, API Service  
> **Path:** `apps/frontend/src/`

---

## 🏛️ Frontend Directory Layout

```
src/
├── app/                          ← Next.js App Router pages
│   ├── layout.tsx                ← Root layout (fonts, metadata)
│   ├── globals.css               ← Global styles + CSS variables
│   ├── page.tsx                  ← Auth portal (route: /)
│   └── chat/page.tsx             ← Main workspace (route: /chat)
│
├── components/                   ← UI Workspace Components
│   ├── chat-sidebar.tsx          ← Left navigation panel
│   ├── chat-area.tsx             ← Main chat interface & streaming controller
│   ├── chat-message.tsx          ← Markdown message rendering bubble
│   ├── knowledge-area.tsx        ← KB management + document upload
│   ├── analytics-area.tsx        ← Usage metrics & analytics
│   ├── agent-studio.tsx          ← Multi-agent control panel
│   ├── ml-area.tsx               ← Fine-tuning & ML training UI
│   ├── sql-studio.tsx            ← Natural language to SQL studio
│   ├── python-studio.tsx         ← Python execution sandbox
│   ├── email-studio.tsx          ← AI email composer
│   └── calendar-studio.tsx       ← Smart scheduling assistant
│
├── services/
│   └── api-service.ts            ← Unified API client (Axios + SSE streaming)
│
├── stores/
│   └── chat-store.ts             ← Zustand global store
```

---

## 💬 Chat Streaming & Markdown Mechanics

1. **Streaming Flow (`chat-area.tsx`)**:
   - User submits prompt ➔ `addMessage({ role: "user", content: prompt })`.
   - Empty placeholder created ➔ `addMessage({ role: "assistant", content: "" })`.
   - `apiService.streamChat()` consumes Server-Sent Events (SSE) token chunks.
   - Tokens appended dynamically to Zustand store via `updateLastMessageContent(token)`.

2. **Markdown Rendering (`chat-message.tsx`)**:
   - Utilizes `ReactMarkdown` with `remark-gfm` plugin.
   - Supports headings, bold/italic, bullet lists, GFM tables, blockquotes, and code syntax highlighting with one-click copy buttons.

---

# 📙 Volume 3: Backend Architecture Deep Dive

> **Focus:** FastAPI, SQLAlchemy ORM, Repository Pattern, Endpoint Design  
> **Path:** `apps/backend/app/`

---

## 🏛️ Backend Architecture Overview

```
app/
├── main.py                      ← FastAPI application entry point
├── config.py                    ← Pydantic BaseSettings configuration
├── api/v1/endpoints/            ← Modular endpoint routers (Auth, Chat, Knowledge, Workspaces, etc.)
├── models/                      ← SQLAlchemy ORM database models
├── schemas/                     ← Pydantic request/response validation schemas
├── repositories/                ← Abstraction layer for database queries
├── services/                    ← Business logic (RAG, Chat, Agents, Fine-tuning)
├── providers/                   ← Multi-LLM provider wrappers
└── security/                    ← Passlib password hashing & JWT token verification
```

---

## 🗄️ Database Entity Schema Summary

- **User & Workspaces**: `users`, `workspaces`, `workspace_members`, `workspace_invitations`.
- **Conversations**: `conversations`, `messages`, `folders`, `conversation_comments`, `message_reactions`.
- **Knowledge & RAG**: `knowledge_bases`, `knowledge_documents`, `document_chunks`, `retrieval_logs`.
- **ML & Fine-Tuning**: `training_projects`, `training_runs`, `training_artifacts`, `dataset_projects`.

---

# 📕 Volume 4: AI Pipeline & Local LLM Deep Dive

> **Focus:** NexoraProvider, Singleton Model Loader, BitsAndBytes 4-bit Quantization  
> **Path:** `apps/backend/app/providers/`

---

## 🤖 Multi-LLM Provider Architecture

```
Request ➔ AIService ➔ ProviderFactory.get_provider()
                           ├── "nexora"       ➔ NexoraProvider (Local Qwen3 4B)
                           ├── "openai"       ➔ OpenAIProvider
                           ├── "gemini"       ➔ GeminiProvider
                           ├── "openrouter"   ➔ OpenRouterProvider
                           └── "ollama"       ➔ OllamaProvider
```

### Singleton Model Loader (`NexoraProvider`)
To prevent re-loading heavy weights on every API request, `NexoraProvider` uses class-level singletons (`_model`, `_tokenizer`, `_load_lock`). `preload_model()` is executed eagerly at FastAPI startup:

```python
# 4-bit Quantization Configuration
quantization_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_compute_dtype=torch.float16,
    bnb_4bit_use_double_quant=True,
    bnb_4bit_quant_type="nf4"
)
```

---

# 📒 Volume 5: RAG Pipeline, Knowledge Base & Multi-Agent System

> **Focus:** Qdrant Vector Database, Hybrid Search, Multi-Agent Orchestration  
> **Path:** `apps/backend/app/services/`

---

## 🔍 Hybrid RAG Pipeline

```
User Query ➔ Query Expansion ➔ Parallel Search (Vector + Keyword) ➔ Near-Duplicate Filtering ➔ Reranking ➔ Context Budget Trimming ➔ Final Prompt Injection
```

1. **Vector Embedding**: Text chunks embedded into 384-dimensional vectors using `sentence-transformers/all-MiniLM-L6-v2`.
2. **Qdrant Storage**: Vectors stored in Qdrant collections with workspace payload filtering.
3. **Hybrid Search**: Combines Qdrant vector similarity (70% weight) and lexical full-text matching (30% weight).

---

# 🌐 Volume 6: User Journey & Real-World Use Cases

> **Focus:** End-to-end workflows for CEOs, Data Analysts, Developers, and Researchers

---

## 🏢 PDF Knowledge Base Analysis Flow

1. **Create Knowledge Base**: Navigate to Knowledge Base tab ➔ Create "Q2 2025 Financial Reports".
2. **Upload Documents**: Upload company PDF reports (`sales_june.pdf`, `finance_q2.pdf`). Text is automatically chunked, embedded, and indexed in Qdrant.
3. **Enable Grounded Mode**: Switch Grounded Mode ON in chat interface and select "Q2 2025 Financial Reports".
4. **Query & Attribution**: Ask "What was our total revenue in June 2025?". Nexora AI responds using verified document context and cites source footnotes (`[1] finance_q2.pdf • Page 3`).

---

*End of Nexora AI Master Technical Deep Dive & Architecture Guide.*
