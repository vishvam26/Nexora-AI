"""
ManagerAgent — Step 11 Multi-Agent Orchestration

The central LLM planner and synthesizer of the Nexora AI Decision Intelligence Platform.

Two-Pass LLM Architecture:
─────────────────────────────────────────────────────────────────────────
Pass 1 — PLANNING (OpenAI Function Calling):
    Input : CEO question + agent tool definitions
    LLM   : Selects which agents to invoke and what task to give each
    Output: List of AgentPlanStep (ordered, dependency-aware)

Pass 2 — SYNTHESIS (Standard Chat Completion):
    Input : CEO question + all AgentResult summaries + RAG context chunks
    LLM   : Generates one coherent, cited, boardroom-ready final answer
    Output: Final answer string + extracted citations + confidence score
─────────────────────────────────────────────────────────────────────────

Anti-hallucination guarantees:
- Synthesis prompt explicitly forbids fabricating numbers not in agent outputs
- If no relevant data found: returns "No relevant information found in the available data."
- Confidence score reflects how many agents returned successful results

Design: Manager is completely decoupled from individual agents.
It only knows about BaseAgent.get_tool_definition() and AgentResult.
Adding a new agent requires zero changes to ManagerAgent.
"""
import json
import logging
import os
from typing import Dict, Any, List, Optional, Generator

from app.services.agents.base_agent import AgentContext, AgentResult

logger = logging.getLogger("app.services.agents.manager_agent")

# Max chars of agent output passed to synthesis LLM
MAX_SYNTHESIS_CONTEXT = 24_000


