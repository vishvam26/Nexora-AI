"""
Pydantic Schemas for MCP / SQL Studio API — Step 13
"""
from pydantic import BaseModel, Field


class SQLQueryRequest(BaseModel):
    query: str = Field(
        ...,
        description="The SELECT SQL query string to execute",
        min_length=10,
        max_length=5000,
    )
