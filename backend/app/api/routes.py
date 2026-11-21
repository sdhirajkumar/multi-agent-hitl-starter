"""FastAPI HTTP and SSE routing definitions."""
import uuid
from typing import Any, Dict, List
from fastapi import APIRouter, HTTPException, Query, status
from sse_starlette.sse import EventSourceResponse

from app.api.schemas import (
    CreateRunRequest,
    ResumeRunRequest,
    RunResponse,
    RunStateResponse,
)
from app.api.sse import run_manager
from app.core.logging import logger
from app.llm.factory import LLMFactory

router = APIRouter(tags=["Multi-Agent HITL Runs"])


@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check() -> Dict[str, str]:
    """Healthcheck endpoint."""
    return {"status": "ok", "service": "multi-agent-hitl-starter"}


@router.get("/providers", response_model=List[Dict[str, Any]])
async def list_providers() -> List[Dict[str, Any]]:
    """List available LLM providers, supported models, and API key status."""
    return LLMFactory.get_available_providers()


@router.post("/runs", response_model=RunResponse, status_code=status.HTTP_201_CREATED)
async def create_run(request: CreateRunRequest) -> RunResponse:
    """Initialize a new multi-agent orchestrator run and allocate a thread_id."""
    thread_id = str(uuid.uuid4())
    logger.info(f"Creating run {thread_id} for deliverable '{request.deliverable_type}'")

    await run_manager.create_run(
        thread_id=thread_id,
        task=request.task,
        deliverable_type=request.deliverable_type,
        llm_provider=request.llm_provider,
        model_name=request.model_name,
        temperature=request.temperature,
    )

    return RunResponse(
        thread_id=thread_id,
        status="initialized",
        deliverable_type=request.deliverable_type,
        message="Workflow initialized. Connect to /api/runs/{thread_id}/stream to execute and observe.",
    )


@router.get("/runs/{thread_id}/stream")
async def stream_run(thread_id: str):
    """Server-Sent Events (SSE) endpoint to stream agent node transitions,

    interrupt events, and output tokens in real-time.
    """
    logger.info(f"Client connected to SSE stream for thread: {thread_id}")
    return EventSourceResponse(
        run_manager.event_generator(thread_id),
        media_type="text/event-stream",
    )


@router.post("/runs/{thread_id}/resume", status_code=status.HTTP_200_OK)
async def resume_run(thread_id: str, request: ResumeRunRequest) -> Dict[str, Any]:
    """Resume execution of an interrupted workflow after human approval, edit, or rejection."""
    logger.info(f"Resuming run {thread_id} with action: {request.action}")

    # Validate that if edit was selected, edited_draft is provided
    if request.action == "edit" and not request.edited_draft:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Field 'edited_draft' must be provided when action is 'edit'.",
        )

    result = await run_manager.resume_run(
        thread_id=thread_id,
        action=request.action,
        edited_draft=request.edited_draft,
        feedback=request.feedback,
    )

    return result


@router.get("/runs/{thread_id}/state", response_model=RunStateResponse)
async def get_run_state(thread_id: str) -> RunStateResponse:
    """Inspect current checkpoint state, values, events, and pending interrupts."""
    state_data = await run_manager.get_state(thread_id)
    return RunStateResponse(**state_data)
