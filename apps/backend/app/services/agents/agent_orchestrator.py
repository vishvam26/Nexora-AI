"""
AgentOrchestrator — Step 11 Multi-Agent Orchestration

The single public entry point for the entire agent system.
Callers (API endpoints) only need to call: AgentOrchestrator.ask()

Responsibilities:
1. Resolve doc_id → file_path (DB lookup)
2. Build AgentContext from request parameters
3. Call ManagerAgent.plan() to get the execution plan
4. Execute each agent sequentially (timed_run with 30s timeout guard)
5. Feed all results to ManagerAgent.synthesize()
6. Persist the complete AgentSession to disk
7. Return structured session response

Streaming variant: ask_stream() yields SSE events as agents complete.
"""
import time
import logging
from typing import Dict, Any, List, Optional, Generator

from app.services.agents.base_agent import AgentContext, AgentResult
from app.services.agents.analytics_agent import AnalyticsAgent
from app.services.agents.ml_agent import MLAgent
from app.services.agents.rag_agent import RAGAgent
from app.services.agents.report_agent import ReportAgent
from app.services.agents.memory_agent import MemoryAgent
from app.services.agents.sql_agent import SQLAgent
from app.services.agents.python_agent import PythonAgent
from app.services.agents.email_agent import EmailAgent
from app.services.agents.calendar_agent import CalendarAgent
from app.services.agents.manager_agent import ManagerAgent




from app.services.agents.agent_session import AgentSession

logger = logging.getLogger("app.services.agents.agent_orchestrator")

# Per-agent timeout in seconds (soft timeout via try/except, not OS signal)
AGENT_TIMEOUT_S = 30


