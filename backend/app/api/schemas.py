"""Pydantic schemas for the REST and SSE API endpoints."""
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field


class CreateRunRequest(BaseModel):
    """Payload to initiate a new multi-agent workflow run."""

    task: str = Field(
        ...,
        min_length=3,
        description="The deliverable goal or prompt for the multi-agent system.",
        json_schema_extra={"example": "Create an Incident Response Plan for a high-severity Redis cluster outage"},
    )
    deliverable_type: str = Field(
        default="incident_response_plan",
        description="Type of deliverable (e.g., technical_brief, incident_response_plan, content_outline)",
    )
    llm_provider: Optional[str] = Field(
        default=None,
        description="LLM provider: 'mock', 'openai', 'anthropic', 'gemini', 'bedrock', 'ollama'",
    )
    model_name: Optional[str] = Field(
        default=None,
        description="Model name override (e.g. gpt-4o, claude-3-5-sonnet, llama3)",
    )
    temperature: Optional[float] = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Sampling temperature",
    )


class ResumeRunRequest(BaseModel):
    """Payload for human decision upon graph interrupt."""

    action: Literal["approve", "edit", "reject"] = Field(
        ...,
        description="Decision: 'approve' to finalize, 'edit' to replace draft, or 'reject' to request revision.",
    )
    edited_draft: Optional[str] = Field(
        default=None,
        description="Directly edited draft string (required if action is 'edit').",
    )
    feedback: Optional[str] = Field(
        default=None,
        description="Human critique / feedback for the Writer (recommended if action is 'reject').",
    )


class RunResponse(BaseModel):
    """Response returned upon starting a new run."""

    thread_id: str
    status: str
    deliverable_type: str
    message: str


class RunStateResponse(BaseModel):
    """Comprehensive snapshot of a run's state and interrupt status."""

    thread_id: str
    status: str
    is_interrupted: bool
    interrupt_data: Optional[Dict[str, Any]] = None
    draft: Optional[str] = None
    final_output: Optional[str] = None
    plan: List[str] = Field(default_factory=list)
    research_data: List[str] = Field(default_factory=list)
    revision_count: int = 0
    events: List[Dict[str, Any]] = Field(default_factory=list)
    next_nodes: List[str] = Field(default_factory=list)
