"""Application settings loaded from environment variables."""
import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()


class Settings:
    """Application settings."""

    # ============================================
    # Azure AI Foundry Project Configuration
    # ============================================
    # Option A (recommended): Connection string from Foundry UI → Overview
    # Format: region.api.azureml.ms;subscription-id;resource-group;project-name
    # Example: eastus.api.azureml.ms;xxxxxxxx-xxxx;my-rg;my-project
    AI_PROJECT_CONNECTION_STRING = os.getenv("AZURE_AI_PROJECT_CONNECTION_STRING")

    # Option B: Full endpoint URL (used by AgentsClient in base_agent.py)
    # Format: https://region.api.azureml.ms/subscriptions/.../workspaces/project-name
    AI_PROJECT_ENDPOINT = os.getenv("AZURE_AI_PROJECT_ENDPOINT")

    AI_PROJECT_NAME = os.getenv("AZURE_AI_PROJECT_NAME")
    SUBSCRIPTION_ID = os.getenv("AZURE_SUBSCRIPTION_ID")
    RESOURCE_GROUP = os.getenv("AZURE_RESOURCE_GROUP")

    # ============================================
    # Azure OpenAI Configuration
    # ============================================
    OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
    OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
    OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4.1-mini")
    OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2024-08-01-preview")
    OPENAI_EMBEDDING_DEPLOYMENT = os.getenv(
        "AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "text-embedding-3-small"
    )

    # ============================================
    # Azure AI Search Configuration
    # ============================================
    SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT")
    SEARCH_API_KEY = os.getenv("AZURE_SEARCH_API_KEY")
    SEARCH_INDEX_NAME = os.getenv("AZURE_SEARCH_INDEX_NAME", "helpdesk-docs")

    # Connection name in Azure AI Foundry
    SEARCH_CONNECTION_NAME = os.getenv("AZURE_AI_SEARCH_CONNECTION_NAME", "helpdeskem")

    # ============================================
    # Azure DevOps Configuration
    # ============================================
    DEVOPS_ORG_URL = os.getenv("AZURE_DEVOPS_ORG_URL")
    DEVOPS_PROJECT = os.getenv("AZURE_DEVOPS_PROJECT")
    DEVOPS_PAT = os.getenv("AZURE_DEVOPS_PAT")

    # ============================================
    # Agent Framework Configuration
    # ============================================
    AGENT_TEMPERATURE = float(os.getenv("AGENT_TEMPERATURE", "0"))
    AGENT_MAX_TOKENS = int(os.getenv("AGENT_MAX_TOKENS", "2000"))

    # RAG Configuration
    RAG_TOP_K = int(os.getenv("RAG_TOP_K", "2"))
    RAG_SCORE_THRESHOLD = float(os.getenv("RAG_SCORE_THRESHOLD", "0"))
    RAG_QUERY_TYPE = os.getenv("RAG_QUERY_TYPE", "vector_semantic_hybrid")

    # Feature Flags
    ENABLE_CODE_INTERPRETER = os.getenv("ENABLE_CODE_INTERPRETER", "false").lower() == "true"
    ENABLE_CONVERSATION_THREADING = os.getenv("ENABLE_CONVERSATION_THREADING", "true").lower() == "true"

    # ============================================
    # Azure Content Safety Configuration
    # ============================================
    # Create resource: portal.azure.com → AI Services → Content Safety
    # Endpoint format: https://<resource-name>.cognitiveservices.azure.com/
    CONTENT_SAFETY_ENDPOINT = os.getenv("AZURE_CONTENT_SAFETY_ENDPOINT")
    CONTENT_SAFETY_KEY = os.getenv("AZURE_CONTENT_SAFETY_KEY")
    # Severity threshold: 0=safe, 2=low, 4=medium, 6=high. Block at 4 (medium) or above.
    CONTENT_SAFETY_THRESHOLD = int(os.getenv("AZURE_CONTENT_SAFETY_THRESHOLD", "4"))

    # ============================================
    # API Server Configuration
    # ============================================
    API_HOST = os.getenv("API_HOST", "0.0.0.0")
    API_PORT = int(os.getenv("API_PORT", "8000"))
    API_DEBUG = os.getenv("API_DEBUG", "true").lower() == "true"


# Global settings instance
settings = Settings()
