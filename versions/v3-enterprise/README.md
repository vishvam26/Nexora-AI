# Nexora AI — V3 Enterprise Edition

## What is this?

V3 is the **Enterprise AI Platform** — a full multi-tenant SaaS system for organizations with company-level hierarchy.

> ⚠️ **Status: Working but not deployed.** V3 is fully built and functional but intentionally not published yet. It is being kept for future commercial use when the product is ready to scale to businesses.

---

## Quick Start

### Step 1 — Copy `.env.example` to `apps/backend/.env`

```bash
cp versions/v3-enterprise/.env.example apps/backend/.env
```

### Step 2 — Switch to PostgreSQL (recommended for enterprise)

```env
DATABASE_URL=postgresql://nexora:nexora123@localhost:5432/nexora_ai
```

### Step 3 — Install and migrate

```bash
cd apps/backend
pip install -r requirements.txt
alembic upgrade head
```

### Step 4 — Start backend

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## Features in V3 (Core + Team + Enterprise)

### ✅ Everything from V2, PLUS:

| Module | Status |
|---|---|
| 🏭 Multi-tenant Company Isolation | ✅ |
| 👔 CEO / Admin Dashboard | ✅ |
| 🛡️ Organization RBAC | ✅ |
| 📋 Audit Logs | ✅ |
| ⚙️ Company Settings (branding, timezone, AI prefs) | ✅ |
| 🔐 AES-256-GCM Encrypted API Key Storage | ✅ |
| 📧 Company-level Invitations | ✅ |
| 🏗️ Department & Team Management | 🔜 |
| 💳 Billing / Subscription | 🔜 |
| 🔑 SSO | 🔜 |

## Enterprise Role Hierarchy

```
CEO / OWNER
  └── ADMIN (Manager)
        └── EMPLOYEE
              └── VIEWER
```

## Tenant Isolation

```
Company A → Workspace A → Files, Chats, Vectors
Company B → Workspace B → Files, Chats, Vectors
(Company A can NEVER access Company B's data)
```

## Why is V3 not deployed?

- Target audience: Businesses and corporations
- Requires proper billing, SSO, and SLA before public deployment
- Currently used as portfolio demonstration of enterprise-grade architecture
