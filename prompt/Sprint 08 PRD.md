Title:
AI Chat Engine (OpenAI Compatible)

Objective

When user sends a message

↓

Save User Message

↓

Send to LLM

↓

Receive AI Response

↓

Save Assistant Message

↓

Return Response

--------------------------------

Features

Create AI Service

LLM abstraction layer

Support future providers

OpenAI

OpenRouter

Gemini

Claude

(Local Models Later)

--------------------------------

Create

app/services/ai_service.py

--------------------------------

Flow

POST /chat

↓

Validate JWT

↓

Validate Conversation

↓

Save User Message

↓

Generate AI Response

↓

Save Assistant Message

↓

Return JSON

--------------------------------

Schemas

ChatRequest

conversation_id

message

-----------------------------

ChatResponse

user_message

assistant_message

conversation_id

-----------------------------

Repository

Reuse MessageRepository

Reuse ConversationRepository

-----------------------------

Security

User only accesses own conversations

-----------------------------

Architecture

Router

↓

Service

↓

AI Service

↓

Repository

↓

Database

--------------------------------

Acceptance

✓ Chat endpoint works

✓ User message stored

✓ AI reply stored

✓ Conversation history preserved

✓ Swagger updated