"""Integration tests for graph compilation and execution progression."""
import pytest
from langgraph.checkpoint.memory import MemorySaver
from app.graph.builder import create_agent_graph
from app.graph.state import AgentState


@pytest.mark.asyncio
async def test_graph_pauses_at_hitl_interrupt(base_state: AgentState):
    """The graph should traverse supervisor -> researcher -> writer -> reviewer -> human_review

    and halt dynamically at the interrupt gate.
    """
    checkpointer = MemorySaver()
    graph = create_agent_graph(checkpointer=checkpointer)
    thread_id = "test-thread-graph-pause-1"
    config = {"configurable": {"thread_id": thread_id}}

    # Stream execution until interrupt
    events_collected = []
    async for chunk in graph.astream(
        base_state,
        config=config,
        stream_mode="updates",
    ):
        events_collected.append(chunk)

    # Inspect paused state
    state = await graph.aget_state(config)
    assert state.next == ("human_review",)
    assert len(state.tasks) > 0
    assert len(state.tasks[0].interrupts) > 0

    interrupt_data = state.tasks[0].interrupts[0].value
    assert interrupt_data["type"] == "human_approval"
    assert "draft" in interrupt_data
    assert len(interrupt_data["draft"]) > 0
