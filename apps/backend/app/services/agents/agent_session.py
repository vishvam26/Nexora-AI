"""
AgentSession — Step 11 Multi-Agent Orchestration

Persistent audit trail for every agent orchestration run.
Each session records:
  - The CEO's original question
  - Manager's execution plan
  - Every agent's result (status, output, summary, latency)
  - Final synthesized answer
  - Total latency

Stored as JSON files at: storage/agent_sessions/{session_id}.json
An index file at: storage/agent_sessions/index.json tracks recent sessions.

Design: JSON on disk (no DB migration needed). Can be migrated to PostgreSQL
in Step 12 for multi-user concurrent session management.
"""
import os
import json
import time
import uuid
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger("app.services.agents.agent_session")

SESSION_DIR = os.path.join("storage", "agent_sessions")
INDEX_PATH = os.path.join(SESSION_DIR, "index.json")
MAX_INDEX_ENTRIES = 100  # Keep last 100 sessions in index

os.makedirs(SESSION_DIR, exist_ok=True)


class AgentSession:
    """
    Manages creation, persistence, and retrieval of agent orchestration sessions.
    """

    @classmethod
    def create(
        cls,
        question: str,
        workspace_id: Optional[int],
        doc_id: Optional[int],
    ) -> Dict[str, Any]:
        """
        Creates a new session dict with a unique ID.
        Returns the mutable session dict — caller updates it and calls save().
        """
        session_id = f"agt_{uuid.uuid4().hex[:12]}_{int(time.time())}"
        session = {
            "session_id": session_id,
            "question": question,
            "workspace_id": workspace_id,
            "doc_id": doc_id,
            "status": "running",
            "plan": [],               # List of planned agent steps
            "agent_results": [],      # List of AgentResult dicts
            "final_answer": "",
            "citations": [],
            "confidence": 0.0,
            "total_latency_ms": 0,
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "completed_at": None,
        }
        logger.info(f"[AgentSession] Created session: {session_id}")
        return session

    @classmethod
    def save(cls, session: Dict[str, Any]) -> str:
        """
        Persists session to disk and updates the index.
        Returns the session_id.
        """
        session_id = session["session_id"]
        path = os.path.join(SESSION_DIR, f"{session_id}.json")

        with open(path, "w", encoding="utf-8") as f:
            json.dump(session, f, indent=2, default=str)

        # Update index
        cls._update_index(session_id, session)
        return session_id

    @classmethod
    def get(cls, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Loads a session by ID from disk.
        Returns None if not found.
        """
        path = os.path.join(SESSION_DIR, f"{session_id}.json")
        if not os.path.exists(path):
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"[AgentSession] Failed to load {session_id}: {e}")
            return None

    @classmethod
    def list_recent(cls, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Returns the most recent `limit` sessions from the index (summary view).
        Does not load full session data to keep the list response compact.
        """
        if not os.path.exists(INDEX_PATH):
            return []
        try:
            with open(INDEX_PATH, "r", encoding="utf-8") as f:
                index = json.load(f)
            return index[:limit]
        except Exception:
            return []

    @classmethod
    def _update_index(cls, session_id: str, session: Dict[str, Any]) -> None:
        """Maintains a rolling index of recent sessions."""
        index: List[Dict[str, Any]] = []
        if os.path.exists(INDEX_PATH):
            try:
                with open(INDEX_PATH, "r", encoding="utf-8") as f:
                    index = json.load(f)
            except Exception:
                index = []

        # Summary entry for the index
        summary = {
            "session_id": session_id,
            "question": session.get("question", "")[:120],  # truncate for index
            "status": session.get("status", "unknown"),
            "agents_run": [r["agent_name"] for r in session.get("agent_results", [])],
            "confidence": session.get("confidence", 0.0),
            "total_latency_ms": session.get("total_latency_ms", 0),
            "created_at": session.get("created_at", ""),
        }

        # Remove old entry for same session_id if re-saving
        index = [e for e in index if e.get("session_id") != session_id]
        index.insert(0, summary)
        index = index[:MAX_INDEX_ENTRIES]

        with open(INDEX_PATH, "w", encoding="utf-8") as f:
            json.dump(index, f, indent=2)
