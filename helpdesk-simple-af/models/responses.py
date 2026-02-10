"""Response models for API endpoints."""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class QueryResponse(BaseModel):
    """Response model for query endpoint."""

    intent: str = Field(..., description="Detected user intent", examples=["rag"])
    message: str = Field(
        ..., description="Response message from the agent", examples=["Here's how to reset your password..."]
    )
    sources: Optional[List[Dict[str, Any]]] = Field(
        None, description="Source documents used for RAG responses"
    )
    ticket_id: Optional[int] = Field(None, description="Created ticket ID if applicable")
    ticket_url: Optional[str] = Field(None, description="URL to the created ticket")
    fallback: bool = Field(
        False, description="Whether the response is a fallback due to no relevant information"
    )
    suggest_ticket: bool = Field(
        False, description="Whether to suggest creating a support ticket"
    )
    thread_id: Optional[str] = Field(
        None, description="Conversation thread ID for multi-turn conversations"
    )


class TicketResponse(BaseModel):
    """Response model for ticket creation."""

    ticket_id: int = Field(..., description="Created ticket ID")
    ticket_url: str = Field(..., description="URL to view the ticket")
    message: str = Field(..., description="Confirmation message")


class HealthResponse(BaseModel):
    """Response model for health check."""

    status: str = Field(..., description="Service status", examples=["healthy"])
    framework: str = Field(
        ..., description="Agent framework in use", examples=["Azure AI Agent Framework"]
    )
