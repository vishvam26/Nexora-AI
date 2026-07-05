Objective

Implement a complete Conversation Management System.

Features
1. Conversation Model

Fields

id
user_id
title
created_at
updated_at
2. Relationship
One User

↓

Many Conversations
3. Endpoints
POST /conversations

Create new conversation.

GET /conversations

Return all conversations of logged-in user.

GET /conversations/{id}

Return conversation details.

User cannot access another user's conversation.

DELETE /conversations/{id}

Soft delete (preferred) or hard delete.

Repository

Create

ConversationRepository
Service

Create

ConversationService

Business validation.

Schemas
ConversationCreate

ConversationResponse

ConversationListResponse
Alembic

Generate migration.

Acceptance Criteria

✅ JWT Required

✅ Only own conversations visible

✅ Conversation created

✅ Conversation list works

✅ Single conversation works

✅ Delete works