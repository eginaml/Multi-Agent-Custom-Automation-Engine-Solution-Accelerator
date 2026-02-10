"""Azure DevOps service for work item management."""
from azure.devops.connection import Connection
from msrest.authentication import BasicAuthentication
from azure.devops.v7_1.work_item_tracking.models import JsonPatchOperation
from typing import Dict, Any
from config.settings import settings


class DevOpsService:
    """Service for Azure DevOps work item operations."""

    def __init__(self):
        """Initialize DevOps client."""
        credentials = BasicAuthentication("", settings.DEVOPS_PAT)
        self.connection = Connection(
            base_url=settings.DEVOPS_ORG_URL, creds=credentials
        )
        self.wit_client = self.connection.clients.get_work_item_tracking_client()

    def create_work_item(
        self, title: str, description: str, priority: int = 2
    ) -> Dict[str, Any]:
        """Create a work item (ticket) in Azure DevOps.

        Args:
            title: Ticket title
            description: Ticket description
            priority: Priority level (1=Critical, 2=High, 3=Medium, 4=Low)

        Returns:
            Dictionary with ticket information
        """
        # Create work item document
        document = [
            JsonPatchOperation(
                op="add", path="/fields/System.Title", value=title
            ),
            JsonPatchOperation(
                op="add",
                path="/fields/System.Description",
                value=description,
            ),
            JsonPatchOperation(
                op="add", path="/fields/Microsoft.VSTS.Common.Priority", value=priority
            ),
        ]

        # Create work item
        work_item = self.wit_client.create_work_item(
            document=document,
            project=settings.DEVOPS_PROJECT,
            type="Task",
        )

        return {
            "id": work_item.id,
            "url": work_item._links.additional_properties["html"]["href"],
            "title": title,
            "description": description,
            "priority": priority,
        }

    def get_work_item(self, work_item_id: int) -> Dict[str, Any]:
        """Get work item details by ID.

        Args:
            work_item_id: Work item ID

        Returns:
            Dictionary with work item details
        """
        work_item = self.wit_client.get_work_item(
            id=work_item_id, project=settings.DEVOPS_PROJECT
        )

        return {
            "id": work_item.id,
            "title": work_item.fields.get("System.Title"),
            "state": work_item.fields.get("System.State"),
            "assigned_to": work_item.fields.get("System.AssignedTo", {}).get(
                "displayName", "Unassigned"
            ),
            "created_date": work_item.fields.get("System.CreatedDate"),
            "url": work_item._links.additional_properties["html"]["href"],
        }
