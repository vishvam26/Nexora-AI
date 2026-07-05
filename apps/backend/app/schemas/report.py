"""
Pydantic schemas for Report Generator API (Step 10).
"""
from pydantic import BaseModel, Field
from typing import Literal, Optional


class ReportGenerateRequest(BaseModel):
    report_type: Literal[
        "executive_summary",
        "ml_model_card",
        "statistical_breakdown",
        "full_analytics",
    ] = Field(
        default="full_analytics",
        description="Type of report to generate",
    )
    export_format: Literal["markdown", "pdf", "excel", "pptx", "png"] = Field(
        default="pdf",
        description="Output file format",
    )
    grounded: bool = Field(
        default=True,
        description="If True, LLM is instructed to cite all data and avoid hallucinations",
    )
    custom_instructions: Optional[str] = Field(
        default="",
        description="Optional user instructions to append to the LLM report prompt",
        max_length=2000,
    )
    include_analytics: bool = Field(default=True, description="Include analytics profile in report")
    include_ml: bool = Field(default=True, description="Include ML session and model comparison")
    include_shap: bool = Field(default=True, description="Include SHAP feature attributions")
