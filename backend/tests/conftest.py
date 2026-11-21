"""Pytest fixtures and configuration."""
import os
import sys
from pathlib import Path
import pytest
from httpx import AsyncClient, ASGITransport

# Ensure backend root is on sys.path
backend_path = Path(__file__).resolve().parent.parent
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

# Force mock LLM provider for tests
os.environ["LLM_PROVIDER"] = "mock"
os.environ["DATABASE_PATH"] = ":memory:"

from app.main import app
from app.graph.state import AgentState


@pytest.fixture
def base_state() -> AgentState:
    """Provide a standard initial state fixture."""
    return {
        "task": "Build an Incident Response Plan for critical Redis cluster failover",
        "deliverable_type": "incident_response_plan",
        "llm_provider": "mock",
        "model_name": "mock-agent-v1",
        "temperature": 0.0,
        "plan": [],
        "research_data": [],
        "draft": "",
        "critique": None,
        "revision_count": 0,
        "max_revisions": 2,
        "human_feedback": None,
        "human_decision": None,
        "status": "initialized",
        "events": [],
        "messages": [],
    }


@pytest.fixture
async def async_client():
    """Async HTTP client for testing FastAPI endpoints."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
