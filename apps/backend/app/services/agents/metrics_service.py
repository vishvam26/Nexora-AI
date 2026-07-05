"""
MetricsService — Step 12 Cost Tracker & Observability

Gathers sessions stored as JSON logs on disk to compute aggregated KPI statistics:
- Total sessions run
- Average total latency
- Overall run success rate vs error rate
- Cumulative monetary cost in USD (GPT-4o-mini rates)
- Per-agent performance metrics (avg execution latency, runs, skipped counts)
- Daily cost history for charting
"""
import os
import json
import logging
from collections import defaultdict
from typing import Dict, Any, List

from app.services.agents.agent_session import AgentSession

logger = logging.getLogger("app.services.agents.metrics_service")

SESSION_DIR = os.path.join("storage", "agent_sessions")


class MetricsService:
    """
    Calculates operational health and billing statistics from historical session JSON files.
    """

    @classmethod
    def get_dashboard_data(cls) -> Dict[str, Any]:
        """
        Scans all files in agent_sessions directory to produce aggregate metrics.
        """
        total_sessions = 0
        total_latency = 0.0
        total_cost = 0.0
        total_tokens_in = 0
        total_tokens_out = 0
        status_counts = defaultdict(int)

        # Per-agent counters
        agent_metrics = defaultdict(lambda: {
            "runs": 0,
            "success": 0,
            "error": 0,
            "skipped": 0,
            "latency_sum": 0.0,
            "cost_sum": 0.0
        })

        # Daily cost trends
        daily_trends = defaultdict(lambda: {"cost": 0.0, "sessions": 0})

        if not os.path.exists(SESSION_DIR):
            return cls._empty_metrics()

        try:
            files = [f for f in os.listdir(SESSION_DIR) if f.endswith(".json") and f != "index.json"]
        except Exception as e:
            logger.error(f"[MetricsService] Directory scan failed: {e}")
            return cls._empty_metrics()

        for filename in files:
            filepath = os.path.join(SESSION_DIR, filename)
            try:
                with open(filepath, "r", encoding="utf-8") as fh:
                    sess = json.load(fh)
            except Exception:
                continue

            total_sessions += 1
            total_latency += sess.get("total_latency_ms", 0)
            total_cost += sess.get("cost_usd", 0.0)
            total_tokens_in += sess.get("tokens_in", 0)
            total_tokens_out += sess.get("tokens_out", 0)
            
            status = sess.get("status", "unknown")
            status_counts[status] += 1

            # Parse daily trends based on created_at (YYYY-MM-DD)
            created_at = sess.get("created_at", "")
            if created_at and len(created_at) >= 10:
                date_str = created_at[:10]
                daily_trends[date_str]["cost"] += sess.get("cost_usd", 0.0)
                daily_trends[date_str]["sessions"] += 1

            # Parse individual agent metrics
            for result in sess.get("agent_results", []):
                name = result.get("agent_name", "unknown")
                state = result.get("status", "unknown")
                latency = result.get("latency_ms", 0)
                cost = result.get("cost_usd", 0.0)

                agent_metrics[name]["runs"] += 1
                agent_metrics[name]["latency_sum"] += latency
                agent_metrics[name]["cost_sum"] += cost

                if state == "success":
                    agent_metrics[name]["success"] += 1
                elif state == "error":
                    agent_metrics[name]["error"] += 1
                elif state == "skipped":
                    agent_metrics[name]["skipped"] += 1

        if total_sessions == 0:
            return cls._empty_metrics()

        # Format agent metrics dictionary
        formatted_agents = {}
        for name, metrics in agent_metrics.items():
            runs = metrics["runs"]
            formatted_agents[name] = {
                "name": name,
                "runs": runs,
                "success_rate": round(metrics["success"] / runs * 100, 1) if runs > 0 else 0,
                "avg_latency_ms": int(metrics["latency_sum"] / runs) if runs > 0 else 0,
                "total_cost_usd": round(metrics["cost_sum"], 6)
            }

        # Format daily trends list sorted by date ascending
        formatted_trends = []
        for date_str, data in sorted(daily_trends.items()):
            formatted_trends.append({
                "date": date_str,
                "cost_usd": round(data["cost"], 6),
                "sessions": data["sessions"]
            })

        avg_latency = int(total_latency / total_sessions)
        success_rate = round((status_counts["complete"] / total_sessions) * 100, 1) if total_sessions > 0 else 0.0

        return {
            "total_sessions": total_sessions,
            "avg_latency_ms": avg_latency,
            "success_rate": success_rate,
            "total_cost_usd": round(total_cost, 6),
            "total_tokens_in": total_tokens_in,
            "total_tokens_out": total_tokens_out,
            "status_breakdown": dict(status_counts),
            "agents": formatted_agents,
            "daily_trends": formatted_trends
        }

    @classmethod
    def _empty_metrics(cls) -> Dict[str, Any]:
        return {
            "total_sessions": 0,
            "avg_latency_ms": 0,
            "success_rate": 0.0,
            "total_cost_usd": 0.0,
            "total_tokens_in": 0,
            "total_tokens_out": 0,
            "status_breakdown": {},
            "agents": {},
            "daily_trends": []
        }
