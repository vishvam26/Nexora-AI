# Nexora AI — V2 (Team Collaboration Mode)

## What is V2?

V2 is the **Team AI Workspace** — a collaborative project environment for student groups, startup teams, and research projects.

Think: **GitHub + Notion + ChatGPT** for your team.

## How to Run V2

In your `.env` file, set:

```env
APP_MODE=TEAM
```

All core features + team collaboration features will be automatically enabled.

## Features Included in V2

### ✅ Everything in V1 (Core), PLUS:

| Module | Description |
|---|---|
| 🏢 Workspaces | Isolated project spaces per team |
| 👥 Team Members | Invite members with role-based access |
| ✅ Task Management | Create, assign, and track tasks |
| 📜 Activity Feed | GitHub-like event timeline |
| 💬 Document Comments | Comment and discuss on shared files |
| 🔗 Workspace Invitations | Join via invite link or code |
| 📊 Leader Dashboard | Project overview for team leader |
| 🤖 AI Project Manager | AI-driven task completion insights |
| 🔒 File Visibility | PRIVATE / WORKSPACE / READ_ONLY / PUBLIC |

## Team Roles

```
OWNER (Team Leader)
  └── ADMIN
        └── EDITOR (Team Member)
              └── VIEWER (Read-only)
```

## Example Use Case

```
College project group:
  ├── Leader (OWNER) → sees all tasks, activity, members
  ├── Member 1 (EDITOR) → uploads datasets, creates reports
  ├── Member 2 (EDITOR) → trains ML models
  └── Member 3 (VIEWER) → reviews reports only
```

## Features NOT included in V2

- ❌ Company / CEO hierarchy
- ❌ Billing / Subscription
- ❌ Audit Logs
- ❌ Organization Management

## Deployment

```bash
APP_MODE=TEAM uvicorn app.main:app --host 0.0.0.0 --port 8000
```
