"""
Evaluation & AI Replay API Endpoints — Volume 4

Routes:
  POST /eval/feedback                  — Submit chat thumbs rating + run LLM-as-a-judge
  GET  /eval/dashboard                 — Fetch average faithfulness, confidence, and latency KPIs
  GET  /eval/review-queue              — List pending review requests
  POST /eval/review/{id}/status        — Update review status (approve/reject)
  GET  /eval/export/{format}           — Download dataset as jsonl or csv
  POST /eval/replay/{id}               — Replay sandbox executor: rerun original prompt
"""
import os
import json
import logging
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.responses import Response, StreamingResponse
from sqlalchemy.orm import Session
from typing import Dict, Any, List

from app.db.session import get_db
from app.models.user import User
from app.security.dependencies import get_current_user
from app.models.chat_feedback import ChatFeedback
from app.models.message import Message
from app.services.eval.evaluator import EvaluationService
from app.services.eval.dataset_builder import DatasetBuilder, JSONL_PATH
from app.schemas.eval import FeedbackSubmitRequest, EvalMetricsSummary, TuningCandidateResponse

router = APIRouter(
    prefix="/eval",
    tags=["AI Model Evaluation"],
)

logger = logging.getLogger("app.api.v1.endpoints.eval")


def _run_judge_evaluation(feedback_id: int, query: str, response: str, chunks: List[str], db_session_factory):
    """
    Background worker task to calculate evaluation metrics.
    Avoids blocking API responses for client rating submission.
    """
    db = db_session_factory()
    try:
        scores = EvaluationService.evaluate_response(query, response, chunks)
        feedback = db.query(ChatFeedback).filter(ChatFeedback.id == feedback_id).first()
        if feedback:
            feedback.faithfulness = scores.get("faithfulness", 0.85)
            feedback.answer_relevance = scores.get("answer_relevance", 0.80)
            feedback.context_recall = scores.get("context_recall", 0.85)
            feedback.hallucination_score = scores.get("hallucination_score", 0.15)
            feedback.confidence_score = scores.get("confidence_score", 0.80)
            feedback.priority = scores.get("priority", "LOW")
            feedback.root_cause = scores.get("root_cause", "None")
            feedback.domain_tag = scores.get("domain_tag", "General Analytics")
            
            # Save query hash
            feedback.query_hash = DatasetBuilder.calculate_hash(query, response)

            db.commit()
            logger.info(f"[EvaluationBackground] Feedback ID {feedback_id} scores updated: {scores}")
    except Exception as e:
        logger.error(f"[EvaluationBackground] Evaluation worker failed: {e}")
        db.rollback()
    finally:
        db.close()


@router.post(
    "/feedback",
    response_model=Dict[str, Any],
    summary="Submit user thumbs feedback on chat message and trigger LLM judge evaluation",
)
def submit_chat_feedback(
    payload: FeedbackSubmitRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    msg = db.query(Message).filter(Message.id == payload.message_id).first()
    if not msg:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Target chat message not found."
        )

    # Save feedback + replay payloads
    feedback = ChatFeedback(
        user_id=current_user.id,
        conversation_id=msg.conversation_id,
        message_id=msg.id,
        thumbs_up=payload.thumbs_up,
        thumbs_down=payload.thumbs_down,
        feedback=payload.feedback_text,
        response_time_ms=payload.response_time_ms,
        
        # Save exact execution states for replay sandbox debugs
        replay_query=payload.original_query,
        replay_prompt=payload.prompt_text,
        replay_chunks=json.dumps(payload.context_chunks)
    )
    db.add(feedback)
    db.commit()
    db.refresh(feedback)

    # Dispatch metrics calculation in background thread
    from app.db.session import SessionLocal
    background_tasks.add_task(
        _run_judge_evaluation,
        feedback.id,
        payload.original_query,
        msg.content,
        payload.context_chunks,
        SessionLocal
    )

    return {"success": True, "feedback_id": feedback.id, "message": "Feedback submitted successfully."}


