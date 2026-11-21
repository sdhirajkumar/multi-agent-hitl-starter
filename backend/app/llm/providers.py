"""LLM Mock Provider and Provider Adapters."""
import asyncio
from typing import Any, AsyncIterator, Dict, List, Optional
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.outputs import ChatGeneration, ChatResult


class MockChatModel(BaseChatModel):
    """Deterministic, zero-credential simulated LLM for testing, local demos,

    and offline runs. Produces realistic agent responses tailored to each role.
    """

    role: str = "general"
    model_name: str = "mock-agent-v1"

    @property
    def _llm_type(self) -> str:
        return "mock_chat_model"

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[Any] = None,
        **kwargs: Any,
    ) -> ChatResult:
        content = self._generate_response(messages)
        message = AIMessage(content=content)
        generation = ChatGeneration(message=message)
        return ChatResult(generations=[generation])

    async def _agenerate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[Any] = None,
        **kwargs: Any,
    ) -> ChatResult:
        # Small non-blocking delay to simulate realistic agent thinking in SSE stream
        await asyncio.sleep(0.3)
        return self._generate(messages, stop=stop, run_manager=run_manager, **kwargs)

    def _generate_response(self, messages: List[BaseMessage]) -> str:
        last_content = messages[-1].content if messages else ""
        if isinstance(last_content, list):
            last_content = " ".join(str(item) for item in last_content)
        last_str = str(last_content).lower()

        if self.role == "supervisor":
            return (
                "PLAN:\n"
                "1. Gather technical specifications, industry benchmarks, and operational constraints.\n"
                "2. Synthesize gathered data into a structured deliverable with executive summary and actionable steps.\n"
                "3. Perform quality audit against domain requirements.\n"
                "ROUTING DECISION: Delegate context gathering to Researcher Agent."
            )

        elif self.role == "researcher":
            return (
                "### RESEARCH FINDINGS:\n"
                "- Architecture Standard: Modular microservices with decoupled state machines and idempotent consumers.\n"
                "- Performance Target: P99 latency < 120ms under 10k RPS load peak.\n"
                "- Reliability Patterns: Exponential backoff with jitter, dead-letter queues, and dynamic circuit breakers.\n"
                "- Observability: Distributed tracing via OpenTelemetry and semantic state transition logs.\n"
                "- Security Compliance: Zero-trust mTLS, least-privilege IAM scopes, and encrypted checkpoints at rest."
            )

        elif self.role == "writer":
            has_critique = "critique" in last_str or "feedback" in last_str or "revision" in last_str
            revision_note = (
                "\n> **Revision Note:** Updated based on human critique and reviewer recommendations. "
                "Enhanced technical depth and concrete recovery procedures.\n"
                if has_critique
                else ""
            )

            return (
                f"# Deliverable Draft: Comprehensive Operational & Technical Specification\n\n"
                f"{revision_note}\n"
                f"## 1. Executive Summary\n"
                f"This document provides the canonical operational blueprint designed to ensure high availability, "
                f"fault tolerance, and measurable performance across distributed services. It defines clear roles, "
                f"SLOs, and escalation matrices.\n\n"
                f"## 2. Key Architecture Pillars\n"
                f"- **Stateful Orchestration**: LangGraph-driven cyclic graph with durable checkpoints.\n"
                f"- **Resilience & Fault Isolation**: Asynchronous queue workers with automated failover.\n"
                f"- **Security & Governance**: Policy enforcement points and full audit logging of state transitions.\n\n"
                f"## 3. Incident & Operational Procedures\n"
                f"| Phase | Trigger | Action Required | Responsible Agent/Team |\n"
                f"| :--- | :--- | :--- | :--- |\n"
                f"| Detection | SLO breach > 2% | Alert triage & root-cause isolation | On-Call Lead |\n"
                f"| Mitigation | Service degradation | Failover to secondary cluster / throttle traffic | Automation Runner |\n"
                f"| Resolution | Health metrics green | Post-mortem generation and checkpointer compaction | Incident Commander |\n\n"
                f"## 4. Verification & Validation Metrics\n"
                f"- P99 Latency: < 120ms\n"
                f"- MTTR (Mean Time to Recover): < 15 minutes\n"
                f"- Checkpoint Recovery SLA: < 500ms"
            )

        elif self.role == "reviewer":
            return (
                "### REVIEW CRITIQUE:\n"
                "- Structure & Depth: High quality, covers executive summary, architecture, and operational runbook.\n"
                "- Compliance: Aligns with P99 latency targets and failure recovery guidelines.\n"
                "- Recommendation: The draft is solid. Minor recommendation to verify escalation contacts during HITL review.\n"
                "STATUS: SATISFACTORY (Ready for Human Approval)"
            )

        return f"Response processed for role '{self.role}' on prompt: {last_content[:100]}..."
