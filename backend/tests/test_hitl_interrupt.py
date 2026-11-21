"""Integration tests for Human-in-the-Loop (HITL) interrupt and resume actions."""
import pytest
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command
from app.graph.builder import create_agent_graph
from app.graph.state import AgentState


@pytest.mark.asyncio
async def test_hitl_action_approve(base_state: AgentState):
    """Submitting 'approve' should finalize the deliverable via publisher node."""
    checkpointer = MemorySaver()
    graph = create_agent_graph(checkpointer=checkpointer)
    config = {"configurable": {"thread_id": "test-hitl-approve"}}

    # Execute until interrupt
    async for _ in graph.astream(base_state, config=config, stream_mode="updates"):
        pass

    state_before = await graph.aget_state(config)
    assert state_before.next == ("human_review",)

    # Resume with APPROVE
    resume_cmd = Command(resume={"action": "approve"})
    async for _ in graph.astream(resume_cmd, config=config, stream_mode="updates"):
        pass

    state_after = await graph.aget_state(config)
    # Graph should have reached END
    assert state_after.next == ()
    assert state_after.values["status"] == "completed"
    assert state_after.values["final_output"] is not None
    assert state_after.values["human_decision"] == "approve"


@pytest.mark.asyncio
async def test_hitl_action_edit(base_state: AgentState):
    """Submitting 'edit' should override draft with human edits and publish."""
    checkpointer = MemorySaver()
    graph = create_agent_graph(checkpointer=checkpointer)
    config = {"configurable": {"thread_id": "test-hitl-edit"}}

    # Execute until interrupt
    async for _ in graph.astream(base_state, config=config, stream_mode="updates"):
        pass

    custom_edited_draft = "# Human Edited Operational Blueprint\nDirect human modifications."
    resume_cmd = Command(
        resume={
            "action": "edit",
            "edited_draft": custom_edited_draft,
        }
    )
    async for _ in graph.astream(resume_cmd, config=config, stream_mode="updates"):
        pass

    state_after = await graph.aget_state(config)
    assert state_after.next == ()
    assert state_after.values["final_output"] == custom_edited_draft
    assert state_after.values["human_decision"] == "edit"


@pytest.mark.asyncio
async def test_hitl_action_reject_routes_back_to_writer(base_state: AgentState):
    """Submitting 'reject' with feedback should loop back to writer to revise."""
    checkpointer = MemorySaver()
    graph = create_agent_graph(checkpointer=checkpointer)
    config = {"configurable": {"thread_id": "test-hitl-reject"}}

    # Execute until first interrupt
    async for _ in graph.astream(base_state, config=config, stream_mode="updates"):
        pass

    state_1 = await graph.aget_state(config)
    first_draft = state_1.values["draft"]

    # Resume with REJECT and human feedback
    feedback = "Please add specific escalation contacts and reduce P99 target to < 50ms."
    resume_cmd = Command(
        resume={
            "action": "reject",
            "feedback": feedback,
        }
    )

    # Stream second cycle - it will route back through supervisor -> writer -> reviewer -> human_review
    async for _ in graph.astream(resume_cmd, config=config, stream_mode="updates"):
        pass

    state_2 = await graph.aget_state(config)
    # It paused again at human_review for the revised draft!
    assert state_2.next == ("human_review",)
    assert state_2.values["revision_count"] >= 1
