"""
MCP Database endpoints — Step 13 Model Context Protocol

Exposes routes to:
  - Fetch active database table schemas
  - Execute read-only SELECT commands inside a query sandbox
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any

from app.db.session import get_db
from app.models.user import User
from app.security.dependencies import get_current_user
from app.services.mcp.sql_tool import SQLTool
from app.schemas.mcp import SQLQueryRequest

router = APIRouter(
    prefix="/mcp",
    tags=["Model Context Protocol"],
)


@router.get(
    "/schema",
    response_model=Dict[str, Any],
    summary="Get relational database schemas, tables and column definitions",
)
def get_db_schema(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Returns active schema lists dynamically reflected from active database engines.
    """
    res = SQLTool.get_schema_info(db)
    if not res.get("success"):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=res.get("error", "Database reflection failed.")
        )
    return res


@router.post(
    "/query",
    response_model=Dict[str, Any],
    summary="Execute SELECT queries securely inside the query sandbox",
)
def execute_sql_query(
    payload: SQLQueryRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Executes SELECT queries with security regex checks to prevent write queries.
    """
    res = SQLTool.execute_query(db, payload.query)
    if not res.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=res.get("error", "SQL Query execution failed.")
        )
    return res
