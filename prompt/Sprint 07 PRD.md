# Sprint 07 – Message Management System

## Objective

Implement persistent messages inside conversations.

Each conversation can contain multiple messages.

---

## Database Model

Message

Fields

id

conversation_id

role

content

created_at

updated_at

is_deleted

---

role values

"user"

"assistant"

"system"

---

Relationships

Conversation

↓

Many Messages

---

Endpoints

POST /messages

Create message

---

GET /messages/{conversation_id}

Return all conversation messages

---

DELETE /messages/{id}

Soft delete message

---

Repository

MessageRepository

---

Service

MessageService

---

Schemas

MessageCreate

MessageResponse

MessageListResponse

---

Security

JWT Required

User can access ONLY own conversation messages.

---

Acceptance Criteria

✓ Create message

✓ Retrieve conversation history

✓ Delete message

✓ Ownership validation

✓ Alembic migration

✓ Swagger updated