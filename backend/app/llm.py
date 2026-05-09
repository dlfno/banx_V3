from __future__ import annotations

from langchain_core.language_models import BaseChatModel

from .config import settings


def build_chat_model(
    streaming: bool = True,
    temperature: float = 0.4,
    max_tokens: int = 2048,
) -> BaseChatModel:
    """Factory for the chat model. Supports Anthropic native and OpenRouter (OpenAI-compat).

    `max_tokens` aplica al output total (incluye reasoning_tokens en modelos con
    extended thinking). Default 2048 es suficiente para turnos de agentes (~200
    palabras + reasoning); para el Secretario que escribe la minuta completa
    súbelo a 6000+ para evitar truncamiento por finish_reason=length.
    """
    provider = settings.PROVIDER
    if provider == "anthropic":
        from langchain_anthropic import ChatAnthropic

        if not settings.ANTHROPIC_API_KEY:
            raise RuntimeError("PROVIDER=anthropic pero ANTHROPIC_API_KEY no está configurado")
        return ChatAnthropic(
            model=settings.MODEL,
            api_key=settings.ANTHROPIC_API_KEY,
            streaming=streaming,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=300,
        )

    if provider == "openrouter":
        from langchain_openai import ChatOpenAI

        if not settings.OPENROUTER_API_KEY:
            raise RuntimeError("PROVIDER=openrouter pero OPENROUTER_API_KEY no está configurado")
        return ChatOpenAI(
            model=settings.MODEL,
            base_url="https://openrouter.ai/api/v1",
            api_key=settings.OPENROUTER_API_KEY,
            streaming=streaming,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=300,
            default_headers={
                "HTTP-Referer": "http://localhost:5173",
                "X-Title": "Banxico Sim",
            },
        )

    raise RuntimeError(f"Provider no soportado: {provider}")
