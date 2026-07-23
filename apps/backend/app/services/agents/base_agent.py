"""
Base Agent Framework — Step 11 Multi-Agent Orchestration

Defines the contract that all specialized agents must implement.
BaseAgent is the single interface the ManagerAgent and AgentOrchestrator talk to.

Design principles:
- Each agent is independently callable (no tight coupling to orchestrator)
- AgentResult is fully serializable to JSON for SSE streaming and session storage
- AgentContext carries only what agents need — no God objects
- tool_calls list lets the Manager audit what backend services ran
"""
import time
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, List, Optional

logger = logging.getLogger("app.services.agents.base_agent")


# ──────────────────────────────────────────────────────────────────────────────
# Data Contracts
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class AgentContext:
    """
    Carries all context an agent might need.
    Agents only read what's relevant to them.
    """
    question: str                           # Original CEO question
    user_id: Optional[int] = None           # Calling user ID
    workspace_id: Optional[int] = None      # For RAG scoping
    knowledge_base_id: Optional[int] = None # For specific KB scoping
    doc_id: Optional[int] = None            # For Analytics/ML scoping
    file_path: Optional[str] = None         # For Analytics/ML file access
    top_k: int = 5                          # RAG retrieval depth
    generate_report: bool = False           # Signal for ReportAgent
    report_format: str = "pdf"              # Report export format
    report_type: str = "full_analytics"     # Report type key
    prior_results: Dict[str, Any] = field(default_factory=dict)
    # prior_results allows downstream agents to consume upstream agent outputs
    # e.g. RAGAgent can see AnalyticsAgent's profile summary before crafting its query


@dataclass
class AgentResult:
    """
    Standardized output from every agent.
    Fully JSON-serializable for SSE streaming + session persistence.
    """
    agent_name: str
    task: str
    status: str                              # "success" | "error" | "skipped"
    output: Dict[str, Any]                   # Raw structured data from backend services
    summary: str                             # Human-readable summary of findings
    latency_ms: int = 0
    tool_calls: List[str] = field(default_factory=list)  # Which backend APIs were called
    error: Optional[str] = None
    tokens_in: int = 0
    tokens_out: int = 0
    cost_usd: float = 0.0

    def to_dict(self) -> Dict[str, Any]:

        return asdict(self)

    @classmethod
    def skipped(cls, agent_name: str, task: str, reason: str) -> "AgentResult":
        return cls(
            agent_name=agent_name,
            task=task,
            status="skipped",
            output={},
            summary=f"Skipped: {reason}",
            error=reason,
        )

    @classmethod
    def error_result(cls, agent_name: str, task: str, error: str) -> "AgentResult":
        return cls(
            agent_name=agent_name,
            task=task,
            status="error",
            output={},
            summary=f"Agent encountered an error: {error}",
            error=error,
        )


# ──────────────────────────────────────────────────────────────────────────────
# Base Agent Abstract Class
# ──────────────────────────────────────────────────────────────────────────────

class BaseAgent(ABC):
    """
    Abstract base class for all Nexora specialized agents.

    Subclasses must implement:
    - name: str            — unique identifier used in Manager tool definitions
    - description: str     — shown to Manager LLM so it knows when to invoke this agent
    - run()                — the main execution method
    - get_tool_definition()— returns OpenAI function-calling tool spec for Manager

    The timed_run() wrapper handles timing, error catching, and logging automatically.
    """

    name: str = "base_agent"
    description: str = "A generic agent."

    @abstractmethod
    def run(self, task: str, context: AgentContext) -> AgentResult:
        """
        Execute the agent's task.
        Must return an AgentResult — never raise exceptions (catch internally).
        """
        ...

    def timed_run(self, task: str, context: AgentContext) -> AgentResult:
        """
        Wraps run() with timing, exception safety, and structured logging.
        The Orchestrator always calls this, never run() directly.
        """
        t0 = time.time()
        logger.info(f"[{self.name}] Starting: {task!r}")
        try:
            result = self.run(task, context)
            result.latency_ms = int((time.time() - t0) * 1000)
            logger.info(
                f"[{self.name}] Done in {result.latency_ms}ms | status={result.status}"
            )
            return result
        except Exception as e:
            latency_ms = int((time.time() - t0) * 1000)
            logger.error(f"[{self.name}] Unhandled exception: {e}", exc_info=True)
            result = AgentResult.error_result(self.name, task, str(e))
            result.latency_ms = latency_ms
            return result

    def get_tool_definition(self) -> Dict[str, Any]:
        """
        Returns an OpenAI function-calling tool definition.
        Manager Agent uses this to decide whether to invoke this agent.
        Subclasses can override to add custom parameters.
        """
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
                            "description": "Specific sub-task for this agent to perform",
                        }
                    },
                    "required": ["task"],
                },
            },
        }
