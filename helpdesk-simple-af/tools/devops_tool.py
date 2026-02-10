"""DevOps tool for function calling in agents."""
from services.devops_service import DevOpsService
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


# Tool definition for Azure AI Agents
DEVOPS_TOOL_DEFINITION = {
    "type": "function",
    "function": {
        "name": "create_devops_ticket",
        "description": "Creates a support ticket in Azure DevOps. Use this when the user asks to create a ticket, report an issue, or when you cannot find relevant information to help them.",
        "parameters": {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "A concise title for the ticket (e.g., 'Password reset not working')",
                },
                "description": {
                    "type": "string",
                    "description": "Detailed description of the issue including what the user tried and any error messages",
                },
                "priority": {
                    "type": "integer",
                    "description": "Priority level: 1=Critical, 2=High, 3=Medium, 4=Low",
                    "enum": [1, 2, 3, 4],
                    "default": 2,
                },
            },
            "required": ["title", "description"],
        },
    },
}


async def create_devops_ticket(title: str, description: str, priority: int = 2) -> Dict[str, Any]:
    """Execute DevOps ticket creation.

    This function is called by the agent when it invokes the tool.

    Args:
        title: Ticket title
        description: Ticket description
        priority: Priority (1-4, where 1 is critical)

    Returns:
        Dictionary with ticket creation result
    """
    logger.info(f"Creating DevOps ticket: {title}")

    try:
        devops_service = DevOpsService()
        result = devops_service.create_work_item(
            title=title, description=description, priority=priority
        )

        return {
            "success": True,
            "ticket_id": result["id"],
            "ticket_url": result["url"],
            "message": f"Ticket #{result['id']} created successfully",
        }

    except Exception as ex:
        logger.error(f"Failed to create DevOps ticket: {ex}")
        return {
            "success": False,
            "error": str(ex),
            "message": f"Failed to create ticket: {str(ex)}",
        }


# Tool executor mapping (for agent framework)
TOOL_EXECUTORS = {
    "create_devops_ticket": create_devops_ticket,
}
