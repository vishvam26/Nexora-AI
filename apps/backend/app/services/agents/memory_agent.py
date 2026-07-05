"""
MemoryAgent — Step 12 Multi-Agent Orchestration

Provides cross-session recall. Reads recent session logs from disk,
scores them against the current question using basic keyword/overlap logic,
and returns matched memories as context for the Manager Agent.
"""
import logging
import os
import re
from typing import Dict, Any, List

from app.services.agents.base_agent import BaseAgent, AgentContext, AgentResult
from app.services.agents.agent_session import AgentSession

logger = logging.getLogger("app.services.agents.memory_agent")


class MemoryAgent(BaseAgent):
    name = "memory_agent"
    description = (
        "Recalls insights, reports, answers, and context from past sessions. "
        "Invoke when the question references previous sessions, past reports, "
        "historical questions, or asks to compare current findings with earlier runs."
    )

    def run(self, task: str, context: AgentContext) -> AgentResult:
        tool_calls = []
        output: Dict[str, Any] = {}
        summaries = []

        # 1. Retrieve rolling index of recent sessions
        try:
            recent_sessions = AgentSession.list_recent(limit=50)
            tool_calls.append("AgentSession.list_recent")
        except Exception as e:
            logger.error(f"[MemoryAgent] Failed to read sessions index: {e}")
            return AgentResult.error_result(self.name, task, f"Index read failed: {str(e)}")

        if not recent_sessions:
            return AgentResult(
                agent_name=self.name,
                task=task,
                status="success",
                output={"memories": []},
                summary="No previous session logs found to recall from.",
                tool_calls=tool_calls
            )

        # 2. Tokenize task/query for keyword overlap score
        query_words = set(re.findall(r"\w+", (task or context.question).lower()))
        matched_memories = []

        # 3. Load full details for potential matches and compute score
        for summary_entry in recent_sessions:
            sess_id = summary_entry.get("session_id")
            if not sess_id:
                continue

            # Skip the active session if it has been saved intermediate
            if context.prior_results and any(r.get("session_id") == sess_id for r in context.prior_results.values()):
                continue

            # Calculate keyword overlap score vs question
            sess_question = summary_entry.get("question", "").lower()
            sess_words = set(re.findall(r"\w+", sess_question))
            overlap = len(query_words.intersection(sess_words))

            if overlap > 0:
                # Load full session details to extract synthesized answer
                full_sess = AgentSession.get(sess_id)
                tool_calls.append("AgentSession.get")
                if full_sess and full_sess.get("final_answer"):
                    matched_memories.append({
                        "session_id": sess_id,
                        "question": full_sess.get("question"),
                        "final_answer": full_sess.get("final_answer")[:500] + ("..." if len(full_sess.get("final_answer", "")) > 500 else ""),
                        "created_at": full_sess.get("created_at"),
                        "relevance_score": overlap
                    })

        # Sort memories by relevance score descending
        matched_memories.sort(key=lambda x: x["relevance_score"], reverse=True)
        top_memories = matched_memories[:3] # Keep top 3 relevant historical answers

        output["memories"] = top_memories
        
        if top_memories:
            summary_parts = []
            for mem in top_memories:
                summary_parts.append(f"Session {mem['session_id'][:8]} (Q: '{mem['question']}')")
            summaries.append(f"Recalled {len(top_memories)} past session(s): {'; '.join(summary_parts)}.")
        else:
            summaries.append("Searched past sessions but found no relevant match.")

        return AgentResult(
            agent_name=self.name,
            task=task,
            status="success",
            output=output,
            summary=" ".join(summaries),
            tool_calls=tool_calls
        )

    def get_tool_definition(self) -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "task": {
                            "type": "string",
                            "description": "Historical context request/keyword to recall from memory, e.g. 'previous churn analysis' or 'last week meeting notes'"
                        }
                    },
                    "required": ["task"]
                }
            }
        }