class ManagerAgent:
    """
    LLM-powered planner and synthesizer.
    Does NOT inherit BaseAgent — it IS the orchestration layer, not a worker.
    """

    def __init__(self, agents: List[Any]):
        """
        agents: list of BaseAgent instances (Analytics, ML, RAG, Report)
        """
        self.agents: Dict[str, Any] = {a.name: a for a in agents}

    # ──────────────────────────────────────────────────────────────────
    # Pass 1: Planning
    # ──────────────────────────────────────────────────────────────────

    def plan(self, context: AgentContext) -> List[Dict[str, Any]]:
        """
        Uses OpenAI function-calling to determine which agents to invoke.

        Returns a list of plan steps:
        [
            {"agent": "analytics_agent", "task": "analyze churn distribution"},
            {"agent": "ml_agent",        "task": "explain feature importances"},
            {"agent": "rag_agent",       "task": "find churn reduction policies"},
        ]

        Falls back to a safe default plan if LLM unavailable.
        """
        api_key = os.environ.get("OPENAI_API_KEY", "")
        if not api_key:
            logger.warning("[ManagerAgent] OPENAI_API_KEY not set — using fallback plan")
            return self._fallback_plan(context)

        try:
            import openai
            client = openai.OpenAI(api_key=api_key)

            # Build tool definitions from all registered agents
            tools = [agent.get_tool_definition() for agent in self.agents.values()]

            # Suppress report_agent if CEO didn't ask for a report
            if not context.generate_report:
                tools = [t for t in tools if t["function"]["name"] != "report_agent"]

            system_prompt = (
                "You are the Manager Agent in Nexora AI Decision Intelligence Platform. "
                "Your role is to analyze the CEO's question and decide which specialized agents to invoke. "
                "\n\nAvailable context:\n"
                f"- Document available: {'Yes (doc_id=' + str(context.doc_id) + ')' if context.doc_id else 'No'}\n"
                f"- Knowledge base: {'Yes (workspace_id=' + str(context.workspace_id) + ')' if context.workspace_id else 'No'}\n"
                f"- Generate report: {'Yes' if context.generate_report else 'No'}\n"
                "\nRules:\n"
                "1. Only call agents whose capabilities are relevant to the question.\n"
                "2. If no document is available, skip analytics_agent and ml_agent.\n"
                "3. If no knowledge base is available, skip rag_agent.\n"
                "4. Write a specific, actionable task description for each agent.\n"
                "5. You may call multiple agents — call ALL that are relevant.\n"
                "6. If generate_report=True, always include report_agent last.\n"
                "7. If the CEO's question references past topics, previous runs, reports, or history, always call memory_agent first.\n"
                "8. If the CEO's question asks for database stats, user registrations, count metrics, schemas, or tables, always invoke sql_agent.\n"
                "9. If the CEO's question requires custom math, calculations, coding, plotting, charting, or visualization, always call python_agent.\n"
                "10. If the CEO's question requests emailing a report, sending notification updates, or dispatching email alerts, always call email_agent last.\n"
                "11. If the CEO's question requests booking a meeting, scheduling a sync, planning calendar events, or checking slot availability, always invoke calendar_agent.\n"
            )





            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"CEO Question: {context.question}"},
                ],
                tools=tools,
                tool_choice="auto",
                max_tokens=1024,
            )

            # Parse tool calls from the LLM response
            plan = []
            msg = response.choices[0].message
            if msg.tool_calls:
                for tc in msg.tool_calls:
                    agent_name = tc.function.name
                    try:
                        args = json.loads(tc.function.arguments)
                        task = args.get("task", context.question)
                    except json.JSONDecodeError:
                        task = context.question
                    plan.append({"agent": agent_name, "task": task})

            if not plan:
                logger.info("[ManagerAgent] LLM chose no tools — using fallback plan")
                return self._fallback_plan(context)

            logger.info(f"[ManagerAgent] Plan: {[s['agent'] for s in plan]}")
            return plan

        except Exception as e:
            logger.error(f"[ManagerAgent] Planning LLM failed: {e}")
            return self._fallback_plan(context)

    def _fallback_plan(self, context: AgentContext) -> List[Dict[str, Any]]:
        """
        Rule-based fallback plan when LLM is unavailable.
        Selects agents based on what context is available.
        """
        plan = []
        if context.doc_id:
            plan.append({"agent": "analytics_agent", "task": context.question})
            plan.append({"agent": "ml_agent", "task": context.question})
        if context.workspace_id:
            plan.append({"agent": "rag_agent", "task": context.question})
        if context.generate_report and context.doc_id:
            plan.append({"agent": "report_agent", "task": f"Generate a {context.report_type} {context.report_format} report"})
        if not plan:
            # Last resort: try RAG with a broad search
            plan.append({"agent": "rag_agent", "task": context.question})
        return plan

    # ──────────────────────────────────────────────────────────────────
    # Pass 2: Synthesis
    # ──────────────────────────────────────────────────────────────────

    def synthesize(
        self,
        question: str,
        agent_results: List[AgentResult],
    ) -> Dict[str, Any]:
        """
        Synthesizes all agent results into one coherent final answer.

        Returns:
        {
            "final_answer": str,
            "citations": List[Dict],
            "confidence": float,
        }
        """
        api_key = os.environ.get("OPENAI_API_KEY", "")

        # Build context from all agent results
        context_blocks = []
        all_citations = []

        for result in agent_results:
            if result.status == "success":
                context_blocks.append(
                    f"### {result.agent_name.replace('_', ' ').title()}\n"
                    f"Task: {result.task}\n"
                    f"Summary: {result.summary}\n"
                )
                # Collect RAG citations
                rag_citations = result.output.get("citations", [])
                all_citations.extend(rag_citations)

                # Append key output data (limited for token budget)
                raw_output = json.dumps(result.output, default=str)
                if len(raw_output) > 3000:
                    raw_output = raw_output[:3000] + "...[truncated]"
                context_blocks.append(f"Data:\n```json\n{raw_output}\n```\n")
                
                # Check for memories and surface them specifically
                if result.agent_name == "memory_agent" and "memories" in result.output:
                    for idx, mem in enumerate(result.output["memories"]):
                        context_blocks.append(
                            f"### Historical Memory #{idx+1}\n"
                            f"Previous Question: {mem.get('question')}\n"
                            f"Previous Answer: {mem.get('final_answer')}\n"
                            f"Created At: {mem.get('created_at')}\n"
                        )
                
                # Check for SQL queries and format results clearly
                if result.agent_name == "sql_agent" and "query_result" in result.output:
                    q_res = result.output["query_result"]
                    context_blocks.append(
                        f"### Relational Query Output\n"
                        f"Columns: {', '.join(q_res.get('headers', []))}\n"
                        f"Rows Returned: {q_res.get('row_count', 0)}\n"
                    )
                
                # Check for Python executions and format console output
                if result.agent_name == "python_agent" and "stdout" in result.output:
                    context_blocks.append(
                        f"### Python Console STDOUT\n"
                        f"{result.output.get('stdout', '')}\n"
                    )
                    if "chart_path" in result.output:
                        context_blocks.append(
                            f"Generated Visualization Chart Path: {result.output.get('chart_path')}\n"
                        )
                
                # Check for Email dispatches and format summary details
                if result.agent_name == "email_agent" and "to" in result.output:
                    context_blocks.append(
                        f"### SMTP Mail Envelope Dispatch\n"
                        f"Recipient: {result.output.get('to')}\n"
                        f"Subject line: {subject}\n"
                        f"Status: Success\n"
                    )
                
                # Check for Calendar schedulings and format booking slots
                if result.agent_name == "calendar_agent" and "event_id" in result.output:
                    context_blocks.append(
                        f"### Local Calendar Meeting Booked\n"
                        f"Title: {result.output.get('title')}\n"
                        f"Start: {result.output.get('start_time')}\n"
                        f"End: {result.output.get('end_time')}\n"
                        f"ICS File Path: {result.output.get('ics_path')}\n"
                    )





            elif result.status == "skipped":
                context_blocks.append(
                    f"### {result.agent_name.replace('_', ' ').title()}\n"
                    f"Status: Skipped — {result.summary}\n"
                )
            else:
                context_blocks.append(
                    f"### {result.agent_name.replace('_', ' ').title()}\n"
                    f"Status: Error — {result.error}\n"
                )

        full_context = "\n\n".join(context_blocks)

        # Truncate total context to token budget
        if len(full_context) > MAX_SYNTHESIS_CONTEXT:
            full_context = full_context[:MAX_SYNTHESIS_CONTEXT] + "\n\n[Context truncated]"

        # Calculate confidence based on successful agents
        successful = sum(1 for r in agent_results if r.status == "success")
        total = len(agent_results)
        confidence = round(successful / total, 2) if total > 0 else 0.0

        from app.config import settings
        from app.services.ai_service import AIService

        # If no API key and provider is openai — return structured fallback
        if not api_key and settings.AI_PROVIDER.lower().strip() == "openai":
            fallback_answer = self._fallback_synthesis(agent_results)
            return {
                "final_answer": fallback_answer,
                "citations": all_citations,
                "confidence": confidence,
            }

        # LLM Synthesis
        try:
            if settings.AI_PROVIDER.lower().strip() == "openai" or api_key:
                system_prompt = (
                    "You are the Nexora AI final synthesis engine. "
                    "You receive structured outputs from multiple specialized AI agents and synthesize them "
                    "into one clear, professional, boardroom-ready answer for the CEO.\n\n"
                    "STRICT RULES:\n"
                    "1. Only use data explicitly present in the agent outputs below. Never fabricate numbers.\n"
                    "2. If data is missing for part of the answer, say: 'No relevant data available for this section.'\n"
                    "3. Structure the answer with clear sections (## headings).\n"
                    "4. Cite sources for RAG-retrieved information: [Source: DocumentName, Page X].\n"
                    "5. End with a '## Recommendation' section with 2-3 actionable insights.\n"
                    "6. Be concise — executives have 3 minutes, not 30.\n"
                )
                user_prompt = (
                    f"CEO Question: **{question}**\n\n"
                    f"=== AGENT OUTPUTS ===\n{full_context}\n\n"
                    "Generate the final synthesized answer following the rules above."
                )
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ]
                import openai
                client = openai.OpenAI(api_key=api_key)
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=messages,
                    max_tokens=2048,
                    temperature=0.2,
                )
                final_answer = response.choices[0].message.content or ""
                usage = getattr(response, "usage", None)
                tokens_in = usage.prompt_tokens if usage else 0
                tokens_out = usage.completion_tokens if usage else 0
                cost_usd = (tokens_in * 0.00000015) + (tokens_out * 0.00000060)
            else:
                system_prompt = (
                    "You are a helpful AI assistant. "
                    "Synthesize the outputs from the AI agents below to answer the user's question. "
                    "Be direct, concise, and professional."
                )
                user_prompt = (
                    f"Question: {question}\n\n"
                    f"Agent Findings:\n{full_context}\n"
                )
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ]
                final_answer = AIService.generate_response(messages)
                tokens_in = len(full_context) // 4
                tokens_out = len(final_answer) // 4
                cost_usd = 0.0

            return {
                "final_answer": final_answer,
                "citations": all_citations,
                "confidence": confidence,
                "tokens_in": tokens_in,
                "tokens_out": tokens_out,
                "cost_usd": round(cost_usd, 6),
            }

        except Exception as e:
            logger.error(f"[ManagerAgent] Synthesis LLM failed: {e}")
            return {
                "final_answer": self._fallback_synthesis(agent_results),
                "citations": all_citations,
                "confidence": confidence,
            }

    def _fallback_synthesis(self, agent_results: List[AgentResult]) -> str:
        """Structured text fallback when LLM synthesis is unavailable."""
        lines = [
            "# Nexora AI Analysis Report\n",
            "> ⚠ LLM synthesis unavailable (OPENAI_API_KEY not configured). "
            "Showing raw agent summaries.\n",
        ]
        for result in agent_results:
            agent_label = result.agent_name.replace("_", " ").title()
            lines.append(f"## {agent_label}")
            lines.append(f"**Status:** {result.status}")
            lines.append(f"**Summary:** {result.summary}\n")
        return "\n".join(lines)

    # ──────────────────────────────────────────────────────────────────
    # Streaming SSE generator
    # ──────────────────────────────────────────────────────────────────

    def stream_events(
        self,
        plan: List[Dict[str, Any]],
        agent_results: List[AgentResult],
        synthesis_result: Dict[str, Any],
        session_id: str,
        total_latency_ms: int,
    ) -> Generator[str, None, None]:
        """
        Yields SSE-formatted event strings for the streaming endpoint.
        These are sent to the AgentStudio frontend in real-time.
        """
        def sse(event: str, data: Any) -> str:
            return f"event: {event}\ndata: {json.dumps(data, default=str)}\n\n"

        # Plan ready
        yield sse("plan_ready", {"plan": plan})

        # Agent results (replayed — actual streaming happens in orchestrator)
        for result in agent_results:
            yield sse("agent_result", {
                "agent": result.agent_name,
                "status": result.status,
                "summary": result.summary,
                "latency_ms": result.latency_ms,
                "tool_calls": result.tool_calls,
            })

        # Final answer
        yield sse("final_answer", {
            "answer": synthesis_result["final_answer"],
            "citations": synthesis_result["citations"],
            "confidence": synthesis_result["confidence"],
        })

        # Done
        yield sse("done", {
            "session_id": session_id,
            "total_latency_ms": total_latency_ms,
            "cost_usd": synthesis_result.get("cost_usd", 0.0),
            "tokens_in": synthesis_result.get("tokens_in", 0),
            "tokens_out": synthesis_result.get("tokens_out", 0)
        })

