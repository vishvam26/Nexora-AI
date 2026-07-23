# Nexora AI — V3 (Enterprise SaaS Mode)

## What is V3?

V3 is the **Enterprise AI Platform** — a full multi-tenant SaaS system for organizations with structured company hierarchies.

Designed for: Businesses, startups with departments, corporate teams.

## How to Run V3

In your `.env` file, set:

```env
APP_MODE=ENTERPRISE
```

All core + team + enterprise features will be automatically enabled.

## Features Included in V3

### ✅ Everything in V2 (Core + Team), PLUS:

| Module | Description |
|---|---|
| 🏭 Companies | Multi-tenant company isolation |
| 👔 CEO Dashboard | Organization-wide analytics |
| 🛡️ Admin Panel | User management, permissions |
| 📋 Audit Logs | Full action history per company |
| ⚙️ Company Settings | Branding, timezone, AI model prefs |
| 🔐 Company Secrets | AES-256-GCM encrypted API key storage |
| 🏗️ Organization Management | Department and team structuring |
| 📧 Company Invitations | Invite employees by email with roles |

## Enterprise Role Hierarchy

```
CEO / OWNER
  └── ADMIN (Manager)
        └── EMPLOYEE
              └── VIEWER
```

### Tenant Isolation

```
Company A → Workspace A → Files, Vectors, Chats
Company B → Workspace B → Files, Vectors, Chats

(Company A can NEVER see Company B's data)
```

## Example Use Case

```
Tech Startup:
  ├── CEO (OWNER) → sees all workspaces, billing, audit
  ├── CTO (ADMIN) → manages dev team workspaces
  ├── Dev Team (EDITOR) → builds projects collaboratively
  └── Interns (VIEWER) → read-only access
```

## Future V3 Features (Planned)

- 💳 Billing / Stripe / Razorpay integration
- 📦 Subscription plans (Free / Pro / Enterprise)
- 🔑 SSO (Single Sign-On)
- 📈 Usage analytics per department
- 🚀 API key marketplace

## Deployment

```bash
APP_MODE=ENTERPRISE uvicorn app.main:app --host 0.0.0.0 --port 8000
```
