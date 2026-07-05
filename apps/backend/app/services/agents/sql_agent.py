"""
SQLAgent — Step 13 Model Context Protocol

Specialized agent that executes SELECT queries directly against the database
to fetch schemas, transactional tables, and run transactional metrics.
"""
import logging
from typing import Dict, Any

from app.services.agents.base_agent import BaseAgent, AgentContext, AgentResult
from app.services.mcp.sql_tool import SQLTool
from app.db.session import SessionLocal

logger = logging.getLogger("app.services.agents.sql_agent")


class SQLAgent(BaseAgent):
    name = "sql_agent"
    description = (
        "Queries the application relational database directly. "
        "Allows database schema inspection (tables, columns) and executes read-only "
        "SELECT queries to fetch actual counts, user registration lists, and metrics. "
        "Invoke when the CEO's question requires real-time query counts from Nexora's operational database."
    )

    def run(self, task: str, context: AgentContext) -> AgentResult:
        tool_calls = []
        output: Dict[str, Any] = {}
        summaries = []

        # Obtain direct database connection session
        db = SessionLocal()
        try:
            # 1. Check if table schema is requested or missing in context
            if "schema" in task.lower() or "table" in task.lower() or "columns" in task.lower():
                schema_res = SQLTool.get_schema_info(db)
                tool_calls.append("SQLTool.get_schema_info")
                if schema_res.get("success"):
                    output["db_schema"] = schema_res.get("schema")
                    tables = list(schema_res.get("schema", {}).keys())
                    summaries.append(f"Inspected database schema. Found tables: {', '.join(tables)}.")
                else:
                    summaries.append(f"Schema inspection warning: {schema_res.get('error')}")

            # 2. Query execution intent translation (simple rule mapping for basic tasks)
            # If a SQL statement is inside task string, execute it directly
            sql_match = re.search(r"(select\s+.*)", task, re.IGNORECASE | re.DOTALL)
            if sql_match:
                sql_query = sql_match.group(1)
                query_res = SQLTool.execute_query(db, sql_query)
                tool_calls.append("SQLTool.execute_query")
                if query_res.get("success"):
                    output["query_result"] = query_res
                    count = query_res.get("row_count", 0)
                    summaries.append(f"Executed SELECT query successfully. Returned {count} row(s).")
                else:
                    summaries.append(f"SQL execution error: {query_res.get('error')}")
            else:
                # If no explicit SELECT, perform a general schema mapping
                schema_res = SQLTool.get_schema_info(db)
                tool_calls.append("SQLTool.get_schema_info")
                if schema_res.get("success"):
                    output["db_schema"] = schema_res.get("schema")
                    tables = list(schema_res.get("schema", {}).keys())
                    summaries.append(f"Operational database structure loaded. Tables available: {', '.join(tables)}.")

        except Exception as e:
            logger.error(f"[SQLAgent] SQLAgent execution failed: {e}")
            return AgentResult.error_result(self.name, task, str(e))
        finally:
            db.close()

        if not output:
            return AgentResult.error_result(self.name, task, "SQL Agent failed to retrieve data.")

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
                            "description": "SQL operation task description or the SELECT query block to execute, e.g. 'SELECT count(*) from users'"
                        }
                    },
                    "required": ["task"]
                }
            }
        }

import re
