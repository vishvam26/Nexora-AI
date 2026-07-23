# Nexora AI — Roadmap

## Current Status

**Version**: 1.0.0-beta  
**Mode**: PERSONAL (V1 core complete)  
**Stage**: Pre-deployment stability testing

---

## Phase 1 — V1 Stable ✅ (Current)

- [x] AI Chat with multiple LLM providers (Gemini, OpenAI, Local Nexora model)
- [x] RAG engine with hybrid search (vector + keyword)
- [x] Knowledge base with document upload and indexing
- [x] ML Studio (training + inference)
- [x] Python Sandbox (code execution)
- [x] Analytics Studio
- [x] Report generation
- [x] Autonomous agents (Email, Calendar, MCP)
- [x] AES-256-GCM secrets encryption
- [x] Multi-tenant database architecture
- [x] APP_MODE modular architecture (PERSONAL / TEAM / ENTERPRISE)
- [x] Task management foundation (models + API)
- [x] Activity feed foundation (models + API)
- [x] Document comments foundation

---

## Phase 2 — Deployment & Beta Testing 🚀 (Next)

- [ ] AWS / Cloud deployment
- [ ] Kaggle Kaggle notebook setup (Ngrok public link)
- [ ] Beta users onboarding (10–20 users)
- [ ] Bug tracking and fixing
- [ ] Performance profiling and optimization
- [ ] API rate limiting
- [ ] Error monitoring (Sentry)

---

## Phase 3 — V2 Team Collaboration 🤝

- [ ] Frontend workspace UI (team dashboard)
- [ ] Task board UI (Kanban / list view)
- [ ] Activity feed UI (GitHub-style timeline)
- [ ] Document comment UI
- [ ] Leader dashboard
- [ ] Workspace invitation UI
- [ ] AI Project Manager recommendations UI
- [ ] Member contribution analytics

---

## Phase 4 — Public Launch 🌍

- [ ] Public documentation site
- [ ] API documentation (Swagger polish)
- [ ] Tutorial videos
- [ ] Community Discord / GitHub Discussions
- [ ] Landing page

---

## Phase 5 — V3 Enterprise SaaS 🏢

- [ ] Company onboarding flow
- [ ] CEO / Admin dashboard UI
- [ ] Audit log UI
- [ ] Organization management UI
- [ ] Physical backend refactor (core / team / enterprise packages)

---

## Phase 6 — Monetization 💳 (Long-term, 2–3 years)

> Only when product has thousands of active users and real-world feedback.

- [ ] Subscription plans (Free / Pro / Enterprise)
- [ ] Stripe / Razorpay billing integration
- [ ] Usage limits per plan
- [ ] Premium features gating
- [ ] SSO (Single Sign-On)

---

## Why Not Monetize Now?

Current goals:
- ✅ Build a strong portfolio project
- ✅ GitHub showcase for interviews
- ✅ Collect real user feedback
- ✅ Fix bugs before scaling

Adding billing now would add complexity without benefit.
**First build, then monetize.**

---

## Physical Refactor Plan (Phase 5)

Currently backend is one unified package.  
After V2 stabilizes, planned structure:

```
apps/backend/app/
  ├── core/
  ├── team/
  └── enterprise/
```

**Postponed until**: V2 complete + stable + deployed + tested.  
**Risk now**: Import breakage, Alembic migration errors, circular imports.
