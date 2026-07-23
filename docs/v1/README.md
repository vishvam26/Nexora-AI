# Nexora AI — V1 (Personal Mode)

## What is V1?

V1 is the **Personal AI Workspace** — a single-user, standalone AI assistant with powerful core capabilities.

No team, no company. Just you and your AI.

## How to Run V1

In your `.env` file, set:

```env
APP_MODE=PERSONAL
```

That's it. All team and enterprise features will be automatically disabled.

## Features Included in V1 (Core)

| Module | Description |
|---|---|
| 🤖 AI Chat | Conversational AI with memory |
| 🧠 Memory | Context-aware conversation history |
| 📚 Knowledge Base | Upload and query your own documents |
| 🔍 RAG Engine | Hybrid retrieval (vector + keyword) |
| 📊 Analytics Studio | Visualize data interactively |
| 🤖 ML Studio | Train and test ML models |
| 🐍 Python Sandbox | Execute Python code in-browser |
| 🗄️ SQL Studio | Query databases with AI assistance |
| 📝 Reports | AI-generated document reports |
| 🔎 Search | Semantic + lexical hybrid search |
| 👥 Agents | Email, Calendar, MCP agents |

## Features NOT included in V1

- ❌ Workspaces / Teams
- ❌ Task Management
- ❌ Activity Feed
- ❌ Document Comments
- ❌ Company Hierarchy
- ❌ CEO / Admin Dashboard
- ❌ Audit Logs

## Deployment

To deploy V1 on Kaggle / local:

```bash
APP_MODE=PERSONAL uvicorn app.main:app --host 0.0.0.0 --port 8000
```
