# Nexora-AI

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![Node.js Version](https://img.shields.io/badge/node-%3E%3D18.0.0-green.svg)](https://nodejs.org/)

Nexora-AI is an enterprise-grade, full-stack AI development platform designed for building, training, evaluating, and deploying next-generation intelligent agents, neural networks, and machine learning pipelines.

---

## 🚀 Key Features

* **Modular AI Core:** Scalable models and agent architectures.
* **Intelligent Multi-Agent Orchestration:** Hierarchical planner agent leveraging specialized sub-agents (Analytics, ML, RAG, Memory, Report).
* **Billing & Token Cost Tracker:** Granular diagnostic tracking and cost auditing per model session.
* **Unified Pipeline:** Seamless integration between backend APIs, model training, and frontend interfaces.
* **Production Ready:** Pre-configured Docker environments for seamless orchestration.

---

## 📂 Repository Structure

The project is organized as follows:

```text
Nexora-AI/
├── apps/             # Application applications/services
│   ├── backend/      # Backend service (FastAPI, Qdrant Client, SQLite/PG database)
│   └── frontend/     # Web dashboard / User interface (Next.js React Client)
├── docker/           # Production backend/frontend Dockerfiles and Nginx configurations
├── Makefile          # Orchestration automation shortcuts
└── docker-compose.yml# Production multi-tier stack services (PG, Qdrant, Redis, Nginx, App)
```

---

## 🛠️ Quick Start

### Prerequisites
* Python 3.10+
* Node.js v18+
* Docker & Docker Compose

### Production Deployment

1. **Configure Environment Variables:**
   Create `.env.production` in the project root:
   ```bash
   cp .env.production.example .env.production
   # Open .env.production and paste your secret keys
   ```

2. **Launch the Container Stack:**
   Use the Makefile helper to build and run all services (Nginx, Backend, Frontend, Qdrant, Redis, Postgres):
   ```bash
   make up
   ```

3. **Initialize Database Schema:**
   Apply database migrations inside the active backend container:
   ```bash
   make migrate
   ```

4. **Verify Application Health:**
   Ensure all containers are healthy:
   ```bash
   make status
   ```
   Open `http://localhost` in your browser. Nginx reverse proxies request routing:
   * `/` routes to the Next.js Frontend
   * `/api` routes to the FastAPI Backend

---

## 🧪 Testing

To run the test suite:
```bash
# Run backend tests
cd apps/backend && pytest

# Run frontend tests
cd apps/frontend && npm test
```

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
