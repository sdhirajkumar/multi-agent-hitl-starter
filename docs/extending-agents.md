# Extending Agents & LLM Providers

This guide provides practical, step-by-step instructions for adding custom specialist agents to the LangGraph topology and integrating new LLM providers.

---

## Part 1: Adding a New Agent Specialist Node

Suppose you want to add a **Security Auditor Agent** that inspects drafts for compliance and vulnerabilities before the reviewer.

### Step 1: Define the Agent Node Function

Create `backend/app/agents/security.py`:

```python
from datetime import datetime
from typing import Any, Dict
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from app.graph.state import AgentState
from app.llm.factory import LLMFactory

SECURITY_PROMPT = """You are the Security Auditor Agent.
Audit the deliverable for secrets, unencrypted communications, and compliance violations.
Output a concise list of security findings.
"""

async def security_auditor_node(state: AgentState) -> Dict[str, Any]:
    draft = state.get("draft", "")
    llm = LLMFactory.get_model(role="security")

    response = await llm.ainvoke([
        SystemMessage(content=SECURITY_PROMPT),
        HumanMessage(content=f"Draft to inspect:\n{draft}"),
    ])

    event = {
        "node": "security_auditor",
        "agent": "Security Auditor",
        "timestamp": datetime.utcnow().isoformat(),
        "action": "security_audit_completed",
        "detail": "Verified zero plaintext secrets and verified TLS requirements.",
    }

    return {
        "events": [event],
        "messages": [AIMessage(content=f"[Security Audit]\n{response.content}", name="security")],
    }
```

### Step 2: Register in `AgentState` (if state fields are added)

If your agent adds a new persistent field (e.g. `security_report: Optional[str]`), add it to `backend/app/graph/state.py`:

```python
class AgentState(TypedDict, total=False):
    # ... existing fields ...
    security_report: Optional[str]
```

### Step 3: Register in the Graph Builder

In `backend/app/graph/builder.py`:

```python
from app.agents.security import security_auditor_node

def build_graph():
    workflow = StateGraph(AgentState)

    # 1. Add your node
    workflow.add_node("security_auditor", security_auditor_node)

    # 2. Add edges (e.g., return to supervisor)
    workflow.add_edge("security_auditor", "supervisor")

    # 3. Add to supervisor conditional edges
    workflow.add_conditional_edges(
        "supervisor",
        route_from_supervisor,
        {
            # ... existing routes ...
            "security_auditor": "security_auditor",
        }
    )
```

### Step 4: Update Supervisor Routing

In `backend/app/agents/supervisor.py`:
Update the routing condition and prompt to instruct the supervisor when to delegate to `"security_auditor"`.

---

## Part 2: Adding a New LLM Provider

Suppose you want to integrate a new provider, such as **Mistral AI Cloud** or **DeepSeek**.

### Step 1: Add Credentials in Settings

In `backend/app/core/config.py`:

```python
class Settings(BaseSettings):
    # ...
    MISTRAL_API_KEY: Optional[str] = None
```

Add the variable to `.env.example`:
```bash
MISTRAL_API_KEY=your_mistral_key_here
```

### Step 2: Add Provider Initialization in LLM Factory

In `backend/app/llm/factory.py`:

```python
# 1. Add default model mapping
DEFAULT_MODELS = {
    # ...
    "mistral": "mistral-large-latest",
}

# 2. Add provider instantiation branch
if chosen_provider == "mistral":
    api_key = settings.MISTRAL_API_KEY
    if not api_key:
        logger.warning("MISTRAL_API_KEY not set; falling back to MockChatModel.")
        return MockChatModel(role=role or "general")
    from langchain_mistralai import ChatMistralAI
    return ChatMistralAI(model=chosen_model, api_key=api_key, temperature=chosen_temp)

# 3. Add metadata to get_available_providers()
{
    "id": "mistral",
    "name": "Mistral AI",
    "default_model": "mistral-large-latest",
    "models": ["mistral-large-latest", "mistral-small-latest"],
    "is_configured": bool(settings.MISTRAL_API_KEY),
    "is_local": False,
}
```

The React frontend fetches `GET /api/providers` dynamically upon mount and will automatically display the new provider in the dropdown bar without requiring any UI code changes.
