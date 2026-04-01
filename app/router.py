"""API routes for the OpenRouter service."""

import json
from typing import Optional

from fastapi import APIRouter, Depends
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from starlette.responses import StreamingResponse

from app.config import Settings, get_settings
from app.exceptions import LLMInvocationError
from app.llm_client import async_invoke_with_retry, async_stream, get_llm
from app.schemas import (
    ChatRequest,
    ChatResponse,
    HealthCheckResponse,
    Message,
    UsageMetadata,
)

router = APIRouter(prefix="/v1", tags=["chat"])


def _convert_messages(messages: list[Message]) -> list:
    """Convert API Message objects to LangChain message objects.

    Args:
        messages: List of API Message objects.

    Returns:
        list: List of LangChain message objects.
    """
    lc_messages = []
    for msg in messages:
        if msg.role == "system":
            lc_messages.append(SystemMessage(content=msg.content))
        elif msg.role == "user":
            lc_messages.append(HumanMessage(content=msg.content))
        elif msg.role == "assistant":
            lc_messages.append(AIMessage(content=msg.content))
    return lc_messages


@router.get("/health")
async def health_check(settings: Settings = Depends(get_settings)) -> HealthCheckResponse:
    """Health check endpoint.

    Returns:
        HealthCheckResponse: Service health status.
    """
    return HealthCheckResponse(
        status="healthy",
        model=settings.model_id,
        environment=settings.environment,
    )


@router.post("/chat", response_model=ChatResponse)
async def chat_completion(
    request: ChatRequest,
    settings: Settings = Depends(get_settings),
) -> ChatResponse:
    """Handle chat completion request.

    Args:
        request: Chat request payload.
        settings: Application settings (injected).

    Returns:
        ChatResponse: Generated response with usage metadata.

    Raises:
        LLMInvocationError: If LLM invocation fails.
    """
    # Get the model to use (request override or config default)
    model_id = request.model or settings.model_id

    # Create LLM instance
    llm = get_llm(
        model_id=model_id,
        temperature=request.temperature,
        max_tokens=request.max_tokens,
    )

    # Convert messages to LangChain format
    lc_messages = _convert_messages(request.messages)

    # Invoke LLM with retry logic
    content = await async_invoke_with_retry(llm, lc_messages)

    # Extract usage metadata if available
    usage = None
    # Note: Usage metadata extraction depends on the response object
    # For now, we return None; in production, you'd parse the response_metadata

    return ChatResponse(
        content=content,
        model=model_id,
        usage=usage,
        finish_reason="stop",
    )


@router.post("/chat/stream")
async def chat_stream(
    request: ChatRequest,
    settings: Settings = Depends(get_settings),
) -> StreamingResponse:
    """Handle streaming chat completion request.

    Returns SSE (Server-Sent Events) formatted stream.

    Args:
        request: Chat request payload.
        settings: Application settings (injected).

    Returns:
        StreamingResponse: SSE stream with response chunks.

    Raises:
        LLMInvocationError: If LLM invocation fails.
    """
    # Get the model to use
    model_id = request.model or settings.model_id

    # Create LLM instance
    llm = get_llm(
        model_id=model_id,
        temperature=request.temperature,
        max_tokens=request.max_tokens,
    )

    # Convert messages to LangChain format
    lc_messages = _convert_messages(request.messages)

    async def event_generator():
        """Generate SSE events from the LLM stream."""
        try:
            async for chunk in async_stream(llm, lc_messages):
                # Format as SSE data line
                data = json.dumps({"content": chunk, "model": model_id})
                yield f"data: {data}\n\n"

            # Send completion marker
            yield "data: [DONE]\n\n"

        except LLMInvocationError as e:
            # Send error event
            error_data = json.dumps(
                {"error": e.message, "code": e.error_code}
            )
            yield f"data: {error_data}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