@router.get(
    "/dashboard",
    response_model=EvalMetricsSummary,
    summary="Get aggregated AI evaluation metrics and satisfaction rates",
)
def get_eval_dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    feedbacks = db.query(ChatFeedback).filter(ChatFeedback.faithfulness.isnot(None)).all()
    
    total = len(feedbacks)
    dataset_size = 0
    if os.path.exists(JSONL_PATH):
        try:
            dataset_size = os.path.getsize(JSONL_PATH)
        except Exception:
            pass

    if total == 0:
        return EvalMetricsSummary(
            avg_faithfulness=0.0,
            avg_relevance=0.0,
            avg_recall=0.0,
            avg_hallucination=0.0,
            avg_confidence=0.0,
            avg_latency_ms=0.0,
            satisfaction_rate=0.0,
            positive_feedback_count=0,
            negative_feedback_count=0,
            pending_reviews_count=0,
            approved_samples_count=0,
            rejected_samples_count=0,
            dataset_size_bytes=dataset_size,
            current_model_version="nexora-v1"
        )

    # Calculations
    faith_sum = sum(fb.faithfulness for fb in feedbacks)
    rel_sum = sum(fb.answer_relevance for fb in feedbacks)
    rec_sum = sum(fb.context_recall for fb in feedbacks)
    hal_sum = sum(fb.hallucination_score for fb in feedbacks)
    conf_sum = sum(fb.confidence_score for fb in feedbacks)
    
    # Latency calculations
    latency_records = [fb.response_time_ms for fb in feedbacks if fb.response_time_ms is not None]
    avg_latency = sum(latency_records) / len(latency_records) if latency_records else 2100.0

    pos_ratings = sum(1 for fb in feedbacks if fb.thumbs_up)
    neg_ratings = sum(1 for fb in feedbacks if fb.thumbs_down)
    satisfaction = round((pos_ratings / total) * 100, 1) if total > 0 else 0.0

    pending = db.query(ChatFeedback).filter(ChatFeedback.review_status == "pending").count()
    approved = db.query(ChatFeedback).filter(ChatFeedback.review_status == "approved").count()
    rejected = db.query(ChatFeedback).filter(ChatFeedback.review_status == "rejected").count()

    return EvalMetricsSummary(
        avg_faithfulness=round(faith_sum / total, 2),
        avg_relevance=round(rel_sum / total, 2),
        avg_recall=round(rec_sum / total, 2),
        avg_hallucination=round(hal_sum / total, 2),
        avg_confidence=round(conf_sum / total, 2),
        avg_latency_ms=round(avg_latency, 1),
        satisfaction_rate=satisfaction,
        positive_feedback_count=pos_ratings,
        negative_feedback_count=neg_ratings,
        pending_reviews_count=pending,
        approved_samples_count=approved,
        rejected_samples_count=rejected,
        dataset_size_bytes=dataset_size,
        current_model_version="nexora-v1"
    )


