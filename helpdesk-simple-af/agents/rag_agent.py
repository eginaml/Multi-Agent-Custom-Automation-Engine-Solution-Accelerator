"""RAG Agent using Azure OpenAI Assistants API with function-based search."""
from typing import AsyncIterator, Dict, Any, Optional
from agents.base_agent import BaseAgent
from services.search_service import SearchService
from config.settings import settings
import logging
import json

logger = logging.getLogger(__name__)

_SEARCH_TOOL = {
    "type": "function",
    "function": {
        "name": "search_knowledge_base",
        "description": (
            "Search the IT helpdesk knowledge base for relevant documentation "
            "and step-by-step instructions. Use this to answer user questions."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query to find relevant documentation",
                }
            },
            "required": ["query"],
        },
    },
}


class RAGAgent(BaseAgent):
    """RAG agent using Azure AI Search via function calling.

    Uses the Assistants API function tool to call SearchService, which does
    vector/semantic search against Azure AI Search directly with API key auth.
    """

    def __init__(self):
        super().__init__(
            agent_name="RAG Agent",
            agent_description="Answers questions using knowledge base documentation",
            agent_instructions=(
                "You are a helpful IT support assistant. "
                "Use the search_knowledge_base tool to find relevant documentation "
                "and answer user questions with clear, step-by-step instructions. "
                "If the search returns no relevant results, clearly state that and "
                "suggest the user create a support ticket."
            ),
        )
        self._thread_id: Optional[str] = None

    async def _after_open(self) -> None:
        """Create the assistant with the search function tool."""
        try:
            self.logger.info("Creating RAG assistant with search tool...")
            assistant = await self._client.beta.assistants.create(
                model=self.model,
                name=self.agent_name,
                instructions=self.agent_instructions,
                tools=[_SEARCH_TOOL],
            )
            self._agent_id = assistant.id
            self._agent = assistant
            self.logger.info(f"Created RAG assistant (id={assistant.id})")
        except Exception as ex:
            self.logger.error(f"Failed to create RAG agent: {ex}")
            raise

    async def _before_close(self) -> None:
        """Delete the server-side assistant."""
        if self._agent_id and self._client:
            try:
                await self._client.beta.assistants.delete(self._agent_id)
                self.logger.info(f"Deleted assistant (id={self._agent_id})")
            except Exception as ex:
                self.logger.warning(f"Failed to delete assistant: {ex}")

    async def _execute_search(self, query: str) -> str:
        """Execute search and return JSON string result."""
        try:
            svc = SearchService()
            result = svc.search(
                query,
                top_k=settings.RAG_TOP_K,
                score_threshold=settings.RAG_SCORE_THRESHOLD,
            )
            docs = result.get("documents", [])
            if docs:
                return json.dumps({
                    "found": True,
                    "documents": [
                        {
                            "title": d.get("title", ""),
                            "content": d.get("content", ""),
                        }
                        for d in docs
                    ],
                })
            return json.dumps({"found": False, "documents": []})
        except Exception as ex:
            self.logger.error(f"Search error: {ex}")
            return json.dumps({"found": False, "error": str(ex)})

    async def invoke(
        self, message: str, thread_id: Optional[str] = None
    ) -> AsyncIterator[Dict[str, Any]]:
        """Answer a question using RAG.

        Yields:
            text_delta, final dicts
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

            self.logger.info(f"Running RAG agent for: {message[:60]}...")
            full_response = ""

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
                            if tc.function.name == "search_knowledge_base":
                                args = json.loads(tc.function.arguments)
                                output = await self._execute_search(args.get("query", ""))
                                tool_outputs.append(
                                    {"tool_call_id": tc.id, "output": output}
                                )

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
                "sources": [],
                "thread_id": thread_id,
                "fallback": (
                    not full_response
                    or "cannot find" in full_response.lower()
                    or "no relevant" in full_response.lower()
                ),
            }

        except Exception as ex:
            self.logger.error(f"Error in RAG invoke: {ex}")
            yield {
                "type": "error",
                "message": f"Error processing query: {str(ex)}",
                "fallback": True,
            }
