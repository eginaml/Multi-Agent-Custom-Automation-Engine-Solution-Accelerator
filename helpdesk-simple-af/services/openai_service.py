"""Azure OpenAI service wrapper."""
from openai import AzureOpenAI
from typing import List
from config.settings import settings


class OpenAIService:
    """Service for Azure OpenAI operations."""

    def __init__(self):
        """Initialize OpenAI client."""
        self.client = AzureOpenAI(
            azure_endpoint=settings.OPENAI_ENDPOINT,
            api_key=settings.OPENAI_API_KEY,
            api_version=settings.OPENAI_API_VERSION,
        )

    def generate_embedding(self, text: str) -> List[float]:
        """Generate embeddings for text.

        Args:
            text: Text to embed

        Returns:
            List of floats representing the embedding
        """
        response = self.client.embeddings.create(
            model=settings.OPENAI_EMBEDDING_DEPLOYMENT,
            input=text,
        )
        return response.data[0].embedding

    def chat_completion(
        self,
        messages: List[dict],
        temperature: float = None,
        max_tokens: int = None,
    ) -> str:
        """Generate chat completion.

        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum tokens to generate

        Returns:
            Generated text
        """
        if temperature is None:
            temperature = settings.AGENT_TEMPERATURE
        if max_tokens is None:
            max_tokens = settings.AGENT_MAX_TOKENS

        response = self.client.chat.completions.create(
            model=settings.OPENAI_DEPLOYMENT,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content
