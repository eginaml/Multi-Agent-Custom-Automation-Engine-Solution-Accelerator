"""Main application entry point for Simple Helpdesk (Agent Framework)."""
from fastapi import FastAPI
from contextlib import asynccontextmanager
from config.settings import settings
from api.router import router, orchestrator
from agents.orchestrator import Orchestrator
import logging
import uvicorn

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle.

    This handles:
    - Agent initialization on startup
    - Agent cleanup on shutdown
    """
    logger.info("=" * 60)
    logger.info("Starting Simple Helpdesk (Agent Framework)")
    logger.info("=" * 60)

    # Initialize orchestrator and agents
    global orchestrator
    try:
        logger.info("Initializing agents...")
        orch = Orchestrator()
        await orch.initialize()

        # Store in router module
        from api import router as router_module
        router_module.orchestrator = orch

        logger.info("✓ Agents initialized successfully")
        logger.info("=" * 60)
        logger.info(f"Server running at http://{settings.API_HOST}:{settings.API_PORT}")
        logger.info("API Documentation: http://localhost:8000/docs")
        logger.info("=" * 60)

    except Exception as ex:
        logger.error(f"Failed to initialize agents: {ex}")
        raise

    yield

    # Cleanup on shutdown
    logger.info("Shutting down...")
    try:
        from api import router as router_module
        if router_module.orchestrator:
            await router_module.orchestrator.cleanup()
        logger.info("✓ Cleanup complete")
    except Exception as ex:
        logger.warning(f"Error during cleanup: {ex}")


# Create FastAPI application
app = FastAPI(
    title="Simple Helpdesk Backend (Agent Framework)",
    description=(
        "Multi-agent helpdesk system with RAG and ticket creation "
        "powered by Azure AI Agent Framework"
    ),
    version="2.0.0",
    lifespan=lifespan,
)

# Include router
app.include_router(router)


if __name__ == "__main__":
    # Run the application
    uvicorn.run(
        "app:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.API_DEBUG,
        log_level="info",
    )
