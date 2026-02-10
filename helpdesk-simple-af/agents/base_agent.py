"""Base agent class using Azure OpenAI Assistants API.

Uses openai.AsyncAzureOpenAI with API key auth instead of azure-ai-agents,
which requires a new-style 1DP endpoint (https://<aiservices>.services.ai.azure.com/...)
not available on older AzureML-based workspaces.
"""
from __future__ import annotations

import logging
from contextlib import AsyncExitStack
from typing import Optional, AsyncIterator, Dict, Any
from openai import AsyncAzureOpenAI
from config.settings import settings

logger = logging.getLogger(__name__)


class BaseAgent:
    """Base class for agents using Azure OpenAI Assistants API.

    Subclasses implement:
    - _after_open(): create the assistant, set self._agent_id
    - invoke(): process messages and yield response dicts
    """

    def __init__(
        self,
        agent_name: str,
        agent_description: str,
        agent_instructions: str,
        model: str = None,
    ) -> None:
        self.agent_name = agent_name
        self.agent_description = agent_description
        self.agent_instructions = agent_instructions
        self.model = model or settings.OPENAI_DEPLOYMENT

        self._stack: Optional[AsyncExitStack] = None
        self._client: Optional[AsyncAzureOpenAI] = None
        self._agent = None
        self._agent_id: Optional[str] = None

        self.logger = logging.getLogger(f"{__name__}.{agent_name}")

    async def open(self) -> BaseAgent:
        """Initialize the agent and its Azure OpenAI client."""
        if self._stack is not None:
            self.logger.warning(f"Agent {self.agent_name} is already open")
            return self

        self.logger.info(f"Opening agent: {self.agent_name}")
        self._stack = AsyncExitStack()

        try:
            await self._before_open()

            # TODO: Switch back to azure-ai-agents AgentsClient once the 1DP endpoint is
            # configured. azure-ai-agents 1.1.0 requires:
            #   https://<aiservices-name>.services.ai.azure.com/api/projects/<project-name>
            # Find it in Azure AI Foundry portal → Project → Overview → "Project endpoint".
            # Add it to .env as AZURE_AI_PROJECT_ENDPOINT and update base_agent.py to use:
            #   from azure.ai.agents.aio import AgentsClient
            #   from azure.identity.aio import DefaultAzureCredential
            #   self._client = AgentsClient(
            #       endpoint=settings.AI_PROJECT_ENDPOINT,
            #       credential=DefaultAzureCredential(),
            #   )
            # API key auth — no Bearer token, no nginx header size issues
            self._client = AsyncAzureOpenAI(
                azure_endpoint=settings.OPENAI_ENDPOINT,
                api_key=settings.OPENAI_API_KEY,
                api_version=settings.OPENAI_API_VERSION,
            )
            await self._stack.enter_async_context(self._client)
            self.logger.debug("Initialized AsyncAzureOpenAI client")

            await self._after_open()
            self.logger.info(f"✓ Agent {self.agent_name} opened successfully")

        except Exception as ex:
            self.logger.error(f"Failed to open agent {self.agent_name}: {ex}")
            if self._stack:
                await self._stack.aclose()
                self._stack = None
            raise

        return self

    async def close(self) -> None:
        """Close the agent and release resources."""
        if self._stack is None:
            self.logger.warning(f"Agent {self.agent_name} is already closed")
            return

        self.logger.info(f"Closing agent: {self.agent_name}")

        try:
            await self._before_close()
        except Exception as ex:
            self.logger.warning(f"Error in _before_close: {ex}")

        try:
            await self._stack.aclose()
            self._stack = None
            self._client = None
            self._agent = None
            self.logger.info(f"✓ Agent {self.agent_name} closed successfully")
        except Exception as ex:
            self.logger.error(f"Error closing agent {self.agent_name}: {ex}")
            raise

    async def __aenter__(self) -> BaseAgent:
        return await self.open()

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.close()

    async def _before_open(self) -> None:
        pass

    async def _after_open(self) -> None:
        raise NotImplementedError("Subclasses must implement _after_open()")

    async def _before_close(self) -> None:
        pass

    async def invoke(self, message: str, thread_id: Optional[str] = None) -> AsyncIterator[Dict[str, Any]]:
        raise NotImplementedError("Subclasses must implement invoke()")

    def is_open(self) -> bool:
        return self._stack is not None

    def __repr__(self) -> str:
        status = "open" if self.is_open() else "closed"
        return f"{self.__class__.__name__}(name={self.agent_name}, status={status})"
