"""Orchestrator for managing multiple agents and routing requests."""
from typing import AsyncIterator, Dict, Any, Optional
from agents.intent_classifier import IntentClassifier
from agents.rag_agent import RAGAgent
from agents.ticket_agent import TicketAgent
from agents.status_agent import StatusAgent
from services.safety_service import SafetyService
import logging

logger = logging.getLogger(__name__)


class Orchestrator:
    """Orchestrates RAG, Ticket, and Status agents based on user intent."""

    def __init__(self):
        self.intent_classifier = IntentClassifier()
        self.safety = SafetyService()
        self._rag_agent: Optional[RAGAgent] = None
        self._ticket_agent: Optional[TicketAgent] = None
        self._status_agent: Optional[StatusAgent] = None
        self.logger = logging.getLogger(__name__)

    async def initialize(self) -> None:
        """Initialize all agents."""
        self.logger.info("Initializing orchestrator and agents...")
        try:
            self._rag_agent = RAGAgent()
            await self._rag_agent.open()
            self.logger.info("RAG agent initialized")

            self._ticket_agent = TicketAgent()
            await self._ticket_agent.open()
            self.logger.info("Ticket agent initialized")

            self._status_agent = StatusAgent()
            await self._status_agent.open()
            self.logger.info("Status agent initialized")

            self.logger.info("Orchestrator initialization complete")

        except Exception as ex:
            self.logger.error(f"Failed to initialize orchestrator: {ex}")
            await self.cleanup()
            raise

    async def cleanup(self) -> None:
        """Cleanup all agents."""
        self.logger.info("Cleaning up orchestrator...")

        for agent, name in [
            (self._rag_agent, "RAG agent"),
            (self._ticket_agent, "Ticket agent"),
            (self._status_agent, "Status agent"),
        ]:
            if agent:
                try:
                    await agent.close()
                    self.logger.info(f"{name} closed")
                except Exception as ex:
                    self.logger.warning(f"Error closing {name}: {ex}")

        self.logger.info("Orchestrator cleanup complete")

    async def process(
        self, message: str, thread_id: Optional[str] = None
    ) -> AsyncIterator[Dict[str, Any]]:
        """Process user message and route to appropriate agent.

        Yields:
            Response updates from the agent
        """
        if not self._rag_agent or not self._ticket_agent or not self._status_agent:
            await self.initialize()

        # Screen for harmful content before routing to any agent
        safety_result = self.safety.check(message)
        if not safety_result.is_safe:
            self.logger.warning(
                f"Message blocked by content safety: {safety_result.blocked_categories}"
            )
            yield {
                "type": "blocked",
                "intent": "unknown",
                "message": (
                    "I'm sorry, I can't process that request as it contains content "
                    "that violates our usage policy."
                ),
                "blocked_categories": safety_result.blocked_categories,
            }
            return

        intent = await self.intent_classifier.classify(message)
        self.logger.info(f"Processing message with intent: {intent}")

        try:
            if intent == "rag":
                self.logger.info("Routing to RAG agent")
                async for update in self._rag_agent.invoke(message, thread_id):
                    update["intent"] = "rag"
                    yield update

            elif intent == "ticket":
                self.logger.info("Routing to Ticket agent")
                async for update in self._ticket_agent.invoke(message, thread_id):
                    update["intent"] = "ticket"
                    yield update

            elif intent == "status":
                self.logger.info("Routing to Status agent")
                async for update in self._status_agent.invoke(message, thread_id):
                    update["intent"] = "status"
                    yield update

        except Exception as ex:
            self.logger.error(f"Error processing message: {ex}")
            yield {
                "type": "error",
                "intent": intent,
                "message": f"Error processing your request: {str(ex)}",
            }

    async def __aenter__(self):
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.cleanup()
