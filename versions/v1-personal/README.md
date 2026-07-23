# Nexora AI — V1 Personal Edition

## What is this?

V1 is the **Personal AI Workspace** — a powerful single-user AI assistant.

No team, no company hierarchy. Just you and your AI.

---

## Quick Start

### Step 1 — Copy `.env.example` to `apps/backend/.env`

```bash
cp versions/v1-personal/.env.example apps/backend/.env
```

### Step 2 — Install dependencies

```bash
cd apps/backend
pip install -r requirements.txt
```

### Step 3 — Run database migrations

```bash
alembic upgrade head
```

### Step 4 — Start backend

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Step 5 — Start frontend (separate terminal)

```bash
cd apps/frontend
npm install
npm run dev
```

---

## Features Included in V1

| Module | Status |
|---|---|
| 🤖 AI Chat (Gemini / OpenAI / Local LLM) | ✅ |
| 🧠 Conversation Memory | ✅ |
| 📚 Knowledge Base + Document Upload | ✅ |
| 🔍 Hybrid RAG Engine (Vector + Keyword) | ✅ |
| 📊 Analytics Studio | ✅ |
| 🤖 ML Studio (Train + Inference) | ✅ |
| 🐍 Python Sandbox | ✅ |
| 🗄️ SQL Assistant | ✅ |
| 📝 AI Report Generator | ✅ |
| 🔎 Semantic Search | ✅ |
| 👥 Multi-Agent System (Email, Calendar, MCP) | ✅ |

## Features NOT in V1

- ❌ Team Workspaces
- ❌ Task Management
- ❌ Activity Feed
- ❌ Company Hierarchy

→ Upgrade to **V2** or **V3** for those features.
