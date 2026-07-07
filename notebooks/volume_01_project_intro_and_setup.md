# 📘 Volume 1: Nexora AI — Project Introduction & Setup Guide

> **Project:** Nexora AI — Enterprise AI & Fine-Tuning Workspace  
> **GitHub:** `https://github.com/vishvam26/Nexora-AI`  
> **Author:** Vishu (vishvam26)  
> **Local LLM:** `vishvam26/nexora-qwen3.5-4b-merged` (Qwen3 4B, fine-tuned)

---

## 🎯 Nexora AI — Shu Chhe?

Nexora AI ek **self-hosted, enterprise-grade AI platform** chhe jene tame khud run karo chho — koi paid API ni jarur nathi. Aa ek poori system chhe jema chat, RAG, agents, fine-tuning, analytics — badhu ek j jagya par.

### Platform na Main Features

| Feature | Shu kare chhe? |
|---------|---------------|
| 💬 **Chat Workspace** | Local Qwen3 LLM sathe real-time streaming chat |
| 📚 **Knowledge Base** | PDF/DOCX upload karo → AI tena mathi answer aape (RAG) |
| 🤖 **Agent Studio** | Multi-agent system — SQL, Python, Email, Calendar agents |
| 📊 **Analytics Engine** | Token usage, response time, cost tracking |
| 🔬 **ML Studio** | LoRA fine-tuning, dataset generation, model management |
| 📋 **AI Evaluation** | Benchmark ane eval dashboard |
| 📝 **Report Studio** | AI-powered report generation |
| 🗓️ **Calendar/Email** | Smart scheduling ane email drafting agents |

---

## 🏗️ Technology Stack

```
Frontend:  Next.js 15 (App Router) + TypeScript + Tailwind CSS
           Zustand (state) + react-markdown + axios

Backend:   FastAPI (Python 3.11) + Uvicorn ASGI server
           SQLAlchemy ORM + Alembic migrations
           PostgreSQL (database)

AI Layer:  Local: Qwen3 4B (4-bit quantized via BitsAndBytes)
           Cloud: OpenAI / Gemini / OpenRouter / HuggingFace / Ollama

Vector DB: Qdrant (cloud free tier) — for RAG embeddings
Embedding: sentence-transformers/all-MiniLM-L6-v2

Deploy:    Google Colab T4 GPU + ngrok tunnel
           (Docker Compose for local full-stack)
```

---

## 📁 Project Folder Structure

```
D:\Nexora-AI\
│
├── apps/
│   ├── backend/               ← FastAPI server (main backend)
│   │   ├── app/
│   │   │   ├── main.py        ← App entry point
│   │   │   ├── config.py      ← All settings from .env
│   │   │   ├── api/           ← 42 API route files
│   │   │   ├── models/        ← 24 database ORM models
│   │   │   ├── schemas/       ← Pydantic input/output schemas
│   │   │   ├── services/      ← Business logic (chat, RAG, agents)
│   │   │   ├── repositories/  ← Database access layer
│   │   │   ├── providers/     ← AI model providers (6 providers)
│   │   │   └── prompts/       ← system_prompt.txt, developer_prompt.txt
│   │   └── requirements.txt
│   │
│   └── frontend/              ← Next.js app
│       └── src/
│           ├── app/           ← App Router pages
│           ├── components/    ← UI components (14 files)
│           ├── services/      ← api-service.ts (all API calls)
│           ├── stores/        ← chat-store.ts (Zustand state)
│           └── types/         ← TypeScript type definitions
│
├── notebooks/                 ← Documentation volumes (THIS FOLDER)
├── scratch/                   ← Temporary test scripts
├── datasets/                  ← Training datasets
├── dataset_factory/           ← Synthetic data generation
├── models/                    ← Model weights (loaded from HuggingFace)
├── scripts/                   ← Deployment helper scripts
├── docker/                    ← Docker configuration files
├── docker-compose.yml         ← One-command local deployment
├── Makefile                   ← Dev shortcuts (make run, make db, etc.)
├── test_model.py              ← Model inference test script
├── cleanup_project.py         ← Project cleanup utility
├── convert_reqs.py            ← Requirements conversion helper
└── .env.production.example    ← Production env template
```

---

## 🚀 Google Colab Setup (Current Deployment Method)

Nexora AI Colab T4 GPU par free ma run thay chhe.

### Step 1: Repository Clone

```python
# Colab Cell 1
import os
!git clone https://github.com/vishvam26/Nexora-AI.git /content/Nexora-AI
os.chdir("/content/Nexora-AI/apps/backend")
```

### Step 2: Dependencies Install

```python
# Colab Cell 2
!pip install -r requirements.txt -q
!pip install -q bitsandbytes accelerate
```

### Step 3: Environment Variables Set

```python
# Colab Cell 3
import os
os.environ["DATABASE_URL"] = "sqlite:///./nexora.db"  # SQLite for Colab
os.environ["AI_PROVIDER"] = "nexora"
os.environ["NEXORA_MODEL_ID"] = "vishvam26/nexora-qwen3.5-4b-merged"
os.environ["SECRET_KEY"] = "your-secret-key-here"
os.environ["HF_TOKEN"] = "your-hf-token"  # Optional
```

### Step 4: Backend Start

```python
# Colab Cell 4
import subprocess, threading
def run_server():
    subprocess.run(["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"])
thread = threading.Thread(target=run_server, daemon=True)
thread.start()
```

### Step 5: ngrok Tunnel

```python
# Colab Cell 5
from pyngrok import ngrok
public_url = ngrok.connect(8000)
print(f"Backend URL: {public_url}")
# Copy this URL to frontend .env.local as NEXT_PUBLIC_API_URL
```

---

## 🖥️ Local Development Setup (Windows)

```powershell
# 1. Clone
git clone https://github.com/vishvam26/Nexora-AI.git
cd Nexora-AI

# 2. Backend
cd apps/backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

# 3. Create .env file with DATABASE_URL, SECRET_KEY, etc.
# Copy from .env.production.example

# 4. Run backend
uvicorn app.main:app --reload --port 8000

# 5. Frontend (new terminal)
cd apps/frontend
npm install
npm run dev
# → http://localhost:3000
```

---

## 🔑 Key Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | postgresql://... | PostgreSQL connection string |
| `SECRET_KEY` | CHANGE_THIS | JWT signing secret |
| `AI_PROVIDER` | openai | `nexora` / `openai` / `gemini` etc. |
| `NEXORA_MODEL_ID` | vishvam26/... | HuggingFace model ID |
| `NEXORA_MAX_NEW_TOKENS` | 512 | Max output length |
| `QDRANT_URL` | (empty) | Qdrant Cloud URL for RAG |
| `QDRANT_API_KEY` | (empty) | Qdrant API key |
| `HF_TOKEN` | (empty) | HuggingFace token |

---

## ✅ Testing Milestones Achieved

| Test | Status |
|------|--------|
| Chat Streaming | ✅ Working |
| Multi-turn Memory | ✅ Working |
| Conversation Isolation | ✅ Working |
| Markdown Rendering | ✅ Working |
| EOS Token Filtering | ✅ Fixed |
| Thinking Mode Disabled | ✅ Fixed |
| RAG Pipeline | ⏳ Needs Qdrant setup |

---

*Volume 1 of 5 | Next → Volume 2: Frontend Architecture*
