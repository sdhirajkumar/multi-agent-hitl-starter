"""Conditional edge routing functions for LangGraph."""
from typing import Literal
from app.core.logging import logger
from app.graph.state import AgentState


def route_from_supervisor(
    state: AgentState,
) -> Literal["researcher", "writer", "reviewer", "human_review", "publisher"]:
    """Route from supervisor to the chosen worker node or termination gate."""
    next_agent = state.get("next_agent", "researcher")
    logger.debug(f"[Edge Router] Supervisor routed to -> {next_agent}")

    if next_agent in ("researcher", "writer", "reviewer", "human_review", "publisher"):
        return next_agent

    return "researcher"


def route_from_human_review(state: AgentState) -> Literal["publisher", "supervisor"]:
    """Route based on human decision: approve/edit -> publisher, reject -> supervisor."""
    decision = state.get("human_decision", "approve")
    logger.debug(f"[Edge Router] Human review routed with decision: {decision}")

    if decision in ("approve", "edit"):
        return "publisher"
    return "supervisor"
