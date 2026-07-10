"""
Pydantic Schemas for Agent Orchestration API — Step 11
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Literal


class AgentAskRequest(BaseModel):
    question: str = Field(
        ...,
        description="The CEO's decision question for the agent system",
        min_length=3,
        max_length=2000,
    )
    workspace_id: Optional[int] = Field(
        default=None,
        description="Workspace ID for RAG knowledge base scoping",
    )
    knowledge_base_id: Optional[int] = Field(
        default=None,
        description="Knowledge Base ID for specific RAG search scoping",
    )
    doc_id: Optional[int] = Field(
        default=None,
        description="Document ID for Analytics and ML agent scoping",
    )
    top_k: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Number of knowledge base chunks to retrieve (RAG Agent)",
    )
    generate_report: bool = Field(
        default=False,
        description="If True, ReportAgent is included to produce an exportable report",
    )
    report_format: Literal["pdf", "excel", "pptx", "png", "markdown"] = Field(
        default="pdf",
        description="Export format for the generated report",
    )
    report_type: Literal[
        "executive_summary", "ml_model_card", "statistical_breakdown", "full_analytics"
    ] = Field(
        default="full_analytics",
        description="Type of report to generate if generate_report=True",
    )


class AgentPlanStep(BaseModel):
    agent: str
    task: str


class AgentResultSchema(BaseModel):
    agent_name: str
    task: str
    status: str
    summary: str
    latency_ms: int
    tool_calls: List[str]
    error: Optional[str] = None


class AgentSessionResponse(BaseModel):
    session_id: str
    question: str
    workspace_id: Optional[int]
    doc_id: Optional[int]
    status: str
    plan: List[Dict[str, Any]]
    agent_results: List[Dict[str, Any]]
    final_answer: str
    citations: List[Dict[str, Any]]
    confidence: float
    total_latency_ms: int
    created_at: str
    completed_at: Optional[str] = None


class AgentSessionSummary(BaseModel):
    session_id: str
    question: str
    status: str
    agents_run: List[str]
    confidence: float
    total_latency_ms: int
    created_at: str
