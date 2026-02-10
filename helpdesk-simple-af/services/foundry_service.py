"""Azure AI Foundry service for connection management.

Note: The azure-ai-projects 1.0.0 GA SDK requires a new-style Azure AI Foundry
endpoint (e.g. https://<name>.services.ai.azure.com). This project uses an
older AzureML-based workspace, so we construct connection IDs from settings
instead of calling the connections API.
"""
from typing import Optional, Dict, Any
from config.settings import settings
import logging

logger = logging.getLogger(__name__)


def _build_connection_id(connection_name: str) -> str:
    """Build the ARM resource ID for a Foundry connection."""
    return (
        f"/subscriptions/{settings.SUBSCRIPTION_ID}"
        f"/resourceGroups/{settings.RESOURCE_GROUP}"
        f"/providers/Microsoft.MachineLearningServices"
        f"/workspaces/{settings.AI_PROJECT_NAME}"
        f"/connections/{connection_name}"
    )


class FoundryService:
    """Service for Azure AI Foundry connection info.

    Constructs connection resource IDs from settings rather than calling
    the connections API, which is incompatible with older AzureML workspaces
    when using azure-ai-projects 1.0.0.
    """

    @classmethod
    def get_search_connection(cls) -> Optional[Dict[str, Any]]:
        """Get Azure AI Search connection details.

        Returns:
            Connection dict with 'id', 'name', 'type', or None if settings missing.
        """
        required = {
            "AZURE_AI_SEARCH_CONNECTION_NAME": settings.SEARCH_CONNECTION_NAME,
            "AZURE_SUBSCRIPTION_ID": settings.SUBSCRIPTION_ID,
            "AZURE_RESOURCE_GROUP": settings.RESOURCE_GROUP,
            "AZURE_AI_PROJECT_NAME": settings.AI_PROJECT_NAME,
        }
        missing = [k for k, v in required.items() if not v]
        if missing:
            logger.error(f"Cannot build search connection ID — missing: {missing}")
            return None

        connection_id = _build_connection_id(settings.SEARCH_CONNECTION_NAME)
        logger.info(f"Using search connection: {settings.SEARCH_CONNECTION_NAME}")
        return {
            "id": connection_id,
            "name": settings.SEARCH_CONNECTION_NAME,
            "type": "AzureAISearch",
        }

    @classmethod
    def get_connection(cls, connection_name: str) -> Optional[Dict[str, Any]]:
        """Get connection details by name.

        Args:
            connection_name: Name of the connection.

        Returns:
            Connection dict with 'id', 'name', or None if settings missing.
        """
        if not all([settings.SUBSCRIPTION_ID, settings.RESOURCE_GROUP, settings.AI_PROJECT_NAME]):
            logger.error("Cannot build connection ID — missing SUBSCRIPTION_ID, RESOURCE_GROUP, or AI_PROJECT_NAME")
            return None

        return {
            "id": _build_connection_id(connection_name),
            "name": connection_name,
        }

    @classmethod
    def list_connections(cls) -> list:
        """List known connections constructed from settings.

        Returns:
            List of connection dicts.
        """
        connections = []
        search_conn = cls.get_search_connection()
        if search_conn:
            connections.append(search_conn)
        return connections