class AgentOrchestrator:
    """
    Singleton-style orchestrator. Instantiated once at module level.
    All agents are initialized here to avoid repeated cold starts.
    """

    def __init__(self):
        self.analytics_agent = AnalyticsAgent()
        self.ml_agent = MLAgent()
        self.rag_agent = RAGAgent()
        self.report_agent = ReportAgent()
        self.memory_agent = MemoryAgent()
        self.sql_agent = SQLAgent()
        self.python_agent = PythonAgent()
        self.email_agent = EmailAgent()
        self.calendar_agent = CalendarAgent()

        self.all_agents = [



            self.analytics_agent,
            self.ml_agent,
            self.rag_agent,
            self.report_agent,
            self.memory_agent,
            self.sql_agent,
            self.python_agent,
            self.email_agent,
            self.calendar_agent,
        ]





        self.manager = ManagerAgent(agents=self.all_agents)
        logger.info("[AgentOrchestrator] Initialized with 4 agents.")

    def ask(
        self,
        question: str,
        user_id: Optional[int] = None,
        workspace_id: Optional[int] = None,
        knowledge_base_id: Optional[int] = None,
        doc_id: Optional[int] = None,
        file_path: Optional[str] = None,
        top_k: int = 5,
        generate_report: bool = False,
        report_format: str = "pdf",
        report_type: str = "full_analytics",
    ) -> Dict[str, Any]:
        """
        Main synchronous orchestration entry point.

        Returns full session dict:
        {
            "session_id": str,
            "plan": [...],
            "agent_results": [...],
            "final_answer": str,
            "citations": [...],
            "confidence": float,
            "total_latency_ms": int,
            "status": "complete" | "failed",
        }
        """
        t_start = time.time()

        # ── 1. Create Session ─────────────────────────────────────────
        session = AgentSession.create(question, workspace_id, doc_id)
        session_id = session["session_id"]

        # ── 2. Build Context ──────────────────────────────────────────
        context = AgentContext(
            question=question,
            user_id=user_id,
            workspace_id=workspace_id,
            knowledge_base_id=knowledge_base_id,
            doc_id=doc_id,
            file_path=file_path,
            top_k=top_k,
            generate_report=generate_report,
            report_format=report_format,
            report_type=report_type,
        )

        # ── 3. Manager Plans ──────────────────────────────────────────
        logger.info(f"[AgentOrchestrator] Session {session_id} | Q: {question[:80]!r}")
        plan = self.manager.plan(context)
        session["plan"] = plan
        AgentSession.save(session)  # save intermediate state

        # ── 4. Execute Agents ─────────────────────────────────────────
        agent_results: List[AgentResult] = []
        prior_results: Dict[str, Any] = {}

        for step in plan:
            agent_name = step.get("agent", "")
            task = step.get("task", question)

            agent = self.all_agents.__class__  # default None
            agent = next(
                (a for a in self.all_agents if a.name == agent_name), None
            )

            if agent is None:
                logger.warning(f"[AgentOrchestrator] Unknown agent: {agent_name}")
                result = AgentResult.skipped(agent_name, task, f"Agent '{agent_name}' not registered.")
            else:
                # Update context with prior results for downstream agents
                context.prior_results = prior_results
                result = agent.timed_run(task, context)
                prior_results[agent_name] = result.output

            agent_results.append(result)
            session["agent_results"].append(result.to_dict())
            AgentSession.save(session)  # save after each agent for audit trail

        # ── 5. Synthesis ──────────────────────────────────────────────
        synthesis = self.manager.synthesize(question, agent_results)

        # ── 6. Finalize Session ───────────────────────────────────────
        total_ms = int((time.time() - t_start) * 1000)
        session["final_answer"] = synthesis["final_answer"]
        session["citations"] = synthesis["citations"]
        session["confidence"] = synthesis["confidence"]
        session["tokens_in"] = synthesis.get("tokens_in", 0)
        session["tokens_out"] = synthesis.get("tokens_out", 0)
        session["cost_usd"] = synthesis.get("cost_usd", 0.0)
        session["total_latency_ms"] = total_ms
        session["status"] = "complete"
        session["completed_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

        AgentSession.save(session)

        logger.info(
            f"[AgentOrchestrator] Session {session_id} complete | "
            f"{total_ms}ms | confidence={synthesis['confidence']}"
        )

        return session

    def ask_stream(
        self,
        question: str,
        user_id: Optional[int] = None,
        workspace_id: Optional[int] = None,
        knowledge_base_id: Optional[int] = None,
        doc_id: Optional[int] = None,
        file_path: Optional[str] = None,
        top_k: int = 5,
        generate_report: bool = False,
        report_format: str = "pdf",
        report_type: str = "full_analytics",
    ) -> Generator[str, None, None]:
        """
        Streaming SSE variant.
        Yields SSE event strings as each agent completes.
        Allows the AgentStudio UI to animate the pipeline in real-time.

        Event sequence:
          plan_ready → (agent_start → agent_result)* → synthesis_start → final_answer → done
        """
        import json

        def sse(event: str, data: Any) -> str:
            return f"event: {event}\ndata: {json.dumps(data, default=str)}\n\n"

        t_start = time.time()

        # Create session
        session = AgentSession.create(question, workspace_id, doc_id)
        session_id = session["session_id"]

        context = AgentContext(
            question=question,
            user_id=user_id,
            workspace_id=workspace_id,
            knowledge_base_id=knowledge_base_id,
            doc_id=doc_id,
            file_path=file_path,
            top_k=top_k,
            generate_report=generate_report,
            report_format=report_format,
            report_type=report_type,
        )

        # Plan
        plan = self.manager.plan(context)
        session["plan"] = plan
        AgentSession.save(session)
        yield sse("plan_ready", {"plan": plan, "session_id": session_id})

        # Execute agents + stream events
        agent_results: List[AgentResult] = []
        prior_results: Dict[str, Any] = {}

        for step in plan:
            agent_name = step.get("agent", "")
            task = step.get("task", question)

            yield sse("agent_start", {"agent": agent_name, "task": task})

            agent = next(
                (a for a in self.all_agents if a.name == agent_name), None
            )
            if agent is None:
                result = AgentResult.skipped(agent_name, task, f"Agent '{agent_name}' not registered.")
            else:
                context.prior_results = prior_results
                result = agent.timed_run(task, context)
                prior_results[agent_name] = result.output

            agent_results.append(result)
            session["agent_results"].append(result.to_dict())
            AgentSession.save(session)

            yield sse("agent_result", {
                "agent": result.agent_name,
                "status": result.status,
                "summary": result.summary,
                "latency_ms": result.latency_ms,
                "tool_calls": result.tool_calls,
                "output_keys": list(result.output.keys()),
            })

        # Synthesis
        yield sse("synthesis_start", {"agents_completed": len(agent_results)})

        synthesis = self.manager.synthesize(question, agent_results)
        total_ms = int((time.time() - t_start) * 1000)

        # Finalize
        session["final_answer"] = synthesis["final_answer"]
        session["citations"] = synthesis["citations"]
        session["confidence"] = synthesis["confidence"]
        session["tokens_in"] = synthesis.get("tokens_in", 0)
        session["tokens_out"] = synthesis.get("tokens_out", 0)
        session["cost_usd"] = synthesis.get("cost_usd", 0.0)
        session["total_latency_ms"] = total_ms
        session["status"] = "complete"
        session["completed_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        AgentSession.save(session)


        yield sse("final_answer", {
            "answer": synthesis["final_answer"],
            "citations": synthesis["citations"],
            "confidence": synthesis["confidence"],
        })

        yield sse("done", {
            "session_id": session_id,
            "total_latency_ms": total_ms,
            "cost_usd": session.get("cost_usd", 0.0),
            "tokens_in": session.get("tokens_in", 0),
            "tokens_out": session.get("tokens_out", 0)
        })



# Module-level singleton (shared across all requests)
_orchestrator: Optional[AgentOrchestrator] = None


def get_orchestrator() -> AgentOrchestrator:
    """
    Returns the module-level AgentOrchestrator singleton.
    FastAPI dependency injection will call this once per app startup.
    """
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = AgentOrchestrator()
    return _orchestrator
