"""Ticket Agent using Azure OpenAI Assistants API with function calling."""
from typing import AsyncIterator, Dict, Any, Optional
from agents.base_agent import BaseAgent
from tools.devops_tool import DEVOPS_TOOL_DEFINITION, TOOL_EXECUTORS
import logging
import json

logger = logging.getLogger(__name__)


class TicketAgent(BaseAgent):
    """Ticket creation agent using function calling via Azure OpenAI Assistants."""

    def __init__(self):
        super().__init__(
            agent_name="Ticket Agent",
            agent_description="Creates support tickets in Azure DevOps",
            agent_instructions=(
                "You are a helpful IT support assistant that creates support tickets. "
                "When a user asks to create a ticket or report an issue, extract the relevant "
                "information and use the create_devops_ticket function to create a ticket. "
                "After creating a ticket, provide the ticket number and URL to the user."
            ),
        )

    async def _after_open(self) -> None:
        """Create the assistant with the DevOps function tool."""
        try:
            self.logger.info("Creating Ticket assistant with DevOps function tool...")
            assistant = await self._client.beta.assistants.create(
                model=self.model,
                name=self.agent_name,
                instructions=self.agent_instructions,
                tools=[DEVOPS_TOOL_DEFINITION],
            )
            self._agent_id = assistant.id
            self._agent = assistant
            self.logger.info(f"Created Ticket assistant (id={assistant.id})")
        except Exception as ex:
            self.logger.error(f"Failed to create Ticket agent: {ex}")
            raise

    async def _before_close(self) -> None:
        """Delete the server-side assistant."""
        if self._agent_id and self._client:
            try:
                await self._client.beta.assistants.delete(self._agent_id)
                self.logger.info(f"Deleted assistant (id={self._agent_id})")
            except Exception as ex:
                self.logger.warning(f"Failed to delete assistant: {ex}")

    async def invoke(
        self, message: str, thread_id: Optional[str] = None
    ) -> AsyncIterator[Dict[str, Any]]:
        """Create a ticket based on the user's request.

        Yields:
            text_delta, function_call, final dicts
        """
        if not self._agent_id:
            raise RuntimeError("Agent not initialized. Call open() first.")

        try:
            # Create or reuse thread
            if thread_id:
                self.logger.debug(f"Using existing thread: {thread_id}")
            else:
                thread = await self._client.beta.threads.create()
                thread_id = thread.id
                self.logger.debug(f"Created new thread: {thread_id}")

            await self._client.beta.threads.messages.create(
                thread_id=thread_id,
                role="user",
                content=message,
            )

            self.logger.info(f"Running Ticket agent for: {message[:60]}...")
            full_response = ""
            ticket_info = {}

            # Initial run stream
            async with self._client.beta.threads.runs.stream(
                thread_id=thread_id,
                assistant_id=self._agent_id,
            ) as stream:
                run_id = None
                async for event in stream:
                    if event.event == "thread.run.created":
                        run_id = event.data.id

                    elif event.event == "thread.message.delta":
                        for block in event.data.delta.content or []:
                            if block.type == "text":
                                text = block.text.value
                                full_response += text
                                yield {"type": "text_delta", "text": text}

                    elif event.event == "thread.run.requires_action":
                        run_id = event.data.id
                        tool_calls = (
                            event.data.required_action.submit_tool_outputs.tool_calls
                        )
                        tool_outputs = []

                        for tc in tool_calls:
                            function_name = tc.function.name
                            function_args = json.loads(tc.function.arguments)

                            self.logger.info(
                                f"Executing: {function_name}({function_args})"
                            )

                            if function_name in TOOL_EXECUTORS:
                                result = await TOOL_EXECUTORS[function_name](
                                    **function_args
                                )
                                if result.get("success"):
                                    ticket_info = {
                                        "ticket_id": result.get("ticket_id"),
                                        "ticket_url": result.get("ticket_url"),
                                    }
                                tool_outputs.append(
                                    {
                                        "tool_call_id": tc.id,
                                        "output": json.dumps(result),
                                    }
                                )
                                yield {
                                    "type": "function_call",
                                    "function": function_name,
                                    "arguments": function_args,
                                    "result": result,
                                }

                        # Submit and stream the continuation
                        async with self._client.beta.threads.runs.submit_tool_outputs_stream(
                            thread_id=thread_id,
                            run_id=run_id,
                            tool_outputs=tool_outputs,
                        ) as cont_stream:
                            async for cont_event in cont_stream:
                                if cont_event.event == "thread.message.delta":
                                    for block in cont_event.data.delta.content or []:
                                        if block.type == "text":
                                            text = block.text.value
                                            full_response += text
                                            yield {"type": "text_delta", "text": text}

            yield {
                "type": "final",
                "message": full_response,
                "ticket_id": ticket_info.get("ticket_id"),
                "ticket_url": ticket_info.get("ticket_url"),
                "thread_id": thread_id,
            }

        except Exception as ex:
            self.logger.error(f"Error in Ticket invoke: {ex}")
            yield {
                "type": "error",
                "message": f"Error creating ticket: {str(ex)}",
            }
