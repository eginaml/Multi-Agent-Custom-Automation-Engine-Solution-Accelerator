"""API router for helpdesk endpoints."""
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from models import QueryRequest, QueryResponse, HealthResponse
from agents.orchestrator import Orchestrator
import logging
import json

logger = logging.getLogger(__name__)

router = APIRouter()

# Global orchestrator instance (initialized on startup)
orchestrator: Orchestrator = None


async def get_orchestrator() -> Orchestrator:
    """Get or create orchestrator instance.

    Returns:
        Orchestrator instance
    """
    global orchestrator
    if orchestrator is None:
        orchestrator = Orchestrator()
        await orchestrator.initialize()
    return orchestrator


@router.get("/", response_model=dict)
async def root():
    """Root endpoint."""
    return {
        "service": "Simple Helpdesk Backend (Agent Framework)",
        "version": "2.0.0",
        "framework": "Azure AI Agent Framework",
        "description": "Multi-agent helpdesk with RAG and ticket creation using Azure AI Agent Framework",
        "endpoints": {
            "POST /query": "Process user query (non-streaming)",
            "POST /query/stream": "Process user query (streaming)",
            "GET /health": "Health check",
        },
    }


@router.get("/health", response_model=HealthResponse)
async def health():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        framework="Azure AI Agent Framework",
    )


@router.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    """Process user query (non-streaming).

    This endpoint waits for the full response before returning.

    Args:
        request: Query request with message and optional thread_id

    Returns:
        Complete query response
    """
    logger.info(f"Processing query: {request.message[:50]}...")

    try:
        orch = await get_orchestrator()

        # Collect all updates
        intent = None
        message = ""
        sources = []
        ticket_id = None
        ticket_url = None
        thread_id = request.thread_id
        fallback = False
        suggest_ticket = False

        async for update in orch.process(request.message, request.thread_id):
            # Track intent
            if "intent" in update:
                intent = update["intent"]

            # Accumulate text
            if update.get("type") == "text_delta":
                message += update.get("text", "")

            # Final response
            elif update.get("type") == "final":
                message = update.get("message", message)
                sources = update.get("sources", [])
                ticket_id = update.get("ticket_id")
                ticket_url = update.get("ticket_url")
                thread_id = update.get("thread_id", thread_id)
                fallback = update.get("fallback", False)

                # Suggest ticket if RAG fallback
                if fallback and intent == "rag":
                    suggest_ticket = True

            # Error response
            elif update.get("type") == "error":
                raise HTTPException(status_code=500, detail=update.get("message"))

        return QueryResponse(
            intent=intent or "unknown",
            message=message,
            sources=sources if sources else None,
            ticket_id=ticket_id,
            ticket_url=ticket_url,
            thread_id=thread_id,
            fallback=fallback,
            suggest_ticket=suggest_ticket,
        )

    except Exception as ex:
        logger.error(f"Error processing query: {ex}")
        raise HTTPException(status_code=500, detail=str(ex))


@router.post("/query/stream")
async def query_stream(request: QueryRequest):
    """Process user query with streaming response.

    This endpoint streams the response as Server-Sent Events (SSE).

    Args:
        request: Query request with message and optional thread_id

    Returns:
        Streaming response with updates
    """
    logger.info(f"Processing streaming query: {request.message[:50]}...")

    async def generate():
        """Generate SSE events."""
        try:
            orch = await get_orchestrator()

            async for update in orch.process(request.message, request.thread_id):
                # Send each update as SSE event
                event_data = json.dumps(update)
                yield f"data: {event_data}\n\n"

            # Send completion marker
            yield "data: {\"type\": \"done\"}\n\n"

        except Exception as ex:
            logger.error(f"Error in streaming query: {ex}")
            error_data = json.dumps({"type": "error", "message": str(ex)})
            yield f"data: {error_data}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )
