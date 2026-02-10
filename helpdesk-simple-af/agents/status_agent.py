"""Status Agent — checks ADO ticket status and explains it in plain English."""
import re
from typing import AsyncIterator, Dict, Any, Optional
from agents.base_agent import BaseAgent
from services.devops_service import DevOpsService
import logging

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """You are a friendly IT helpdesk assistant explaining support ticket status to end users.

The ticket states in our system mean:
- To Do / New: Your ticket has been received and is in the queue waiting to be picked up.
- Active / In Progress / Doing: A technician is actively working on your issue right now.
- Resolved / Done / Closed: Your issue has been addressed and marked as resolved.
- On Hold / Blocked: Work is paused — the team may be waiting for more information from you or a third party.

Given a ticket's title and current state, write 2-3 clear, empathetic sentences that:
1. Tell the user exactly where their ticket is in the process
2. Set expectations for what happens next (or what action they may need to take)

Be concise and reassuring. Do not repeat the state name literally — explain it in human terms."""


class StatusAgent(BaseAgent):
    """Checks an Azure DevOps ticket and gives a plain-English status explanation.

    Does not use a persistent server-side assistant — uses a single chat
    completion call per request since no thread history is needed.
    """

    def __init__(self):
        super().__init__(
            agent_name="Status Agent",
            agent_description="Checks support ticket status in Azure DevOps",
            agent_instructions=_SYSTEM_PROMPT,
        )

    async def _after_open(self) -> None:
        """No server-side assistant needed for status checks."""
        self.logger.info("Status agent ready (chat completion mode)")

    async def _before_close(self) -> None:
        """Nothing to delete."""
        pass

    async def invoke(
        self, message: str, thread_id: Optional[str] = None
    ) -> AsyncIterator[Dict[str, Any]]:
        """Check ticket status and stream an LLM explanation.

        Yields:
            text_delta dicts while streaming, then a final dict with ticket details.
        """
        if not self._client:
            raise RuntimeError("Agent not initialized. Call open() first.")

        # Extract ticket number
        match = re.search(r"#?(\d+)", message)
        if not match:
            yield {
                "type": "final",
                "intent": "status",
                "message": "Please provide a ticket number, e.g. 'Check ticket #1234'",
                "fallback": True,
            }
            return

        ticket_id = int(match.group(1))
        self.logger.info(f"Checking status for ticket #{ticket_id}")

        # Fetch from DevOps
        try:
            svc = DevOpsService()
            ticket = svc.get_work_item(ticket_id)
        except Exception as ex:
            self.logger.error(f"Failed to fetch ticket #{ticket_id}: {ex}")
            yield {
                "type": "error",
                "intent": "status",
                "message": f"Could not retrieve ticket #{ticket_id}. Error: {str(ex)}",
            }
            return

        state = ticket.get("state", "Unknown")
        title = ticket.get("title", "")
        assigned_to = ticket.get("assigned_to", "Unassigned")
        url = ticket.get("url", "")

        # Stream LLM explanation
        user_prompt = (
            f"Ticket #{ticket_id}: {title}\n"
            f"State: {state}\n"
            f"Assigned to: {assigned_to}\n\n"
            f"Explain this status to the user."
        )

        full_response = ""
        try:
            stream = await self._client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=200,
                temperature=0.3,
                stream=True,
            )
            async for chunk in stream:
                delta = chunk.choices[0].delta.content if chunk.choices else None
                if delta:
                    full_response += delta
                    yield {"type": "text_delta", "text": delta}

        except Exception as ex:
            self.logger.error(f"LLM call failed: {ex}")
            full_response = f"Ticket #{ticket_id} '{title}' is currently: {state}."
            yield {"type": "text_delta", "text": full_response}

        yield {
            "type": "final",
            "intent": "status",
            "message": full_response,
            "ticket_id": ticket_id,
            "ticket_state": state,
            "ticket_title": title,
            "ticket_url": url,
        }
