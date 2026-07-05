# Sprint 04 – Database Migration & Configuration

## Sprint Name
Production Ready Database Layer

---

# Objective

Convert the current backend from development mode to production-ready database management.

Currently the project uses:

Base.metadata.create_all(bind=engine)

This must be replaced with Alembic migrations.

The project should also move every secret and configuration value into environment variables.

---

# Business Goal

Create a backend that follows industry standards and can be deployed without changing source code.

---

# Current Status

Completed

- FastAPI
- PostgreSQL
- Docker
- SQLAlchemy
- Register API
- Login API
- JWT Authentication
- Protected Routes

---

# Sprint Deliverables

## 1. Alembic

Setup Alembic inside backend.

Requirements

- Initialize Alembic
- Configure SQLAlchemy metadata
- Configure env.py
- Configure alembic.ini
- Generate first migration
- Apply migration

---

## 2. Environment Configuration

Move every secret into .env

Variables

APP_NAME
APP_VERSION
DATABASE_URL
SECRET_KEY
ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES

---

## 3. Config Module

Create a clean Settings class using pydantic-settings.

The entire project must read values only from settings.

No hardcoded values are allowed.

---

## 4. Database Layer

Remove

Base.metadata.create_all()

Database schema must be managed only by Alembic.

---

## 5. Docker

Docker Compose must continue working without modifications.

Database connection should use DATABASE_URL.

---

# Acceptance Criteria

✅ Server starts

✅ Login works

✅ Register works

✅ /users/me works

✅ Alembic migration generated

✅ alembic upgrade head works

✅ No hardcoded secrets

---

# Non Goals

Do NOT

- change APIs
- change folder structure
- rewrite services
- rewrite repositories
- rewrite authentication

---

# Files Expected

Create

alembic/
alembic.ini

Update

app/config.py
app/db/database.py
requirements.txt
.env.example

---

# Testing Checklist

Run

uvicorn app.main:app --reload

Test

POST /auth/register

POST /auth/login

GET /users/me

Run

alembic revision --autogenerate

Run

alembic upgrade head

Everything should pass.

---

Sprint Status

Target = COMPLETE