"""LLM client factory and invocation utilities with retry logic."""

from typing import AsyncGenerator, Optional

from langchain_core.messages import BaseMessage
from langchain_openrouter import ChatOpenRouter
from tenacity import (
    AsyncRetrying,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from app.config import get_settings
from app.exceptions import LLMInvocationError


def get_llm(
    model_id: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: Optional[int] = None,
) -> ChatOpenRouter:
    """Factory function to create a ChatOpenRouter LLM instance.

    Args:
        model_id: Model ID to use. If None, uses MODEL_ID from config.
        temperature: Sampling temperature (0.0 to 2.0).
        max_tokens: Maximum tokens to generate.

    Returns:
        ChatOpenRouter: Configured LLM instance.

    Raises:
        ConfigurationError: If OPENROUTER_API_KEY is not set.
    """
    settings = get_settings()
    effective_model_id = model_id or settings.model_id

    # Create the LLM instance
    # Note: ChatOpenRouter reads OPENROUTER_API_KEY from environment automatically
    llm = ChatOpenRouter(
        model=effective_model_id,
        temperature=temperature,
        max_tokens=max_tokens,
        max_retries=0,  # Retry at LLM level (fallback to our wrapper retry)
    )

    return llm


async def async_invoke_with_retry(
    llm: ChatOpenRouter, messages: list[BaseMessage]
) -> str:
    """Invoke the LLM with automatic retry on failure.

    Implements exponential backoff with a maximum of 3 attempts.
    Each retry has a wait time of 1-10 seconds.

    Args:
        llm: The ChatOpenRouter LLM instance.
        messages: List of LangChain messages to send.

    Returns:
        str: The generated response content.

    Raises:
        LLMInvocationError: If all retries are exhausted.
    """
    retry_config = AsyncRetrying(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type(Exception),
        reraise=True,
    )

    try:
        async for attempt in retry_config:
            with attempt:
                response = await llm.ainvoke(messages)
                return response.content
    except Exception as e:
        raise LLMInvocationError(
            f"Failed to invoke LLM after retries: {str(e)}", original_error=e
        ) from e

    # This should never be reached, but satisfy type checker
    raise LLMInvocationError("Unexpected retry failure")


async def async_stream(
    llm: ChatOpenRouter, messages: list[BaseMessage]
) -> AsyncGenerator[str, None]:
    """Stream responses from the LLM.

    Args:
        llm: The ChatOpenRouter LLM instance.
        messages: List of LangChain messages to send.

    Yields:
        str: Chunks of the generated response.

    Raises:
        LLMInvocationError: If streaming fails.
    """
    try:
        async for chunk in llm.astream(messages):
            if chunk.content:
                yield chunk.content
    except Exception as e:
        raise LLMInvocationError(
            f"Failed to stream from LLM: {str(e)}", original_error=e
        ) from e
