"""Integration tests for FastAPI REST endpoints."""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_endpoint(async_client: AsyncClient):
    """GET /api/health returns 200 OK."""
    response = await async_client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


@pytest.mark.asyncio
async def test_providers_endpoint(async_client: AsyncClient):
    """GET /api/providers returns available LLM providers."""
    response = await async_client.get("/api/providers")
    assert response.status_code == 200
    providers = response.json()
    assert isinstance(providers, list)
    provider_ids = [p["id"] for p in providers]
    assert "mock" in provider_ids
    assert "openai" in provider_ids
    assert "anthropic" in provider_ids


@pytest.mark.asyncio
async def test_create_run_and_state(async_client: AsyncClient):
    """POST /api/runs creates a run and returns a valid thread_id."""
    payload = {
        "task": "Develop an automated incident response plan for network partitions",
        "deliverable_type": "incident_response_plan",
        "llm_provider": "mock",
    }
    create_res = await async_client.post("/api/runs", json=payload)
    assert create_res.status_code == 201
    data = create_res.json()
    assert "thread_id" in data
    thread_id = data["thread_id"]

    # Check state endpoint
    state_res = await async_client.get(f"/api/runs/{thread_id}/state")
    assert state_res.status_code == 200
    state_data = state_res.json()
    assert state_data["thread_id"] == thread_id


@pytest.mark.asyncio
async def test_resume_endpoint_validation(async_client: AsyncClient):
    """POST /api/runs/{thread_id}/resume requires edited_draft when action is 'edit'."""
    payload = {
        "task": "Test task",
        "deliverable_type": "technical_brief",
        "llm_provider": "mock",
    }
    create_res = await async_client.post("/api/runs", json=payload)
    thread_id = create_res.json()["thread_id"]

    # Edit without edited_draft should fail with 400
    res = await async_client.post(
        f"/api/runs/{thread_id}/resume",
        json={"action": "edit"},
    )
    assert res.status_code == 400
