"""StateGraph definition, node assembly, and compilation."""
from datetime import datetime
from typing import Any, Dict, Optional
from langchain_core.messages import AIMessage
from langgraph.graph import END, START, StateGraph
from langgraph.types import interrupt

from app.agents.supervisor import supervisor_node
from app.agents.researcher import researcher_node
from app.agents.writer import writer_node
from app.agents.reviewer import reviewer_node
from app.core.logging import logger
from app.graph.edges import route_from_supervisor, route_from_human_review
from app.graph.state import AgentState


async def human_review_node(state: AgentState) -> Dict[str, Any]:
    """Human-in-the-Loop gate node. Dynamically pauses execution using LangGraph's

    interrupt() primitive, surfacing the draft to the human reviewer. Resumes
    when human submits an action: 'approve', 'edit', or 'reject'.
    """
    logger.info("[HITL Gate] Reached Human Review Gate. Dynamic interrupt() pausing execution.")

    interrupt_payload = {
        "type": "human_approval",
        "task": state.get("task", ""),
        "deliverable_type": state.get("deliverable_type", "technical_brief"),
        "draft": state.get("draft", ""),
        "revision_count": state.get("revision_count", 0),
        "critique": state.get("critique", ""),
        "timestamp": datetime.utcnow().isoformat(),
    }

    # Dynamically pause graph execution until Command(resume=decision) is received
    human_decision_data = interrupt(interrupt_payload)

    logger.info(f"[HITL Gate] Resumed with decision: {human_decision_data}")

    action = human_decision_data.get("action", "approve")
    edited_draft = human_decision_data.get("edited_draft")
    feedback = human_decision_data.get("feedback")

    final_draft = edited_draft if (action == "edit" and edited_draft) else state.get("draft", "")

    event = {
        "node": "human_review",
        "agent": "Human Gate",
        "timestamp": datetime.utcnow().isoformat(),
        "action": f"human_{action}",
        "detail": f"Human review action '{action}' submitted. Feedback: {bool(feedback)}",
    }

    message = AIMessage(
        content=f"[Human Reviewer] Decision: {action.upper()}"
        + (f" | Feedback: {feedback}" if feedback else "")
        + (" | Direct edits applied." if action == "edit" else ""),
        name="human_gate",
    )

    return {
        "draft": final_draft,
        "human_decision": action,
        "human_feedback": feedback if action == "reject" else None,
        "status": f"human_{action}",
        "events": [event],
        "messages": [message],
    }


async def publisher_node(state: AgentState) -> Dict[str, Any]:
    """Finalization node that commits and formats the final deliverable."""
    draft = state.get("draft", "")
    logger.info(f"[Publisher] Publishing deliverable ({len(draft)} chars).")

    event = {
        "node": "publisher",
        "agent": "Publisher",
        "timestamp": datetime.utcnow().isoformat(),
        "action": "published",
        "detail": f"Final deliverable approved and published successfully ({len(draft)} characters).",
    }

    message = AIMessage(
        content="[Publisher] Final deliverable verified and ready for deployment.",
        name="publisher",
    )

    return {
        "final_output": draft,
        "status": "completed",
        "events": [event],
        "messages": [message],
    }


def build_graph():
    """Construct the uncompiled StateGraph."""
    workflow = StateGraph(AgentState)

    # 1. Add agent and gate nodes
    workflow.add_node("supervisor", supervisor_node)
    workflow.add_node("researcher", researcher_node)
    workflow.add_node("writer", writer_node)
    workflow.add_node("reviewer", reviewer_node)
    workflow.add_node("human_review", human_review_node)
    workflow.add_node("publisher", publisher_node)

    # 2. Add entry edge
    workflow.add_edge(START, "supervisor")

    # 3. Add supervisor conditional routing
    workflow.add_conditional_edges(
        "supervisor",
        route_from_supervisor,
        {
            "researcher": "researcher",
            "writer": "writer",
            "reviewer": "reviewer",
            "human_review": "human_review",
            "publisher": "publisher",
        },
    )

    # 4. Add worker return edges back to supervisor
    workflow.add_edge("researcher", "supervisor")
    workflow.add_edge("writer", "supervisor")
    workflow.add_edge("reviewer", "supervisor")

    # 5. Add human review conditional edge
    workflow.add_conditional_edges(
        "human_review",
        route_from_human_review,
        {
            "publisher": "publisher",
            "supervisor": "supervisor",
        },
    )

    # 6. Publisher terminates the graph
    workflow.add_edge("publisher", END)

    return workflow


def create_agent_graph(checkpointer: Optional[Any] = None):
    """Build and compile the multi-agent graph with optional checkpointer."""
    workflow = build_graph()
    return workflow.compile(checkpointer=checkpointer)
