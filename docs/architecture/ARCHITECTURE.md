# Nexora AI — Architecture Overview

## Module Classification

Nexora AI is built as a **single unified codebase** with three logical modes, controlled by one environment variable: `APP_MODE`.

```
┌─────────────────────────────────────────────────────────────┐
│                        NEXORA AI                            │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐  │
│  │                   ENTERPRISE MODULE (V3)              │  │
│  │  company · CEO dashboard · audit logs · org mgmt     │  │
│  │  ┌─────────────────────────────────────────────────┐  │  │
│  │  │              TEAM MODULE (V2)                   │  │  │
│  │  │  workspaces · tasks · activity · comments       │  │  │
│  │  │  ┌─────────────────────────────────────────┐   │  │  │
│  │  │  │           CORE (V1)                     │   │  │  │
│  │  │  │  auth · chat · rag · ml · python        │   │  │  │
│  │  │  │  analytics · reports · knowledge        │   │  │  │
│  │  │  └─────────────────────────────────────────┘   │  │  │
│  │  └─────────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## APP_MODE Routing

| `APP_MODE` | Core | Team Module | Enterprise Module |
|---|---|---|---|
| `PERSONAL` | ✅ | ❌ | ❌ |
| `TEAM` | ✅ | ✅ | ❌ |
| `ENTERPRISE` | ✅ | ✅ | ✅ |

## Switching Modes

Change **one line** in `.env`:

```env
# V1 — Personal
APP_MODE=PERSONAL

# V2 — Team Collaboration
APP_MODE=TEAM

# V3 — Enterprise SaaS
APP_MODE=ENTERPRISE
```

Feature flags are **automatically derived** from `APP_MODE` in `config.py`:

```python
@property
def enable_team(self) -> bool:
    return self.APP_MODE in ("TEAM", "ENTERPRISE")

@property
def enable_enterprise(self) -> bool:
    return self.APP_MODE == "ENTERPRISE"
```

---

## Module Classification Reference

### 🔵 CORE — Used by: PERSONAL, TEAM, ENTERPRISE

| File/Service | Purpose |
|---|---|
| `endpoints/auth.py` | Login, registration, JWT |
| `endpoints/users.py` | User profile management |
| `endpoints/chat.py` | AI chat with LLM providers |
| `endpoints/conversations.py` | Conversation CRUD + history |
| `endpoints/messages.py` | Message store |
| `endpoints/knowledge.py` | Knowledge base + document upload |
| `endpoints/advanced_search.py` | Hybrid semantic search |
| `endpoints/ml.py` | ML model training/inference |
| `endpoints/training_projects.py` | Dataset training pipelines |
| `endpoints/dataset_projects.py` | Dataset management |
| `endpoints/python_agent.py` | Python code execution sandbox |
| `endpoints/analytics.py` | Data analytics + visualization |
| `endpoints/reports.py` | AI-generated reports |
| `endpoints/agents.py` | Autonomous AI agents |
| `endpoints/email_agent.py` | Email automation agent |
| `endpoints/calendar_agent.py` | Calendar AI agent |
| `endpoints/mcp.py` | Model Context Protocol |
| `endpoints/folders.py` | File folder management |
| `endpoints/search.py` | Basic search |
| `endpoints/notifications.py` | User notifications |
| `endpoints/dashboard.py` | Personal dashboard |
| `endpoints/favorites.py` | Saved items |
| `endpoints/feedback.py` | Chat quality feedback |
| `endpoints/health.py` | System health check |
| `services/rag_service.py` | RAG retrieval pipeline |
| `services/memory_service.py` | Conversation memory |
| `services/knowledge_base_service.py` | Document indexing |

---

### 🟡 TEAM MODULE — Used by: TEAM, ENTERPRISE

| File/Service | Purpose |
|---|---|
| `endpoints/workspaces.py` | Workspace CRUD |
| `endpoints/workspace_members.py` | Member invite/manage |
| `endpoints/workspace_invitations.py` | Invitation link system |
| `endpoints/workspace_templates.py` | Project templates |
| `endpoints/workspace_exports.py` | Export workspace data |
| `endpoints/tasks.py` | Task creation, assignment, AI PM |
| `endpoints/activity.py` | Event-driven activity feed |
| `endpoints/comments.py` | Conversation comments |
| `endpoints/reactions.py` | Message reactions |
| `endpoints/shared_conversations.py` | Shared chat threads |
| `models/workspace.py` | Workspace DB model |
| `models/workspace_member.py` | Member role model |
| `models/workspace_invitation.py` | Invitation model |
| `models/task.py` | Task model |
| `models/document_comment.py` | Document comment model |
| `models/activity_log.py` | Activity log model |
| `services/permission_service.py` | Role-based access control |

---

### 🔴 ENTERPRISE MODULE — Used by: ENTERPRISE only

| File/Service | Purpose |
|---|---|
| `endpoints/company.py` | Company CRUD + CEO dashboard |
| `models/company.py` | Company tenant model |
| `models/company_settings.py` | Company config model |
| `models/company_secrets.py` | Encrypted API key model |
| `models/invitation.py` | Company-level invitations |
| `security/crypto.py` | AES-256-GCM encryption |

---

## Future Physical Refactor Plan (V3 Stable)

Once V2 is stable and tested, the backend will be physically reorganized:

```
apps/backend/app/
  ├── core/          # PERSONAL features
  │   ├── auth/
  │   ├── chat/
  │   ├── rag/
  │   └── ...
  ├── team/          # TEAM features
  │   ├── workspaces/
  │   ├── tasks/
  │   └── ...
  └── enterprise/    # ENTERPRISE features
      ├── companies/
      ├── billing/
      └── ...
```

**Why not now?** See [ROADMAP.md](./ROADMAP.md) for reasoning.
