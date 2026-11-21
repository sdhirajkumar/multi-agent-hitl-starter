"""Server-Sent Events (SSE) streaming and run lifecycle manager."""
import asyncio
import json
from datetime import datetime
from typing import Any, AsyncGenerator, Dict, Optional
from langgraph.types import Command

from app.core.config import settings
from app.core.logging import logger
from app.graph.builder import create_agent_graph


class RunManager:
    """Orchestrates graph executions, thread-level event streaming,

    interrupt detection, and state recovery.
    """

    def __init__(self):
        self._event_queues: Dict[str, asyncio.Queue] = {}
        self._initial_inputs: Dict[str, Dict[str, Any]] = {}
        self._tasks: Dict[str, asyncio.Task] = {}
        self._graph = None

    def get_graph(self):
        """Lazily initialize compiled graph with memory or sqlite saver."""
        if self._graph is None:
            # MemorySaver enables high-speed in-process state tracking with zero external dependencies
            from langgraph.checkpoint.memory import MemorySaver

            checkpointer = MemorySaver()
            self._graph = create_agent_graph(checkpointer=checkpointer)
            logger.info("Compiled StateGraph with Checkpointer initialized.")
        return self._graph

    async def create_run(
        self,
        thread_id: str,
        task: str,
        deliverable_type: str,
        llm_provider: Optional[str] = None,
        model_name: Optional[str] = None,
        temperature: Optional[float] = 0.7,
    ) -> Dict[str, Any]:
        """Register a new run and prepare event channel."""
        initial_state = {
            "task": task,
            "deliverable_type": deliverable_type,
            "llm_provider": llm_provider or settings.LLM_PROVIDER,
            "model_name": model_name,
            "temperature": temperature or 0.7,
            "plan": [],
            "research_data": [],
            "draft": "",
            "critique": None,
            "revision_count": 0,
            "max_revisions": settings.MAX_REVISIONS,
            "human_feedback": None,
            "human_decision": None,
            "status": "initialized",
            "events": [],
            "messages": [],
        }

        self._initial_inputs[thread_id] = initial_state
        self._event_queues[thread_id] = asyncio.Queue()

        # Emit initial start event
        await self._emit_event(
            thread_id,
            "run_started",
            {
                "thread_id": thread_id,
                "task": task,
                "deliverable_type": deliverable_type,
                "llm_provider": initial_state["llm_provider"],
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

        return initial_state

    async def _emit_event(self, thread_id: str, event_type: str, data: Dict[str, Any]):
        """Push an SSE event to the thread's event queue."""
        queue = self._event_queues.get(thread_id)
        if queue:
            payload = {
                "event": event_type,
                "data": json.dumps(data),
            }
            await queue.put(payload)

    async def execute_or_resume(
        self,
        thread_id: str,
        input_data: Optional[Any] = None,
    ):
        """Execute graph stream until next interrupt or completion."""
        graph = self.get_graph()
        config = {"configurable": {"thread_id": thread_id}}

        try:
            # If no input_data passed, use registered initial state
            current_input = input_data
            if current_input is None and thread_id in self._initial_inputs:
                current_input = self._initial_inputs.pop(thread_id)

            logger.info(f"[RunManager] Streaming execution for thread: {thread_id}")

            async for chunk in graph.astream(
                current_input,
                config=config,
                stream_mode="updates",
            ):
                for node_name, node_update in chunk.items():
                    logger.debug(f"[Chunk] Node completed: {node_name}")
                    await self._emit_event(
                        thread_id,
                        "node_finish",
                        {
                            "thread_id": thread_id,
                            "node": node_name,
                            "update": {
                                k: v
                                for k, v in node_update.items()
                                if k != "messages"
                            },
                            "timestamp": datetime.utcnow().isoformat(),
                        },
                    )

            # Inspect state after chunk stream ends
            state = await graph.aget_state(config)
            interrupts = [
                item.value for task in state.tasks for item in task.interrupts
            ]

            if interrupts:
                interrupt_val = interrupts[0]
                logger.info(
                    f"[RunManager] Graph paused at HITL interrupt for thread: {thread_id}"
                )
                await self._emit_event(
                    thread_id,
                    "interrupt",
                    {
                        "thread_id": thread_id,
                        "interrupt_data": interrupt_val,
                        "draft": state.values.get("draft", ""),
                        "revision_count": state.values.get("revision_count", 0),
                        "status": "paused_for_human_review",
                        "timestamp": datetime.utcnow().isoformat(),
                    },
                )
            elif not state.next:
                # Graph reached END
                logger.info(
                    f"[RunManager] Graph completed successfully for thread: {thread_id}"
                )
                await self._emit_event(
                    thread_id,
                    "complete",
                    {
                        "thread_id": thread_id,
                        "status": "completed",
                        "final_output": state.values.get("final_output", ""),
                        "revision_count": state.values.get("revision_count", 0),
                        "timestamp": datetime.utcnow().isoformat(),
                    },
                )

        except Exception as e:
            logger.error(
                f"[RunManager] Execution error on thread {thread_id}: {e}",
                exc_info=True,
            )
            await self._emit_event(
                thread_id,
                "error",
                {
                    "thread_id": thread_id,
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat(),
                },
            )

    async def resume_run(
        self,
        thread_id: str,
        action: str,
        edited_draft: Optional[str] = None,
        feedback: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Submit human decision and resume graph execution."""
        resume_payload = {
            "action": action,
            "edited_draft": edited_draft,
            "feedback": feedback,
        }

        await self._emit_event(
            thread_id,
            "human_decision_submitted",
            {
                "thread_id": thread_id,
                "action": action,
                "feedback": feedback,
                "has_edits": bool(edited_draft),
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

        command = Command(resume=resume_payload)
        # Run execution asynchronously in background task while returning response
        task = asyncio.create_task(self.execute_or_resume(thread_id, command))
        self._tasks[thread_id] = task

        return {
            "thread_id": thread_id,
            "status": f"resumed_with_{action}",
            "action": action,
        }

    async def get_state(self, thread_id: str) -> Dict[str, Any]:
        """Fetch current checkpoint state, values, and interrupt status."""
        graph = self.get_graph()
        config = {"configurable": {"thread_id": thread_id}}
        state = await graph.aget_state(config)

        interrupts = [
            item.value for task in state.tasks for item in task.interrupts
        ]
        is_interrupted = len(interrupts) > 0
        interrupt_data = interrupts[0] if is_interrupted else None

        values = state.values or {}

        status = "not_started"
        if values:
            if is_interrupted:
                status = "interrupted"
            elif not state.next:
                status = "completed"
            else:
                status = values.get("status", "running")

        return {
            "thread_id": thread_id,
            "status": status,
            "is_interrupted": is_interrupted,
            "interrupt_data": interrupt_data,
            "draft": values.get("draft"),
            "final_output": values.get("final_output"),
            "plan": values.get("plan", []),
            "research_data": values.get("research_data", []),
            "revision_count": values.get("revision_count", 0),
            "events": values.get("events", []),
            "next_nodes": list(state.next) if state.next else [],
        }

    async def event_generator(
        self, thread_id: str
    ) -> AsyncGenerator[Dict[str, str], None]:
        """Generate Server-Sent Events for the specified thread."""
        if thread_id not in self._event_queues:
            self._event_queues[thread_id] = asyncio.Queue()

        queue = self._event_queues[thread_id]

        # If run was just created with initial input and no task is actively running, start it
        if thread_id in self._initial_inputs and thread_id not in self._tasks:
            task = asyncio.create_task(self.execute_or_resume(thread_id))
            self._tasks[thread_id] = task

        while True:
            try:
                # Wait for next event with a periodic keepalive ping
                event_dict = await asyncio.wait_for(queue.get(), timeout=15.0)
                yield event_dict

                # If completed or error, break after delivering event
                if event_dict["event"] in ("complete", "error"):
                    break
            except asyncio.TimeoutError:
                yield {
                    "event": "ping",
                    "data": json.dumps({"timestamp": datetime.utcnow().isoformat()}),
                }
            except asyncio.CancelledError:
                break


# Global singleton manager
run_manager = RunManager()
