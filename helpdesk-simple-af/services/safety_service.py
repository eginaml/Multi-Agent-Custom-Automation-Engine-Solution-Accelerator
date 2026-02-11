"""Azure Content Safety service for input moderation.

Screens user messages for harmful content before they reach any agent.
Categories analysed: Hate, SelfHarm, Sexual, Violence.

If the Content Safety resource is not configured (missing endpoint/key),
the service runs in pass-through mode and logs a warning — this lets the
app run in development without the resource provisioned.
"""
import logging
from dataclasses import dataclass, field
from typing import List

from azure.ai.contentsafety import ContentSafetyClient
from azure.ai.contentsafety.models import AnalyzeTextOptions, TextCategory
from azure.core.credentials import AzureKeyCredential
from azure.core.exceptions import HttpResponseError

from config.settings import settings

logger = logging.getLogger(__name__)


@dataclass
class SafetyResult:
    """Result of a content safety check."""

    is_safe: bool
    blocked_categories: List[str] = field(default_factory=list)
    scores: dict = field(default_factory=dict)
    reason: str = ""


class SafetyService:
    """Screens text for harmful content using Azure Content Safety."""

    def __init__(self):
        endpoint = settings.CONTENT_SAFETY_ENDPOINT
        key = settings.CONTENT_SAFETY_KEY

        if not endpoint or not key:
            logger.warning(
                "Azure Content Safety is not configured "
                "(AZURE_CONTENT_SAFETY_ENDPOINT / AZURE_CONTENT_SAFETY_KEY missing). "
                "Input moderation is DISABLED. Set these values in .env to enable."
            )
            self._client = None
        else:
            self._client = ContentSafetyClient(endpoint, AzureKeyCredential(key))
            logger.info(f"Content Safety client initialised: {endpoint}")

    def check(self, text: str) -> SafetyResult:
        """Analyse text for harmful content.

        Returns:
            SafetyResult with is_safe=True if the text passes moderation.
            Blocks content with severity >= CONTENT_SAFETY_THRESHOLD in any category.
        """
        if not self._client:
            return SafetyResult(is_safe=True, reason="moderation_disabled")

        try:
            options = AnalyzeTextOptions(
                text=text,
                categories=[
                    TextCategory.HATE,
                    TextCategory.SELF_HARM,
                    TextCategory.SEXUAL,
                    TextCategory.VIOLENCE,
                ],
            )
            response = self._client.analyze_text(options)

            threshold = settings.CONTENT_SAFETY_THRESHOLD
            scores: dict = {}
            blocked: List[str] = []

            for item in response.categories_analysis:
                cat = item.category.value if hasattr(item.category, "value") else str(item.category)
                severity = item.severity or 0
                scores[cat] = severity
                if severity >= threshold:
                    blocked.append(cat)

            is_safe = len(blocked) == 0
            reason = f"Blocked: {', '.join(blocked)}" if blocked else "ok"
            logger.info(f"Safety check — safe={is_safe} scores={scores}")
            return SafetyResult(
                is_safe=is_safe,
                blocked_categories=blocked,
                scores=scores,
                reason=reason,
            )

        except HttpResponseError as ex:
            code = ex.error.code if ex.error else "unknown"
            logger.error(f"Content Safety API error [{code}]: {ex}")
            # Fail open — don't block users when the safety API is unavailable
            return SafetyResult(is_safe=True, reason=f"api_error:{code}")

        except Exception as ex:
            logger.error(f"Content Safety check failed unexpectedly: {ex}")
            return SafetyResult(is_safe=True, reason=f"error:{str(ex)}")
