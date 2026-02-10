"""Request models for API endpoints."""
from pydantic import BaseModel, Field
from typing import Optional


class QueryRequest(BaseModel):
    """Request model for query endpoint."""

    message: str = Field(
        ...,
        min_length=1,
        description="User message to process",
        examples=["How do I reset my password?"],
    )
    thread_id: Optional[str] = Field(
        None,
        description="Conversation thread ID for multi-turn conversations",
        examples=["thread_abc123"],
    )


class TicketRequest(BaseModel):
    """Request model for direct ticket creation."""

    title: str = Field(
        ..., min_length=1, description="Ticket title", examples=["Password reset issue"]
    )
    description: str = Field(
        ...,
        min_length=1,
        description="Ticket description",
        examples=["User unable to reset password through self-service portal"],
    )
    priority: int = Field(
        2, ge=1, le=4, description="Ticket priority (1=Critical, 2=High, 3=Medium, 4=Low)"
    )
