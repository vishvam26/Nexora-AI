# Nexora AI — V2 Team Edition

## What is this?

V2 is the **Team AI Workspace** — a collaborative project environment for student groups, startup teams, and research projects.

**Think: GitHub + Notion + ChatGPT for your team.**

---

## Quick Start

### Step 1 — Copy `.env.example` to `apps/backend/.env`

```bash
cp versions/v2-team/.env.example apps/backend/.env
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

## Features in V2 (Core + Team)

### ✅ Everything from V1, PLUS:

| Module | Status |
|---|---|
| 🏢 Workspaces (Team Projects) | ✅ |
| 👥 Member Invite with Roles | ✅ |
| ✅ Task Creation & Assignment | ✅ |
| 📜 GitHub-style Activity Feed | ✅ |
| 💬 Document Comments | ✅ |
| 🔗 Workspace Invitation Links | ✅ |
| 📊 Leader Dashboard | ✅ |
| 🤖 AI Project Manager | ✅ |
| 🔒 File Visibility Controls | ✅ |

## Team Roles

```
OWNER (Team Leader)
  └── ADMIN
        └── EDITOR (Team Member)
              └── VIEWER (Read-only)
```

## Example Use Case

```
College project group (5 students):
  ├── Vishvam  (OWNER)  → sees all tasks, activity, approves work
  ├── Rahul    (EDITOR) → uploads datasets, creates reports
  ├── Meet     (EDITOR) → trains ML models
  ├── Dev      (EDITOR) → runs Python scripts
  └── Krish    (VIEWER) → reviews reports only
```

## Features NOT in V2

- ❌ Company / CEO hierarchy
- ❌ Multi-tenant isolation
- ❌ Billing / Audit Logs

→ Upgrade to **V3** for enterprise features.
