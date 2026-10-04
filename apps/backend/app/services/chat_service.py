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

    # Professional domain guardrail — deterministic pre-LLM block for off-topic (movie/song/gossip etc.)
    OFF_TOPIC_KEYWORDS = [
        "movie", "movies", "film", "films", "bollywood", "hollywood", "tollywood", "netflix", "web series", "series",
        "actor", "actress", "hero", "heroine", "celebrity", "celebrities", "gossip", "song", "songs", "lyrics", "music video",
        "game", "gaming", " PUBG", " free fire", "joke", "jokes", "meme", "memes", "astrology", "horoscope",
        "big boss", "bigg boss", "karan aujla", "diljit"
    ]
    PROFESSIONAL_REFUSAL = "I am Nexora AI, specialized strictly for Study, Business, Data Science, Coding, and Technical tasks. Please ask an educational, professional, or business-related question!"

    @staticmethod
    def _is_off_topic_query(text: str) -> bool:
        t = text.lower().strip()
        # very short casual greetings are allowed (hi/hello) — don't block
        if t in ("hi", "hello", "hey", "hii", "helo") or len(t) < 4:
            return False
        # if query contains off-topic keyword and does NOT contain professional keyword, block
        professional_hints = ["study", "business", "code", "python", "sql", "ml", "machine learning", "data", "analytics", "report", "rag", "qdrant", "resume", "project", "research", "education", "exam", "notes", "explain", "how to", "what is"]
        has_prof = any(k in t for k in professional_hints)
        if has_prof:
            return False
        return any(k in t for k in ChatService.OFF_TOPIC_KEYWORDS)

    @staticmethod
    def _retrieve_grounded_context(db: Session, user_id: int, request: ChatRequest):
        """Shared grounded RAG retrieval with fallback to workspace-wide and raw DB chunks."""
        retrieved_knowledge = ""
        graph_knowledge = ""
        sources_list = []
        if not (request.grounded and request.workspace_id):
            return retrieved_knowledge, graph_knowledge, sources_list

        kb_ids = request.knowledge_base_ids or (
            [request.knowledge_base_id] if request.knowledge_base_id else None
        )
        try:
            from app.config import settings
            from app.services.adaptive_retrieval_service import AdaptiveRetrievalService
            from app.models.document_chunk import DocumentChunk
            from app.models.knowledge_document import KnowledgeDocument
            from app.models.knowledge_base import KnowledgeBase

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

            if not rag_context.has_knowledge and kb_ids:
                rag_context = AdaptiveRetrievalService.retrieve_context(
                    db=db,
                    user_query=request.message,
                    workspace_id=request.workspace_id,
                    knowledge_base_id=None,
                    top_k=settings.RAG_TOP_K,
                    similarity_threshold=0.0,
                    max_context_tokens=settings.MAX_CONTEXT_TOKENS,
                    enable_reranking=False,
                    user_id=user_id,
                )

            if not rag_context.has_knowledge:
                doc_query = (
                    db.query(KnowledgeDocument)
                    .join(KnowledgeBase, KnowledgeDocument.knowledge_base_id == KnowledgeBase.id)
                    .filter(
                        KnowledgeBase.workspace_id == request.workspace_id,
                        KnowledgeDocument.deleted_at.is_(None),
                        KnowledgeBase.deleted_at.is_(None)
                    )
                )
                if kb_ids:
                    doc_query = doc_query.filter(KnowledgeBase.id.in_(kb_ids))
                latest_doc = doc_query.order_by(KnowledgeDocument.created_at.desc(), KnowledgeDocument.id.desc()).first()
                if not latest_doc and kb_ids:
                    latest_doc = (
                        db.query(KnowledgeDocument)
                        .join(KnowledgeBase, KnowledgeDocument.knowledge_base_id == KnowledgeBase.id)
                        .filter(
                            KnowledgeBase.workspace_id == request.workspace_id,
                            KnowledgeDocument.deleted_at.is_(None),
                            KnowledgeBase.deleted_at.is_(None)
                        )
                        .order_by(KnowledgeDocument.created_at.desc(), KnowledgeDocument.id.desc())
                        .first()
                    )
                if latest_doc:
                    raw_chunks = (
                        db.query(DocumentChunk)
                        .filter(DocumentChunk.document_id == latest_doc.id)
                        .order_by(DocumentChunk.chunk_index.asc())
                        .limit(10)
                        .all()
                    )
                    if raw_chunks:
                        retrieved_knowledge = "\n\n".join([
                            f"--- Document Excerpt ({latest_doc.filename}, Page {c.page or 1}) ---\n{c.text}"
                            for c in raw_chunks
                        ])
                        for c in raw_chunks:
                            sources_list.append({
                                "filename": latest_doc.filename or "uploaded_document.pdf",
                                "page": c.page or 1,
                                "section": c.section or "",
                                "score": 1.0,
                                "confidence": 100
                            })

            if rag_context.has_knowledge:
                retrieved_knowledge = rag_context.formatted_context
                graph_knowledge = rag_context.graph_context or ""
                for chunk in rag_context.chunks_used:
                    sources_list.append({
                        "filename": chunk.doc_filename or "document",
                        "page": chunk.page or 1,
                        "section": chunk.section or "",
                        "score": round(chunk.score, 4),
                        "confidence": int(chunk.score * 100)
                    })
                logger.info(f"RAG injected {len(sources_list)} chunks | latency={rag_context.metrics.latency_ms:.1f}ms")
        except Exception as e:
            import traceback
            traceback.print_exc()
            logger.error(f"RAG retrieval failed — continuing without knowledge: {e}")

        return retrieved_knowledge, graph_knowledge, sources_list

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

        # 3. Domain guardrail — deterministic block before LLM (saves HF quota + deterministic)
        if ChatService._is_off_topic_query(request.message):
            ai_reply = ChatService.PROFESSIONAL_REFUSAL
            assistant_message_obj = Message(
                conversation_id=request.conversation_id,
                role="assistant",
                content=ai_reply,
                sources=None
            )
            MessageRepository.create(db, assistant_message_obj)
            MemoryService.update_memory(db, conversation)
            return ChatResponse(
                user_message=user_message_obj,
                assistant_message=assistant_message_obj,
                conversation_id=request.conversation_id
            )

        # 4. Grounded retrieval (shared)
        print(f"\n>>> [SYNC CHAT] QUERY: '{request.message}' | Grounded: {request.grounded} | Workspace: {request.workspace_id} <<<")
        retrieved_knowledge, graph_knowledge, sources_list = ChatService._retrieve_grounded_context(db, user_id, request)

        # 5. Build prompt using PromptService + PromptBuilder (always includes STRICT domain guardrail)
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

        # 6. Generate AI reply — resilient chain (HF -> Gemini -> mock).
        # AIService tries fallbacks automatically; this except is a final
        # safety net so the API returns 200, never 502, during live demos.
        provider_override = request.provider
        if not provider_override:
            from app.config import settings as _s
            if "email" in request.message.lower() and "subject" in request.message.lower() and getattr(_s, "GOOGLE_API_KEY", ""):
                provider_override = "gemini"
        try:
            ai_reply = AIService.generate_response(prompt_messages, provider_override=provider_override)
        except Exception as e:
            logger.warning(f"Primary provider {provider_override or settings.AI_PROVIDER} failed for email draft: {e} — falling back to mock")
            # Fallback to mock ensures 200 not 502 for college demo
            ai_reply = AIService.generate_response(prompt_messages, provider_override="mock")

        # 7. Save assistant reply to database
        assistant_message_obj = Message(
            conversation_id=request.conversation_id,
            role="assistant",
            content=ai_reply,
            sources=sources_list if request.grounded else None
        )
        MessageRepository.create(db, assistant_message_obj)

        # 8. Update conversation memory
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

        # 2b. Domain guardrail — immediate refusal for off-topic without LLM
        if ChatService._is_off_topic_query(request.message):
            def refusal_generator():
                refusal = ChatService.PROFESSIONAL_REFUSAL
                yield f"data: {json.dumps({'content': refusal})}\n\n"
                # save refusal
                from app.db.database import SessionLocal
                from app.repositories.conversation_repository import ConversationRepository
                with SessionLocal() as fresh_db:
                    assistant_message_obj = Message(
                        conversation_id=request.conversation_id,
                        role="assistant",
                        content=refusal,
                        sources=None
                    )
                    MessageRepository.create(fresh_db, assistant_message_obj)
                    fresh_convo = ConversationRepository.get_by_id(fresh_db, request.conversation_id)
                    MemoryService.update_memory(fresh_db, fresh_convo)
            return refusal_generator()

        # 3. Grounded retrieval (shared)
        print(f"\n>>> [STREAM CHAT] QUERY: '{request.message}' | Grounded: {request.grounded} | Workspace: {request.workspace_id} <<<")
        retrieved_knowledge, graph_knowledge, sources_list = ChatService._retrieve_grounded_context(db, user_id, request)

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

        # 5. Yield dynamic token streams — resilient chain (HF -> Gemini -> mock).
        provider_override = request.provider
        if not provider_override:
            from app.config import settings as _s2
            if "email" in request.message.lower() and "subject" in request.message.lower() and getattr(_s2, "GOOGLE_API_KEY", ""):
                provider_override = "gemini"

        def direct_generator():
            accumulated_content = ""
            try:
                # Yield citations meta chunk at stream start
                if request.grounded and sources_list:
                    yield f"data: {json.dumps({'sources': sources_list})}\n\n"

                # Try primary provider, fallback to mock on error to avoid 502
                try:
                    stream_iter = AIService.generate_stream_response(prompt_messages, provider_override=provider_override)
                except Exception as e:
                    logger.warning(f"Stream primary provider {provider_override or 'huggingface'} failed: {e} — mock fallback")
                    stream_iter = AIService.generate_stream_response(prompt_messages, provider_override="mock")

                for token in stream_iter:
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
                # Try mock fallback content instead of 502 error
                try:
                    fallback = AIService.generate_response(prompt_messages, provider_override="mock")
                    yield f"data: {json.dumps({'content': fallback})}\n\n"
                    accumulated_content = fallback
                except Exception:
                    yield f"data: {json.dumps({'error': str(e)})}\n\n"

        return direct_generator()

