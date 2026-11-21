"""Supervisor / Router Agent node definition."""
from datetime import datetime
from typing import Any, Dict
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from app.core.logging import logger
from app.graph.state import AgentState
from app.llm.factory import LLMFactory


SUPERVISOR_SYSTEM_PROMPT = """You are the Supervisor Agent in a specialized multi-agent workflow.
Your goal is to coordinate the delivery of a high-impact deliverable (e.g. Technical Brief, Incident Response Plan, or Content Outline).
Evaluate the current workflow state and determine the best next step:
- If research is missing or incomplete, plan steps and delegate to 'researcher'.
- If research is sufficient and draft is missing or being revised, delegate to 'writer'.
- If draft exists and has not been audited, delegate to 'reviewer'.
- If draft is audited and satisfactory, or revisions are exhausted, route to 'human_review'.
- If human has approved or edited, route to 'publisher'.
Always maintain high technical rigor and clarity.
"""


async def supervisor_node(state: AgentState) -> Dict[str, Any]:
    """Supervisor agent node that creates execution plans and routes tasks."""
    task = state.get("task", "")
    deliverable_type = state.get("deliverable_type", "technical_brief")
    provider = state.get("llm_provider")
    model_name = state.get("model_name")
    temp = state.get("temperature", 0.7)

    logger.info(f"[Supervisor] Evaluating task: {task[:60]}... (type: {deliverable_type})")

    llm = LLMFactory.get_model(
        provider=provider,
        model_name=model_name,
        temperature=temp,
        role="supervisor",
    )

    plan = state.get("plan", [])
    research_data = state.get("research_data", [])
    draft = state.get("draft", "")
    critique = state.get("critique")
    human_decision = state.get("human_decision")
    revision_count = state.get("revision_count", 0)
    max_revisions = state.get("max_revisions", 2)

    # 1. Routing logic determination
    if human_decision in ("approve", "edit"):
        next_agent = "publisher"
        reason = f"Human decision received ({human_decision}). Proceeding to publication."
    elif human_decision == "reject":
        next_agent = "writer"
        reason = "Human requested revisions. Routing back to Writer with feedback."
    elif not research_data:
        next_agent = "researcher"
        reason = "Context and factual data missing. Routing to Researcher."
    elif not draft:
        next_agent = "writer"
        reason = "Research gathered. Routing to Writer to create initial draft."
    elif draft and not critique:
        next_agent = "reviewer"
        reason = "Initial draft complete. Routing to Reviewer for quality audit."
    elif critique and "satisfactory" not in critique.lower() and revision_count < max_revisions:
        next_agent = "writer"
        reason = f"Critic requested revisions (attempt {revision_count + 1}/{max_revisions}). Routing to Writer."
    else:
        next_agent = "human_review"
        reason = "Draft ready for Human-in-the-Loop approval."

    # 2. Invoke LLM for planning / audit if initial run
    if not plan:
        prompt = (
            f"Deliverable: {deliverable_type}\n"
            f"Task: {task}\n"
            "Create a concise 3-point research & execution plan."
        )
        response = await llm.ainvoke(
            [
                SystemMessage(content=SUPERVISOR_SYSTEM_PROMPT),
                HumanMessage(content=prompt),
            ]
        )
        plan_text = response.content if isinstance(response.content, str) else str(response.content)
        new_plan = [line.strip() for line in plan_text.split("\n") if line.strip()][:4]
    else:
        new_plan = plan

    event = {
        "node": "supervisor",
        "agent": "Supervisor",
        "timestamp": datetime.utcnow().isoformat(),
        "action": "routing",
        "next_agent": next_agent,
        "detail": reason,
    }

    message = AIMessage(
        content=f"[Supervisor] {reason}",
        name="supervisor",
    )

    return {
        "plan": new_plan,
        "next_agent": next_agent,
        "status": f"routed_to_{next_agent}",
        "events": [event],
        "messages": [message],
    }
