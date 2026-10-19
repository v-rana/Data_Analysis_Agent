"""LLM construction.

Two independent LLM selections exist:

* ``agent_llm``  - used by the SQL/debugger agents. Controlled only by
  ``AGENT_LLM_PROVIDER`` / ``AGENT_LLM_MODEL`` and unaffected by
  ``LLM_PROVIDER``.
* ``llm``        - the selectable LLM (``LLM_PROVIDER`` / ``LLM_MODEL``),
  used outside agents (e.g. conversation summarization).

Instances are resolved lazily per provider so that a provider which is not
configured (missing API key) cannot break modules that use a different one.
"""
from __future__ import annotations

from functools import cache
from typing import Callable, Mapping

from langchain_core.language_models.chat_models import BaseChatModel

from config import settings

DEFAULT_MODELS: Mapping[str, str] = {
    "google": "gemini-3.5-flash",
    "openai": "gpt-4o",
    "deepseek": "deepseek-chat",
}


class UnsupportedProviderError(ValueError):
    """Raised when an unknown LLM provider is requested."""


def supported_providers() -> tuple[str, ...]:
    return tuple(PROVIDERS)


def _build_google(api_key: str, model: str) -> BaseChatModel:
    from langchain_google_genai import ChatGoogleGenerativeAI

    return ChatGoogleGenerativeAI(
        api_key=api_key,
        model=model,
        temperature=settings.LLM_TEMPERATURE,
        max_tokens=settings.LLM_MAX_TOKENS,
        timeout=None,
        max_retries=settings.LLM_MAX_RETRIES,
    )


def _build_openai(api_key: str, model: str) -> BaseChatModel:
    from langchain_openai import ChatOpenAI

    return ChatOpenAI(
        api_key=api_key,
        model=model,
        temperature=settings.LLM_TEMPERATURE,
        max_tokens=settings.LLM_MAX_TOKENS,
        timeout=None,
        max_retries=settings.LLM_MAX_RETRIES,
    )


def _build_deepseek(api_key: str, model: str) -> BaseChatModel:
    # DeepSeek exposes an OpenAI-compatible API.
    from langchain_openai import ChatOpenAI

    return ChatOpenAI(
        base_url=settings.DEEPSEEK_BASE_URL,
        api_key=api_key,
        model=model,
        temperature=settings.LLM_TEMPERATURE,
        max_tokens=settings.LLM_MAX_TOKENS,
        timeout=None,
        max_retries=settings.LLM_MAX_RETRIES,
    )


PROVIDERS: Mapping[str, str] = {
    "google": "GOOGLE_API_KEY",
    "openai": "OPENAI_API_KEY",
    "deepseek": "DEEPSEEK_API_KEY",
}

_FACTORIES: Mapping[str, Callable[[str, str], BaseChatModel]] = {
    "google": _build_google,
    "openai": _build_openai,
    "deepseek": _build_deepseek,
}


def _api_key(provider: str) -> str:
    return getattr(settings, PROVIDERS[provider], "") or ""


def build_llm(
    provider: str,
    model: str | None = None,
    *,
    purpose: str = "llm",
) -> BaseChatModel:
    """Build a chat model for ``provider``.

    Raises:
        UnsupportedProviderError: if the provider is unknown.
        RuntimeError: if the provider API key is not configured.
    """
    normalized = str(provider).strip().lower()
    factory = _FACTORIES.get(normalized)
    if factory is None:
        raise UnsupportedProviderError(
            f"Unsupported LLM provider {provider!r} for {purpose}. "
            f"Supported: {', '.join(_FACTORIES)}."
        )

    api_key = _api_key(normalized)
    if not api_key:
        raise RuntimeError(
            f"Missing API key for LLM provider {normalized!r} ({purpose}). "
            f"Set {PROVIDERS[normalized]} in the environment."
        )

    return factory(api_key, model or DEFAULT_MODELS[normalized])


@cache
def _cached_llm(provider: str, model: str | None) -> BaseChatModel:
    return build_llm(provider, model, purpose="selectable llm")


def get_llm(
    provider: str | None = None,
    model: str | None = None,
) -> BaseChatModel:
    """Return a cached chat model; defaults to the configured ``LLM_PROVIDER``."""
    return _cached_llm(provider or settings.LLM_PROVIDER, model)


@cache
def get_agent_llm() -> BaseChatModel:
    """Return the agent chat model, pinned to ``AGENT_LLM_PROVIDER``."""
    return build_llm(
        settings.AGENT_LLM_PROVIDER,
        settings.AGENT_LLM_MODEL or None,
        purpose="agents",
    )


def __getattr__(name: str):
    # Backwards-compatible module-level bindings resolved lazily on first use.
    if name == "llm":
        return get_llm()
    if name == "agent_llm":
        return get_agent_llm()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
