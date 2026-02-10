"""Intent classification using an LLM call for accurate natural language understanding."""
import logging
from typing import Literal
from openai import AsyncAzureOpenAI
from config.settings import settings

logger = logging.getLogger(__name__)

IntentType = Literal["rag", "ticket", "status"]

_SYSTEM_PROMPT = """You are an intent classifier for an IT helpdesk system.
Classify the user message into exactly one of these intents:

- ticket: The user wants to create, open, log, file, raise, or submit a support ticket/issue/request
- status: The user wants to check, track, or get the status of an existing ticket (usually mentions a ticket number)
- rag: Anything else — a question, how-to, troubleshooting request, or general helpdesk query

Reply with a single word: ticket, status, or rag. No punctuation, no explanation."""


class IntentClassifier:
    """Classifies user intent using a fast LLM call.

    Uses gpt-4.1-mini for accurate natural language understanding, handling
    phrases like "I'd like to log this problem", "can someone raise this for me",
    "my laptop is broken and I need help" correctly.
    """

    def __init__(self):
        self._client = AsyncAzureOpenAI(
            azure_endpoint=settings.OPENAI_ENDPOINT,
            api_key=settings.OPENAI_API_KEY,
            api_version=settings.OPENAI_API_VERSION,
        )

    async def classify(self, message: str) -> IntentType:
        """Classify user message intent using LLM.

        Args:
            message: User message

        Returns:
            Intent type: 'rag', 'ticket', or 'status'
        """
        try:
            response = await self._client.chat.completions.create(
                model=settings.OPENAI_DEPLOYMENT,
                messages=[
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user", "content": message},
                ],
                max_tokens=5,
                temperature=0,
            )
            intent = response.choices[0].message.content.strip().lower()

            if intent not in ("rag", "ticket", "status"):
                logger.warning(f"Unexpected intent '{intent}', defaulting to 'rag'")
                intent = "rag"

            logger.info(f"Classified '{message[:60]}' → {intent}")
            return intent

        except Exception as ex:
            logger.error(f"Intent classification failed: {ex}, defaulting to 'rag'")
            return "rag"