@router.get(
    "/review-queue",
    response_model=List[TuningCandidateResponse],
    summary="Retrieve feedbacks waiting in the Human Review queue",
)
def get_review_queue(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    print(">>> GET /eval/review-queue called")
    candidates = db.query(ChatFeedback).filter(ChatFeedback.review_status == "pending").all()
    print(f">>> Found {len(candidates)} pending candidates in DB")
    res = []
    for c in candidates:
        try:
            msg = db.query(Message).filter(Message.id == c.message_id).first()
            created_str = ""
            if c.created_at:
                try:
                    created_str = c.created_at.strftime("%Y-%m-%d %H:%M")
                except Exception:
                    created_str = str(c.created_at)

            res.append(TuningCandidateResponse(
                id=c.id,
                query=c.replay_query or "Unknown Query",
                original_response=msg.content if msg else "No Response Content",
                faithfulness=c.faithfulness or 0.0,
                hallucination_score=c.hallucination_score or 0.0,
                confidence_score=c.confidence_score or 0.0,
                priority=c.priority or "LOW",
                review_status=c.review_status or "pending",
                root_cause=c.root_cause or "None",
                domain_tag=c.domain_tag or "General",
                model_version=c.model_version or "nexora-v1",
                rag_pipeline_version=c.rag_pipeline_version or "rag-v2.1",
                created_at=created_str
            ))
        except Exception as item_err:
            print(f"Error parsing candidate {c.id}: {item_err}")
    return res


@router.post(
    "/review/{feedback_id}/status",
    response_model=Dict[str, Any],
    summary="Update feedback status (approve/reject) in Human Review Queue",
)
def update_review_status(
    feedback_id: int,
    status_value: str, # "approved" or "rejected"
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if status_value not in ["approved", "rejected"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Status must be 'approved' or 'rejected'."
        )

    fb = db.query(ChatFeedback).filter(ChatFeedback.id == feedback_id).first()
    if not fb:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feedback record not found."
        )

    fb.review_status = status_value
    fb.reviewed_at = datetime.utcnow()

    # If approved, run dataset builder (adds to JSONL file)
    if status_value == "approved":
        msg = db.query(Message).filter(Message.id == fb.message_id).first()
        response_text = msg.content if msg else ""
        chunks_list = json.loads(fb.replay_chunks or "[]")
        
        meta = {
            "model_version": fb.model_version,
            "dataset_version": fb.dataset_version,
            "rag_pipeline_version": fb.rag_pipeline_version,
            "confidence": fb.confidence_score,
            "hallucination": fb.hallucination_score,
            "domain_tag": fb.domain_tag,
            "root_cause": fb.root_cause
        }
        
        appended = DatasetBuilder.append_to_jsonl(
            fb.id,
            fb.replay_query or "",
            response_text,
            chunks_list,
            meta
        )
        fb.is_flagged_for_tuning = appended

    db.commit()
    return {"success": True, "feedback_id": fb.id, "review_status": fb.review_status}


@router.get(
    "/export/{format_type}",
    summary="Download compiled tuning dataset in jsonl or csv format",
)
def download_tuning_dataset(
    format_type: str, # "jsonl" or "csv"
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if format_type not in ["jsonl", "csv"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Format must be 'jsonl' or 'csv'."
        )

    if format_type == "jsonl":
        if not os.path.exists(JSONL_PATH):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No approved dataset generated yet."
            )
        # Return static streaming response
        file_like = open(JSONL_PATH, mode="rb")
        return StreamingResponse(
            file_like,
            media_type="application/jsonlines",
            headers={"Content-Disposition": "attachment; filename=tuning_queue.jsonl"}
        )

    # For CSV format, query approved candidates in the DB and assemble bytes
    records = db.query(ChatFeedback).filter(ChatFeedback.review_status == "approved").all()
    rows = []
    for r in records:
        msg = db.query(Message).filter(Message.id == r.message_id).first()
        rows.append({
            "id": f"sample_{r.id}",
            "query": r.replay_query,
            "response": msg.content if msg else "",
            "domain_tag": r.domain_tag,
            "root_cause": r.root_cause,
            "faithfulness": r.faithfulness,
            "hallucination": r.hallucination_score,
            "confidence": r.confidence_score,
            "priority": r.priority,
            "model_version": r.model_version,
            "rag_pipeline_version": r.rag_pipeline_version
        })

    csv_data = DatasetBuilder.compile_csv_bytes(rows)
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=tuning_queue.csv"}
    )


@router.post(
    "/replay/{feedback_id}",
    response_model=Dict[str, Any],
    summary="Replay Sandbox: reruns original prompt and compares outputs",
)
def execute_replay_sandbox(
    feedback_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    fb = db.query(ChatFeedback).filter(ChatFeedback.id == feedback_id).first()
    if not fb:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Target feedback session not found."
        )

    original_prompt = fb.replay_prompt
    if not original_prompt:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot replay: Original prompt context was not recorded."
        )

    orig_msg = db.query(Message).filter(Message.id == fb.message_id).first()
    original_response = orig_msg.content if orig_msg else ""

    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="OpenAI API key missing. Cannot run live replay."
        )

    try:
        import openai
        client = openai.OpenAI(api_key=api_key)

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": original_prompt}],
            max_tokens=1024,
            temperature=0.2
        )
        new_response = response.choices[0].message.content or ""

        chunks_list = json.loads(fb.replay_chunks or "[]")
        scores = EvaluationService.evaluate_response(fb.replay_query, new_response, chunks_list)

        return {
            "success": True,
            "query": fb.replay_query,
            "original_response": original_response,
            "new_response": new_response,
            "original_scores": {
                "faithfulness": fb.faithfulness,
                "answer_relevance": fb.answer_relevance
            },
            "new_scores": {
                "faithfulness": scores.get("faithfulness", 0.85),
                "answer_relevance": scores.get("answer_relevance", 0.80)
            }
        }
    except Exception as e:
        logger.error(f"[ReplaySandbox] Execution failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Replay compilation error: {str(e)}"
        )


@router.get("/debug-db")
def debug_db(db: Session = Depends(get_db)):
    feedbacks = db.query(ChatFeedback).all()
    res = []
    for f in feedbacks:
        res.append({
            "id": f.id,
            "message_id": f.message_id,
            "thumbs_up": f.thumbs_up,
            "thumbs_down": f.thumbs_down,
            "review_status": f.review_status,
            "created_at": str(f.created_at) if f.created_at else None,
            "replay_query": f.replay_query,
            "faithfulness": f.faithfulness,
            "hallucination_score": f.hallucination_score
        })
    return res
