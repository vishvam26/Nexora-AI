"""
SQL Database Tool — Step 13 Model Context Protocol

Connects directly to the operational PostgreSQL database to:
  - Extract active schemas, tables, and column data types
  - Execute read-only SELECT queries securely
  - Implement regex blocks to prevent write-commands (SQL injection blocks)
"""
import re
import logging
from sqlalchemy import text, inspect
from sqlalchemy.orm import Session
from typing import Dict, Any, List

from app.services.mcp.tool_registry import ToolRegistry

logger = logging.getLogger("app.services.mcp.sql_tool")


class SQLTool:
    """
    SQL Database Operations Tool Wrapper.
    """

    @staticmethod
    @ToolRegistry.register(
        name="db_schema_inspector",
        description="Returns tables, column names, and data types of the relational database."
    )
    def get_schema_info(db: Session) -> Dict[str, Any]:
        """
        Reflects database tables to dynamically return structure info.
        """
        try:
            inspector = inspect(db.get_bind())
            tables = inspector.get_table_names()
            schema_data = {}

            for table in tables:
                columns = []
                for col in inspector.get_columns(table):
                    columns.append({
                        "name": col["name"],
                        "type": str(col["type"]),
                        "nullable": col["nullable"]
                    })
                schema_data[table] = columns
            return {"success": True, "schema": schema_data}
        except Exception as e:
            logger.error(f"[SQLTool] Schema inspection failed: {e}")
            return {"success": False, "error": str(e)}

    @staticmethod
    @ToolRegistry.register(
        name="db_query_executor",
        description="Executes a raw read-only SQL query against the database and returns rows."
    )
    def execute_query(db: Session, sql_query: str) -> Dict[str, Any]:
        """
        Runs read-only SELECT queries with keyword filtering safeguards.
        """
        clean_query = sql_query.strip()
        
        # 1. Enforce SELECT-only checks
        if not re.match(r"^\s*select\b", clean_query, re.IGNORECASE):
            return {
                "success": False,
                "error": "Security Block: Only SELECT queries are permitted for read operations."
            }

        # 2. Block destructive DDL/DML keywords
        forbidden = [
            r"\binsert\b", r"\bupdate\b", r"\bdelete\b", r"\bdrop\b", 
            r"\balter\b", r"\btruncate\b", r"\bcreate\b", r"\bgrant\b"
        ]
        for word in forbidden:
            if re.search(word, clean_query, re.IGNORECASE):
                return {
                    "success": False,
                    "error": f"Security Block: Forbidden write operation keywords found in query: {word}"
                }

        try:
            result = db.execute(text(clean_query))
            # Resolve headers
            headers = list(result.keys())
            rows = [dict(zip(headers, row)) for row in result.fetchall()]
            
            return {
                "success": True,
                "row_count": len(rows),
                "headers": headers,
                "rows": rows[:100] # Cap rows at 100 to prevent buffer overload
            }
        except Exception as e:
            logger.error(f"[SQLTool] Query failed: {e}")
            return {"success": False, "error": str(e)}
