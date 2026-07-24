import logging
import json
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.message import Message
from app.repositories.conversation_repository import ConversationRepository
from app.repositories.message_repository import MessageRepository
from app.services.ai_service import AIService
from app.services.memory_service import MemoryService
from app.services.prompt_service import PromptService
from app.services.prompt.prompt_builder import PromptBuilder
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
        3. Dynamic Qdrant RAG retrieval (if grounded is enabled)
        4. Build secure prompt with PromptBuilder injection protection
        5. Generate AI response
        6. Save assistant reply with citations
        """
        # 1. Validate conversation
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

        # Validate workspace membership if workspace is associated
        ws_id = conversation.workspace_id or request.workspace_id
        if ws_id:
            from app.services.permission_service import PermissionService
            PermissionService.get_member_role(db, user_id, ws_id)

        # 2. Save user message
        user_message_obj = Message(
            conversation_id=request.conversation_id,
            role="user",
            content=request.message
        )
        MessageRepository.create(db, user_message_obj)

        # 3. Grounded retrieval
        retrieved_knowledge = ""
        graph_knowledge = ""
        sources_list = []

        if request.grounded and request.workspace_id:
            kb_ids = request.knowledge_base_ids or (
                [request.knowledge_base_id] if request.knowledge_base_id else None
            )
            print(f"\n>>> [SYNC CHAT] QUERY: '{request.message}' | Grounded: {request.grounded} | Workspace: {request.workspace_id} | KBs: {kb_ids} <<<")
            try:
                from app.config import settings
                from app.services.adaptive_retrieval_service import AdaptiveRetrievalService
                
                rag_context = AdaptiveRetrievalService.retrieve_context(
                    db=db,
                    user_query=request.message,
                    workspace_id=request.workspace_id,
                    knowledge_base_id=kb_ids,
                    top_k=settings.RAG_TOP_K,
                    similarity_threshold=settings.SIMILARITY_THRESHOLD,
                    max_context_tokens=settings.MAX_CONTEXT_TOKENS,
                    enable_reranking=settings.ENABLE_RERANKING,
                    user_id=user_id,
                )

                # Fallback: if 0 chunks found with strict threshold, retry with low threshold to ensure PDF text reaches LLM
                if not rag_context.has_knowledge:
                    rag_context = AdaptiveRetrievalService.retrieve_context(
                        db=db,
                        user_query=request.message,
                        workspace_id=request.workspace_id,
                        knowledge_base_id=kb_ids,
                        top_k=settings.RAG_TOP_K,
                        similarity_threshold=0.01,
                        max_context_tokens=settings.MAX_CONTEXT_TOKENS,
                        enable_reranking=False,
                        user_id=user_id,
                    )

                print(f">>> [SYNC CHAT] RAG retrieved {len(rag_context.chunks_used)} chunks. Has knowledge: {rag_context.has_knowledge} <<<")
                if rag_context.has_knowledge:
                    retrieved_knowledge = rag_context.formatted_context
                    graph_knowledge = rag_context.graph_context or ""
                    
                    # Extract sources and confidence metrics
                    for chunk in rag_context.chunks_used:
                        sources_list.append({
                            "filename": chunk.doc_filename or "document",
                            "page": chunk.page or 1,
                            "section": chunk.section or "",
                            "score": round(chunk.score, 4),
                            "confidence": int(chunk.score * 100)
                        })

                    logger.info(
                        f"RAG sync injected {len(sources_list)} chunks | "
                        f"latency={rag_context.metrics.latency_ms:.1f}ms"
                    )
            except Exception as e:
                print(f">>> [SYNC CHAT] RAG ERROR: {e} <<<")
                import traceback
                traceback.print_exc()
                logger.error(f"RAG retrieval failed — continuing without knowledge: {e}")

        # 4. Build prompt using PromptService + PromptBuilder
        recent_history = MemoryService.get_recent_history(db, request.conversation_id)
        previous_messages = recent_history[:-1] if len(recent_history) > 0 else []
        current_message = recent_history[-1].content if len(recent_history) > 0 else request.message

        prompt_messages = PromptService.build_prompt(
            history=previous_messages,
            summary=conversation.summary,
            current_user_message=current_message,
            retrieved_knowledge=retrieved_knowledge,
            graph_knowledge=graph_knowledge,
            grounded=request.grounded,
        )

        # 5. Generate AI reply
        ai_reply = AIService.generate_response(prompt_messages, provider_override=request.provider)

        # 6. Save assistant reply to database
        assistant_message_obj = Message(
            conversation_id=request.conversation_id,
            role="assistant",
            content=ai_reply,
            sources=sources_list if request.grounded else None
        )
        MessageRepository.create(db, assistant_message_obj)

        # 7. Update conversation memory
        MemoryService.update_memory(db, conversation)

        return ChatResponse(
            user_message=user_message_obj,
            assistant_message=assistant_message_obj,
            conversation_id=request.conversation_id
        )

    @staticmethod
    def handle_chat_stream(db: Session, user_id: int, request: ChatRequest):
        """
        Streaming chat pipeline:
        1. Validate conversation
        2. Save user message
        3. Dynamic RAG retrieval (if grounded is enabled)
        4. Yield references at stream start, stream token completions, and save final payload.
        """
        # 1. Validate conversation
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

        # Validate workspace membership if workspace is associated
        ws_id = conversation.workspace_id or request.workspace_id
        if ws_id:
            from app.services.permission_service import PermissionService
            PermissionService.get_member_role(db, user_id, ws_id)

        # 2. Save user message
        user_message_obj = Message(
            conversation_id=request.conversation_id,
            role="user",
            content=request.message
        )
        MessageRepository.create(db, user_message_obj)

        # 3. Grounded retrieval
        retrieved_knowledge = ""
        graph_knowledge = ""
        sources_list = []

        if request.grounded and request.workspace_id:
            kb_ids = request.knowledge_base_ids or (
                [request.knowledge_base_id] if request.knowledge_base_id else None
            )
            print(f"\n>>> [STREAM CHAT] QUERY: '{request.message}' | Grounded: {request.grounded} | Workspace: {request.workspace_id} | KBs: {kb_ids} <<<")
            try:
                from app.config import settings
                from app.services.adaptive_retrieval_service import AdaptiveRetrievalService

                rag_context = AdaptiveRetrievalService.retrieve_context(
                    db=db,
                    user_query=request.message,
                    workspace_id=request.workspace_id,
                    knowledge_base_id=kb_ids,
                    top_k=settings.RAG_TOP_K,
                    similarity_threshold=settings.SIMILARITY_THRESHOLD,
                    max_context_tokens=settings.MAX_CONTEXT_TOKENS,
                    enable_reranking=settings.ENABLE_RERANKING,
                    user_id=user_id,
                )

                print(f">>> [STREAM CHAT] RAG retrieved {len(rag_context.chunks_used)} chunks. Has knowledge: {rag_context.has_knowledge} <<<")
                if rag_context.has_knowledge:
                    retrieved_knowledge = rag_context.formatted_context
                    graph_knowledge = rag_context.graph_context or ""

                    # Extract sources
                    for chunk in rag_context.chunks_used:
                        sources_list.append({
                            "filename": chunk.doc_filename or "document",
                            "page": chunk.page or 1,
                            "section": chunk.section or "",
                            "score": round(chunk.score, 4),
                            "confidence": int(chunk.score * 100)
                        })

                    logger.info(
                        f"RAG stream injected {len(sources_list)} chunks | "
                        f"latency={rag_context.metrics.latency_ms:.1f}ms"
                    )
            except Exception as e:
                print(f">>> [STREAM CHAT] RAG ERROR: {e} <<<")
                import traceback
                traceback.print_exc()
                logger.error(f"RAG retrieval failed in stream — continuing: {e}")

        # 4. Build prompt
        recent_history = MemoryService.get_recent_history(db, request.conversation_id)
        previous_messages = recent_history[:-1] if len(recent_history) > 0 else []
        current_message = recent_history[-1].content if len(recent_history) > 0 else request.message

        prompt_messages = PromptService.build_prompt(
            history=previous_messages,
            summary=conversation.summary,
            current_user_message=current_message,
            retrieved_knowledge=retrieved_knowledge,
            graph_knowledge=graph_knowledge,
            grounded=request.grounded,
        )

        # 5. Yield dynamic token streams directly to the StreamingResponse
        def direct_generator():
            accumulated_content = ""
            try:
                # Yield citations meta chunk at stream start
                if request.grounded and sources_list:
                    yield f"data: {json.dumps({'sources': sources_list})}\n\n"

                for token in AIService.generate_stream_response(prompt_messages, provider_override=request.provider):
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
                            content=accumulated_content,
                            sources=sources_list if request.grounded else None
                        )
                        MessageRepository.create(fresh_db, assistant_message_obj)
                        
                        fresh_convo = ConversationRepository.get_by_id(fresh_db, request.conversation_id)
                        MemoryService.update_memory(fresh_db, fresh_convo)
            except Exception as e:
                logger.error(f"Error in stream generator pipeline: {e}", exc_info=True)
                yield f"data: {json.dumps({'error': str(e)})}\n\n"

        return direct_generator()

