"""Centralized LLM model factory with runtime provider selection."""
from typing import Any, Dict, List, Optional
from langchain_core.language_models.chat_models import BaseChatModel

from app.core.config import settings
from app.core.logging import logger
from app.llm.providers import MockChatModel


class LLMFactory:
    """Factory to instantiate chat models based on provider string,

    per-request overrides, and agent role.
    """

    DEFAULT_MODELS: Dict[str, str] = {
        "mock": "mock-agent-v1",
        "openai": "gpt-4o",
        "anthropic": "claude-3-5-sonnet-20241022",
        "gemini": "gemini-1.5-flash",
        "bedrock": "anthropic.claude-3-5-sonnet-20240620-v1:0",
        "ollama": "llama3:latest",
    }

    ROLE_FAST_MODELS: Dict[str, Dict[str, str]] = {
        "openai": {"researcher": "gpt-4o-mini"},
        "anthropic": {"researcher": "claude-3-5-haiku-20241022"},
        "gemini": {"researcher": "gemini-1.5-flash"},
    }

    @classmethod
    def get_model(
        cls,
        provider: Optional[str] = None,
        model_name: Optional[str] = None,
        temperature: Optional[float] = None,
        role: Optional[str] = None,
    ) -> BaseChatModel:
        """Instantiate and return the configured BaseChatModel."""
        chosen_provider = (provider or settings.LLM_PROVIDER or "mock").lower().strip()
        chosen_temp = temperature if temperature is not None else settings.TEMPERATURE

        # Check for role-specific model override
        chosen_model = model_name
        if not chosen_model and role:
            role_attr = f"{role.upper()}_MODEL"
            if hasattr(settings, role_attr) and getattr(settings, role_attr):
                chosen_model = getattr(settings, role_attr)
            elif (
                chosen_provider in cls.ROLE_FAST_MODELS
                and role in cls.ROLE_FAST_MODELS[chosen_provider]
            ):
                chosen_model = cls.ROLE_FAST_MODELS[chosen_provider][role]

        if not chosen_model:
            chosen_model = settings.MODEL_NAME or cls.DEFAULT_MODELS.get(
                chosen_provider, "default"
            )

        # 1. Mock / Demo provider
        if chosen_provider in ("mock", "demo", "test"):
            return MockChatModel(
                role=role or "general",
                model_name=chosen_model,
            )

        # 2. OpenAI
        if chosen_provider == "openai":
            api_key = settings.OPENAI_API_KEY
            if not api_key:
                logger.warning(
                    "OPENAI_API_KEY is not set. Falling back to MockChatModel."
                )
                return MockChatModel(role=role or "general", model_name="mock-fallback")
            try:
                from langchain_openai import ChatOpenAI

                return ChatOpenAI(
                    model=chosen_model,
                    temperature=chosen_temp,
                    api_key=api_key,
                )
            except ImportError:
                logger.warning("langchain-openai not installed; falling back to mock.")
                return MockChatModel(role=role or "general", model_name="mock-fallback")

        # 3. Anthropic
        if chosen_provider == "anthropic":
            api_key = settings.ANTHROPIC_API_KEY
            if not api_key:
                logger.warning(
                    "ANTHROPIC_API_KEY is not set. Falling back to MockChatModel."
                )
                return MockChatModel(role=role or "general", model_name="mock-fallback")
            try:
                from langchain_anthropic import ChatAnthropic

                return ChatAnthropic(
                    model=chosen_model,
                    temperature=chosen_temp,
                    api_key=api_key,
                )
            except ImportError:
                logger.warning(
                    "langchain-anthropic not installed; falling back to mock."
                )
                return MockChatModel(role=role or "general", model_name="mock-fallback")

        # 4. Google Gemini
        if chosen_provider in ("gemini", "google"):
            api_key = settings.GOOGLE_API_KEY
            if not api_key:
                logger.warning(
                    "GOOGLE_API_KEY is not set. Falling back to MockChatModel."
                )
                return MockChatModel(role=role or "general", model_name="mock-fallback")
            try:
                from langchain_google_genai import ChatGoogleGenerativeAI

                return ChatGoogleGenerativeAI(
                    model=chosen_model,
                    temperature=chosen_temp,
                    google_api_key=api_key,
                )
            except ImportError:
                logger.warning(
                    "langchain-google-genai not installed; falling back to mock."
                )
                return MockChatModel(role=role or "general", model_name="mock-fallback")

        # 5. AWS Bedrock
        if chosen_provider == "bedrock":
            try:
                from langchain_community.chat_models import BedrockChat

                return BedrockChat(
                    model_id=chosen_model,
                    region_name=settings.AWS_REGION,
                    model_kwargs={"temperature": chosen_temp},
                )
            except Exception as e:
                logger.warning(
                    f"AWS Bedrock initialization failed ({e}); falling back to mock."
                )
                return MockChatModel(role=role or "general", model_name="mock-fallback")

        # 6. Ollama (local)
        if chosen_provider == "ollama":
            try:
                from langchain_community.chat_models import ChatOllama

                return ChatOllama(
                    model=chosen_model,
                    base_url=settings.OLLAMA_BASE_URL,
                    temperature=chosen_temp,
                )
            except Exception as e:
                logger.warning(
                    f"Ollama initialization failed ({e}); falling back to mock."
                )
                return MockChatModel(role=role or "general", model_name="mock-fallback")

        # Fallback
        logger.warning(
            f"Unknown provider '{chosen_provider}'. Defaulting to MockChatModel."
        )
        return MockChatModel(role=role or "general", model_name="mock-fallback")

    @classmethod
    def get_available_providers(cls) -> List[Dict[str, Any]]:
        """Return metadata on all supported providers and their configuration status."""
        return [
            {
                "id": "mock",
                "name": "Simulated (Zero Credentials)",
                "default_model": cls.DEFAULT_MODELS["mock"],
                "models": ["mock-agent-v1", "mock-agent-fast"],
                "is_configured": True,
                "is_local": True,
            },
            {
                "id": "openai",
                "name": "OpenAI",
                "default_model": cls.DEFAULT_MODELS["openai"],
                "models": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "o1-mini"],
                "is_configured": bool(settings.OPENAI_API_KEY),
                "is_local": False,
            },
            {
                "id": "anthropic",
                "name": "Anthropic Claude",
                "default_model": cls.DEFAULT_MODELS["anthropic"],
                "models": [
                    "claude-3-5-sonnet-20241022",
                    "claude-3-5-haiku-20241022",
                    "claude-3-opus-20240229",
                ],
                "is_configured": bool(settings.ANTHROPIC_API_KEY),
                "is_local": False,
            },
            {
                "id": "gemini",
                "name": "Google Gemini",
                "default_model": cls.DEFAULT_MODELS["gemini"],
                "models": ["gemini-1.5-pro", "gemini-1.5-flash", "gemini-2.0-flash"],
                "is_configured": bool(settings.GOOGLE_API_KEY),
                "is_local": False,
            },
            {
                "id": "bedrock",
                "name": "AWS Bedrock",
                "default_model": cls.DEFAULTMODELS["bedrock"] if hasattr(cls, "DEFAULTMODELS") else cls.DEFAULT_MODELS["bedrock"],
                "models": [
                    "anthropic.claude-3-5-sonnet-20240620-v1:0",
                    "amazon.titan-text-express-v1",
                ],
                "is_configured": bool(
                    settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY
                ),
                "is_local": False,
            },
            {
                "id": "ollama",
                "name": "Ollama (Local Inference)",
                "default_model": cls.DEFAULT_MODELS["ollama"],
                "models": ["llama3:latest", "mistral:latest", "qwen2.5:latest"],
                "is_configured": True,  # Assumes local server
                "is_local": True,
            },
        ]
