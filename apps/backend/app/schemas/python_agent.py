"""
Pydantic Schemas for Python Execution API — Step 14
"""
from pydantic import BaseModel, Field


class PythonCodeRequest(BaseModel):
    code: str = Field(
        ...,
        description="The raw Python script block to execute in the sandbox",
        min_length=5,
        max_length=8000,
    )
