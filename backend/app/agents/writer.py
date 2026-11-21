"""Writer / Synthesizer Agent node definition."""
from datetime import datetime
from typing import Any, Dict
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from app.core.logging import logger
from app.graph.state import AgentState
from app.llm.factory import LLMFactory


WRITER_SYSTEM_PROMPT = """You are the Writer / Synthesizer Agent in a specialized multi-agent workflow.
Your role is to produce a high-caliber, publication-ready markdown deliverable based on the task and research context.
Structure requirements:
1. Clear Executive Summary or Overview
2. Architectural Pillars or Key Sections
3. Step-by-step Procedures, Tables, or Operational Runbooks
4. Measurable SLAs, Verification Metrics, or Next Steps
If reviewer critique or human feedback is provided, you MUST directly address and incorporate that feedback.
Format in clean, professional GitHub-flavored Markdown.
"""


async def writer_node(state: AgentState) -> Dict[str, Any]:
    """Writer agent node that synthesizes findings into a structured draft."""
    task = state.get("task", "")
    deliverable_type = state.get("deliverable_type", "technical_brief")
    provider = state.get("llm_provider")
    model_name = state.get("model_name")
    temp = state.get("temperature", 0.7)

    research_data = state.get("research_data", [])
    critique = state.get("critique")
    human_feedback = state.get("human_feedback")
    current_draft = state.get("draft", "")
    revision_count = state.get("revision_count", 0)

    is_revision = bool(current_draft and (critique or human_feedback))
    new_revision_count = revision_count + 1 if is_revision else revision_count

    logger.info(
        f"[Writer] Drafting {deliverable_type} (revision: {new_revision_count}, "
        f"has_human_feedback={bool(human_feedback)})"
    )

    llm = LLMFactory.get_model(
        provider=provider,
        model_name=model_name,
        temperature=temp,
        role="writer",
    )

    research_context = "\n".join(f"- {r}" for r in research_data) if research_data else "No prior research."

    prompt_parts = [
        f"Task / Deliverable: {task} ({deliverable_type})",
        f"\nResearch Context:\n{research_context}",
    ]

    if current_draft:
        prompt_parts.append(f"\nExisting Draft:\n{current_draft}")

    if critique:
        prompt_parts.append(f"\nReviewer Critique to Address:\n{critique}")

    if human_feedback:
        prompt_parts.append(
            f"\nCRITICAL Human-in-the-Loop Feedback to Incorporate:\n{human_feedback}"
        )

    prompt_parts.append(
        "\nGenerate the complete, polished Markdown document now."
    )

    full_prompt = "\n".join(prompt_parts)

    response = await llm.ainvoke(
        [
            SystemMessage(content=WRITER_SYSTEM_PROMPT),
            HumanMessage(content=full_prompt),
        ]
    )

    draft_content = response.content if isinstance(response.content, str) else str(response.content)

    event_detail = (
        f"Draft revised (Cycle {new_revision_count}) incorporating "
        f"{'human critique' if human_feedback else 'reviewer critique'}."
        if is_revision
        else f"Initial draft compiled ({len(draft_content)} characters)."
    )

    event = {
        "node": "writer",
        "agent": "Writer",
        "timestamp": datetime.utcnow().isoformat(),
        "action": "draft_compiled",
        "revision": new_revision_count,
        "detail": event_detail,
    }

    message = AIMessage(
        content=f"[Writer] Draft compiled (Revision {new_revision_count}). Length: {len(draft_content)} chars.",
        name="writer",
    )

    return {
        "draft": draft_content,
        "revision_count": new_revision_count,
        "human_decision": None,  # Reset decision after addressing feedback
        "critique": None,        # Reset critique for next review cycle
        "status": "draft_compiled",
        "events": [event],
        "messages": [message],
    }
