"""Unit tests for individual agent node behavior."""
import pytest
from app.agents.supervisor import supervisor_node
from app.agents.researcher import researcher_node
from app.agents.writer import writer_node
from app.agents.reviewer import reviewer_node
from app.graph.state import AgentState


@pytest.mark.asyncio
async def test_supervisor_initial_routing(base_state: AgentState):
    """Supervisor should route to researcher if research data is absent."""
    result = await supervisor_node(base_state)
    assert result["next_agent"] == "researcher"
    assert len(result["plan"]) > 0
    assert len(result["events"]) == 1
    assert result["events"][0]["node"] == "supervisor"


@pytest.mark.asyncio
async def test_researcher_node(base_state: AgentState):
    """Researcher should gather factual operational findings."""
    result = await researcher_node(base_state)
    assert "research_data" in result
    assert len(result["research_data"]) > 0
    assert result["status"] == "research_completed"
    assert len(result["events"]) == 1


@pytest.mark.asyncio
async def test_writer_initial_draft(base_state: AgentState):
    """Writer should produce markdown draft and increment revision count."""
    state_with_research = {
        **base_state,
        "research_data": [
            "P99 latency < 120ms target",
            "Multi-AZ failover automation",
        ],
    }
    result = await writer_node(state_with_research)
    assert "draft" in result
    assert len(result["draft"]) > 100
    assert "Executive Summary" in result["draft"]
    assert result["status"] == "draft_compiled"


@pytest.mark.asyncio
async def test_reviewer_node(base_state: AgentState):
    """Reviewer should audit draft and produce critique."""
    state_with_draft = {
        **base_state,
        "draft": "# Draft Title\n## 1. Executive Summary\nOperational details here.",
    }
    result = await reviewer_node(state_with_draft)
    assert "critique" in result
    assert "SATISFACTORY" in result["critique"]
    assert result["events"][0]["is_satisfactory"] is True
