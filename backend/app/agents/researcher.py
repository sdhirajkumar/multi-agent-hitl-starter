"""Researcher Agent node definition."""
from datetime import datetime
from typing import Any, Dict
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from app.core.logging import logger
from app.graph.state import AgentState
from app.llm.factory import LLMFactory


RESEARCHER_SYSTEM_PROMPT = """You are the Researcher Agent in a specialized multi-agent workflow.
Your role is to collect concrete technical facts, industry standards, architectural patterns,
performance targets, and operational constraints for the requested deliverable.
Provide 4 to 6 concise, highly specific, factual bullet points.
Avoid vague generalities. Ground your points in realistic metrics and standard engineering practices.
"""


async def researcher_node(state: AgentState) -> Dict[str, Any]:
    """Researcher agent node that gathers context and operational data."""
    task = state.get("task", "")
    deliverable_type = state.get("deliverable_type", "technical_brief")
    provider = state.get("llm_provider")
    model_name = state.get("model_name")
    temp = state.get("temperature", 0.5)

    logger.info(f"[Researcher] Gathering context for '{deliverable_type}': {task[:60]}...")

    llm = LLMFactory.get_model(
        provider=provider,
        model_name=model_name,
        temperature=temp,
        role="researcher",
    )

    plan = state.get("plan", [])
    plan_context = "\n".join(plan) if plan else "Identify key architecture, latency, and reliability requirements."

    prompt = (
        f"Deliverable Type: {deliverable_type}\n"
        f"Goal: {task}\n\n"
        f"Execution Plan Context:\n{plan_context}\n\n"
        "Provide factual research findings and operational parameters."
    )

    response = await llm.ainvoke(
        [
            SystemMessage(content=RESEARCHER_SYSTEM_PROMPT),
            HumanMessage(content=prompt),
        ]
    )

    content = response.content if isinstance(response.content, str) else str(response.content)
    raw_lines = [line.strip() for line in content.split("\n") if line.strip().startswith(("-", "*", "•"))]
    findings = raw_lines if raw_lines else [content]

    event = {
        "node": "researcher",
        "agent": "Researcher",
        "timestamp": datetime.utcnow().isoformat(),
        "action": "research_gathered",
        "item_count": len(findings),
        "detail": f"Gathered {len(findings)} research findings and operational targets.",
    }

    message = AIMessage(
        content=f"[Researcher Findings]\n{content}",
        name="researcher",
    )

    return {
        "research_data": findings,
        "status": "research_completed",
        "events": [event],
        "messages": [message],
    }
