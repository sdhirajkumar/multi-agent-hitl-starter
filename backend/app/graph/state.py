"""Typed state schema for the multi-agent graph with reducers."""
import operator
from typing import Annotated, Any, Dict, List, Optional
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class AgentState(TypedDict, total=False):
    """Shared state dictionary passed across all graph nodes."""

    # Core Task & Delivery Specification
    task: str
    deliverable_type: str

    # Runtime LLM Configuration Overrides
    llm_provider: str
    model_name: Optional[str]
    temperature: float

    # Multi-Agent State Artifacts
    plan: List[str]
    research_data: List[str]
    draft: str
    critique: Optional[str]
    revision_count: int
    max_revisions: int

    # Human-in-the-Loop Gate Fields
    human_feedback: Optional[str]
    human_decision: Optional[str]  # "approve" | "edit" | "reject"

    # Orchestration & Flow Status
    status: str
    next_agent: Optional[str]
    final_output: Optional[str]

    # Message and Event Reducers
    messages: Annotated[List[BaseMessage], add_messages]
    events: Annotated[List[Dict[str, Any]], operator.add]
