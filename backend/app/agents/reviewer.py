"""Reviewer / Critic Agent node definition."""
from datetime import datetime
from typing import Any, Dict
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from app.core.logging import logger
from app.graph.state import AgentState
from app.llm.factory import LLMFactory


REVIEWER_SYSTEM_PROMPT = """You are the Reviewer / Critic Agent in a specialized multi-agent workflow.
Your role is to critically audit the generated draft against rigorous industry criteria:
1. Completeness: Does it answer the task prompt thoroughly?
2. Actionability: Are the operational steps, tables, or architecture patterns unambiguous?
3. Technical Accuracy: Are metrics, SLAs, and technical recommendations realistic?
4. Quality & Formatting: Is the markdown structure professional?

Output format:
Provide concise bullet-point critique.
Conclude with either:
STATUS: SATISFACTORY (Ready for Human Approval)
OR
STATUS: REVISIONS_NEEDED (Specify exactly what the Writer must fix)
"""


async def reviewer_node(state: AgentState) -> Dict[str, Any]:
    """Reviewer agent node that audits draft quality."""
    task = state.get("task", "")
    deliverable_type = state.get("deliverable_type", "technical_brief")
    provider = state.get("llm_provider")
    model_name = state.get("model_name")
    temp = state.get("temperature", 0.3)

    draft = state.get("draft", "")
    revision_count = state.get("revision_count", 0)
    max_revisions = state.get("max_revisions", 2)

    logger.info(f"[Reviewer] Auditing draft for {deliverable_type} (revision: {revision_count})")

    llm = LLMFactory.get_model(
        provider=provider,
        model_name=model_name,
        temperature=temp,
        role="reviewer",
    )

    prompt = (
        f"Task: {task}\n"
        f"Deliverable Type: {deliverable_type}\n"
        f"Revision Cycle: {revision_count} (Max allowed revisions before forcing human gate: {max_revisions})\n\n"
        f"Draft to Audit:\n{draft}\n\n"
        "Perform quality critique and conclude with SATISFACTORY or REVISIONS_NEEDED."
    )

    response = await llm.ainvoke(
        [
            SystemMessage(content=REVIEWER_SYSTEM_PROMPT),
            HumanMessage(content=prompt),
        ]
    )

    critique_content = (
        response.content if isinstance(response.content, str) else str(response.content)
    )

    is_satisfactory = (
        "satisfactory" in critique_content.lower() or revision_count >= max_revisions
    )

    event = {
        "node": "reviewer",
        "agent": "Reviewer",
        "timestamp": datetime.utcnow().isoformat(),
        "action": "audit_completed",
        "is_satisfactory": is_satisfactory,
        "detail": (
            "Draft audit passed. Ready for Human Gate."
            if is_satisfactory
            else "Draft requires revision from Writer."
        ),
    }

    message = AIMessage(
        content=f"[Reviewer Critique]\n{critique_content}",
        name="reviewer",
    )

    return {
        "critique": critique_content,
        "status": "reviewed",
        "events": [event],
        "messages": [message],
    }
