import logging
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.models.message import Message
from app.repositories.conversation_repository import ConversationRepository
from app.repositories.message_repository import MessageRepository
from app.services.ai_service import AIService
from app.services.memory_service import MemoryService
from app.services.prompt_service import PromptService
from app.services.rag_service import RAGService
from app.services.context_builder import ContextBuilder
from app.schemas.chat import ChatRequest, ChatResponse

logger = logging.getLogger("app.services.chat_service")


class ChatService:
    """
    Service coordinating message validation, RAG retrieval, database persistence,
    and AI response generation with memory management.
    """

    @staticmethod
    def handle_chat(db: Session, user_id: int, request: ChatRequest) -> ChatResponse:
        """
        Full chat pipeline:
        1. Validate conversation ownership
        2. Save user message
        3. Hybrid RAG retrieval (workspace-scoped, with query expansion and graph traversal)
        4. Build prompt (System → Developer → Memory → Summary → RAG → Graph → History → User)
        5. Generate AI response
        6. Save assistant reply
        7. Update conversation memory
        """
        # 1. Validate conversation exists and is owned by the user
        conversation = ConversationRepository.get_by_id(db, request.conversation_id)
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        if conversation.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have access to this conversation"
            )

        # 2. Save user message to database
        user_message_obj = Message(
            conversation_id=request.conversation_id,
            role="user",
            content=request.message
        )
        MessageRepository.create(db, user_message_obj)

        # 3. RAG Retrieval — workspace-scoped, graceful fallback on failure
        retrieved_knowledge = ""
        graph_knowledge = ""
        if request.workspace_id:
            try:
                from app.config import settings
                from app.services.adaptive_retrieval_service import AdaptiveRetrievalService
                rag_context = AdaptiveRetrievalService.retrieve_context(
                    db=db,
                    user_query=request.message,
                    workspace_id=request.workspace_id,
                    knowledge_base_id=request.knowledge_base_id,
                    top_k=settings.RAG_TOP_K,
                    similarity_threshold=settings.SIMILARITY_THRESHOLD,
                    max_context_tokens=settings.MAX_CONTEXT_TOKENS,
                    enable_reranking=settings.ENABLE_RERANKING,
                )
                if rag_context.has_knowledge:
                    retrieved_knowledge = rag_context.formatted_context
                    graph_knowledge = rag_context.graph_context or ""
                    logger.info(
                        f"RAG injected {rag_context.metrics.retrieved_count} chunks | "
                        f"Graph connections: {graph_knowledge} | "
                        f"Confidence: {rag_context.confidence_score} | "
                        f"latency={rag_context.metrics.latency_ms:.1f}ms"
                    )
            except Exception as e:
                logger.error(f"RAG retrieval failed — continuing without knowledge: {e}")

        # 4. Retrieve recent history and build prompt
        recent_history = MemoryService.get_recent_history(db, request.conversation_id)
        previous_messages = recent_history[:-1] if len(recent_history) > 0 else []
        current_message = recent_history[-1].content if len(recent_history) > 0 else request.message

        prompt_messages = PromptService.build_prompt(
            history=previous_messages,
            summary=conversation.summary,
            current_user_message=current_message,
            retrieved_knowledge=retrieved_knowledge,
            graph_knowledge=graph_knowledge,
        )

        # 5. Generate response using the AIService
        ai_reply = AIService.generate_response(prompt_messages)

        # 6. Save assistant reply to database
        assistant_message_obj = Message(
            conversation_id=request.conversation_id,
            role="assistant",
            content=ai_reply
        )
        MessageRepository.create(db, assistant_message_obj)

        # 7. Update conversation memory summaries if needed
        MemoryService.update_memory(db, conversation)

        return ChatResponse(
            user_message=user_message_obj,
            assistant_message=assistant_message_obj,
            conversation_id=request.conversation_id
        )

    @staticmethod
    def handle_chat_stream(db: Session, user_id: int, request: ChatRequest):
        """
        Validates conversation ownership, runs Hybrid RAG retrieval, stores user prompt,
        and returns a generator yielding SSE chunks.
        """
        import json

        # 1. Validate conversation exists and is owned by the user
        conversation = ConversationRepository.get_by_id(db, request.conversation_id)
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        if conversation.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have access to this conversation"
            )

        # 2. Save user message immediately
        user_message_obj = Message(
            conversation_id=request.conversation_id,
            role="user",
            content=request.message
        )
        MessageRepository.create(db, user_message_obj)

        # 3. Hybrid RAG Retrieval — graceful fallback
        retrieved_knowledge = ""
        graph_knowledge = ""
        if request.workspace_id:
            try:
                from app.config import settings
                from app.services.adaptive_retrieval_service import AdaptiveRetrievalService
                rag_context = AdaptiveRetrievalService.retrieve_context(
                    db=db,
                    user_query=request.message,
                    workspace_id=request.workspace_id,
                    knowledge_base_id=request.knowledge_base_id,
                    top_k=settings.RAG_TOP_K,
                    similarity_threshold=settings.SIMILARITY_THRESHOLD,
                    max_context_tokens=settings.MAX_CONTEXT_TOKENS,
                    enable_reranking=settings.ENABLE_RERANKING,
                )
                if rag_context.has_knowledge:
                    retrieved_knowledge = rag_context.formatted_context
                    graph_knowledge = rag_context.graph_context or ""
                    logger.info(
                        f"RAG (stream) injected {rag_context.metrics.retrieved_count} chunks | "
                        f"Graph connections: {graph_knowledge} | "
                        f"Confidence: {rag_context.confidence_score} | "
                        f"latency={rag_context.metrics.latency_ms:.1f}ms"
                    )
            except Exception as e:
                logger.error(f"RAG retrieval failed in stream — continuing: {e}")

        # 4. Retrieve recent history and build prompt
        recent_history = MemoryService.get_recent_history(db, request.conversation_id)
        previous_messages = recent_history[:-1] if len(recent_history) > 0 else []
        current_message = recent_history[-1].content if len(recent_history) > 0 else request.message

        prompt_messages = PromptService.build_prompt(
            history=previous_messages,
            summary=conversation.summary,
            current_user_message=current_message,
            retrieved_knowledge=retrieved_knowledge,
            graph_knowledge=graph_knowledge,
        )

        # 5. Define streaming generator
        def stream_generator():
            accumulated_content = ""
            try:
                for token in AIService.generate_stream_response(prompt_messages):
                    accumulated_content += token
                    yield f"data: {json.dumps({'content': token})}\n\n"

                # Stream complete — save reply and update memory using a fresh database session
                if accumulated_content:
                    from app.db.database import SessionLocal
                    from app.repositories.conversation_repository import ConversationRepository
                    with SessionLocal() as fresh_db:
                        assistant_message_obj = Message(
                            conversation_id=request.conversation_id,
                            role="assistant",
                            content=accumulated_content
                        )
                        MessageRepository.create(fresh_db, assistant_message_obj)
                        
                        # Retrieve conversation from the active session context
                        fresh_convo = ConversationRepository.get_by_id(fresh_db, request.conversation_id)
                        MemoryService.update_memory(fresh_db, fresh_convo)
            except Exception as e:
                logger.error(f"Error in stream generator pipeline: {e}", exc_info=True)
                yield f"data: {json.dumps({'error': str(e)})}\n\n"

        return stream_generator()
