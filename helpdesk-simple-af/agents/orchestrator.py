"""Orchestrator for managing multiple agents and routing requests."""
from typing import AsyncIterator, Dict, Any, Optional
from agents.intent_classifier import IntentClassifier
from agents.rag_agent import RAGAgent
from agents.ticket_agent import TicketAgent
from agents.status_agent import StatusAgent
from services.safety_service import SafetyService
from services.session_store import SessionStore
import logging

logger = logging.getLogger(__name__)


class Orchestrator:
    """Orchestrates RAG, Ticket, and Status agents based on user intent.

    Uses SessionStore for in-session memory: when a session_id is provided,
    the orchestrator reuses existing OpenAI threads so the agent has full
    conversation context for follow-up messages.
    """

    def __init__(self):
        self.intent_classifier = IntentClassifier()
        self.safety = SafetyService()
        self.session_store = SessionStore()
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
        self,
        message: str,
        session_id: Optional[str] = None,
        thread_id: Optional[str] = None,
    ) -> AsyncIterator[Dict[str, Any]]:
        """Process user message and route to appropriate agent.

        Args:
            message: User message text.
            session_id: Optional session identifier. When provided, the
                orchestrator remembers thread_ids across multiple calls
                in the same session, enabling multi-turn conversations.
            thread_id: Optional explicit thread_id override (legacy).
                If session_id is also provided, session_id takes precedence.

        Yields:
            Response updates from the agent.
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

        # Look up existing thread from session store (if session_id provided)
        if session_id and not thread_id:
            thread_id = self.session_store.get_thread(session_id, intent)
            if thread_id:
                self.logger.info(
                    f"Reusing thread {thread_id} for session {session_id}:{intent}"
                )

        try:
            if intent == "rag":
                self.logger.info("Routing to RAG agent")
                async for update in self._rag_agent.invoke(message, thread_id):
                    update["intent"] = "rag"
                    # Persist thread_id in session store for follow-ups
                    if session_id and update.get("type") == "final" and update.get("thread_id"):
                        self.session_store.set_thread(session_id, "rag", update["thread_id"])
                    if session_id:
                        update["session_id"] = session_id
                    yield update

            elif intent == "ticket":
                self.logger.info("Routing to Ticket agent")
                async for update in self._ticket_agent.invoke(message, thread_id):
                    update["intent"] = "ticket"
                    if session_id and update.get("type") == "final" and update.get("thread_id"):
                        self.session_store.set_thread(session_id, "ticket", update["thread_id"])
                    if session_id:
                        update["session_id"] = session_id
                    yield update

            elif intent == "status":
                self.logger.info("Routing to Status agent")
                async for update in self._status_agent.invoke(message, thread_id):
                    update["intent"] = "status"
                    if session_id:
                        update["session_id"] = session_id
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
