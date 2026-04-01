"""Pydantic schemas for API requests and responses."""

from typing import Literal, Optional

from pydantic import BaseModel, Field


class Message(BaseModel):
    """A message in a conversation."""

    role: Literal["system", "user", "assistant"] = Field(
        ..., description="Role of the message sender"
    )
    content: str = Field(..., description="Message content")


class UsageMetadata(BaseModel):
    """Token usage metadata from the LLM response."""

    input_tokens: int = Field(..., description="Number of input tokens used")
    output_tokens: int = Field(..., description="Number of output tokens generated")
    total_tokens: int = Field(..., description="Total tokens used (input + output)")


class ChatRequest(BaseModel):
    """Request payload for chat completion."""

    messages: list[Message] = Field(
        ..., description="List of messages in the conversation"
    )
    model: Optional[str] = Field(
        default=None,
        description="Model ID override. If not provided, uses the default MODEL_ID from config.",
    )
    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="Sampling temperature (0.0 to 2.0)",
    )
    max_tokens: Optional[int] = Field(
        default=None, ge=1, description="Maximum number of tokens to generate"
    )


class ChatResponse(BaseModel):
    """Response payload for chat completion."""

    content: str = Field(..., description="Generated response content")
    model: str = Field(..., description="Model ID that was used")
    usage: Optional[UsageMetadata] = Field(
        default=None, description="Token usage information"
    )
    finish_reason: Optional[str] = Field(
        default=None, description="Reason the model stopped generating (e.g., 'stop', 'length')"
    )


class HealthCheckResponse(BaseModel):
    """Health check response."""

    status: str = Field(..., description="Service status")
    model: str = Field(..., description="Default model in use")
    environment: str = Field(..., description="Deployment environment")
