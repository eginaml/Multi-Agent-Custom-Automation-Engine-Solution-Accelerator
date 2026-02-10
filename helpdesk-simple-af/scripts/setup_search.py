"""Setup Azure AI Search index with mock helpdesk documents."""
import sys
import os
from pathlib import Path

# Add parent directory to path to import project modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex,
    SearchField,
    SearchFieldDataType,
    VectorSearch,
    VectorSearchProfile,
    HnswAlgorithmConfiguration,
    SemanticConfiguration,
    SemanticField,
    SemanticPrioritizedFields,
    SemanticSearch,
)
from azure.core.credentials import AzureKeyCredential
from config.settings import settings
from services.openai_service import OpenAIService
import logging
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_mock_documents():
    """Load mock documents from JSON file.

    Returns:
        List of document dictionaries
    """
    # Get path to data file
    data_file = Path(__file__).parent.parent / "data" / "helpdesk_docs.json"

    logger.info(f"Loading documents from: {data_file}")

    try:
        with open(data_file, "r", encoding="utf-8") as f:
            docs = json.load(f)
        logger.info(f"✓ Loaded {len(docs)} documents from JSON file")
        return docs
    except FileNotFoundError:
        logger.error(f"❌ Data file not found: {data_file}")
        logger.error("Please ensure data/helpdesk_docs.json exists")
        return []
    except json.JSONDecodeError as e:
        logger.error(f"❌ Invalid JSON in data file: {e}")
        return []


def create_search_index():
    """Create Azure AI Search index with vector search configuration."""
    logger.info("Creating Azure AI Search index...")

    # Initialize index client
    index_client = SearchIndexClient(
        endpoint=settings.SEARCH_ENDPOINT,
        credential=AzureKeyCredential(settings.SEARCH_API_KEY)
    )

    # Define index fields
    fields = [
        SearchField(
            name="id",
            type=SearchFieldDataType.String,
            key=True,
            sortable=True,
            filterable=True,
        ),
        SearchField(
            name="title",
            type=SearchFieldDataType.String,
            searchable=True,
            filterable=True,
            sortable=True,
        ),
        SearchField(
            name="content",
            type=SearchFieldDataType.String,
            searchable=True,
        ),
        SearchField(
            name="contentVector",
            type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
            searchable=True,
            vector_search_dimensions=1536,  # text-embedding-3-large dimensions
            vector_search_profile_name="vector-profile",
        ),
    ]

    # Configure vector search
    vector_search = VectorSearch(
        algorithms=[
            HnswAlgorithmConfiguration(
                name="hnsw-algorithm",
                parameters={
                    "m": 4,
                    "efConstruction": 400,
                    "efSearch": 500,
                    "metric": "cosine",
                },
            )
        ],
        profiles=[
            VectorSearchProfile(
                name="vector-profile",
                algorithm_configuration_name="hnsw-algorithm",
            )
        ],
    )

    # Configure semantic search
    semantic_config = SemanticConfiguration(
        name="semantic-config",
        prioritized_fields=SemanticPrioritizedFields(
            title_field=SemanticField(field_name="title"),
            content_fields=[SemanticField(field_name="content")],
        ),
    )

    semantic_search = SemanticSearch(configurations=[semantic_config])

    # Create index
    index = SearchIndex(
        name=settings.SEARCH_INDEX_NAME,
        fields=fields,
        vector_search=vector_search,
        semantic_search=semantic_search,
    )

    # Delete existing index if it exists
    try:
        index_client.delete_index(settings.SEARCH_INDEX_NAME)
        logger.info(f"Deleted existing index: {settings.SEARCH_INDEX_NAME}")
    except Exception:
        pass  # Index doesn't exist, that's fine

    # Create new index
    index_client.create_index(index)
    logger.info(f"✓ Created index: {settings.SEARCH_INDEX_NAME}")


def upload_mock_documents():
    """Upload mock documents to the search index."""
    logger.info("Uploading mock documents...")

    # Load documents from JSON file
    mock_docs = load_mock_documents()
    if not mock_docs:
        logger.error("❌ No documents to upload")
        return 0

    # Initialize OpenAI service for embeddings
    openai_service = OpenAIService()

    # Initialize search client
    search_client = SearchClient(
        endpoint=settings.SEARCH_ENDPOINT,
        index_name=settings.SEARCH_INDEX_NAME,
        credential=AzureKeyCredential(settings.SEARCH_API_KEY)
    )

    # Generate embeddings and upload documents
    documents_to_upload = []
    for doc in mock_docs:
        logger.info(f"Generating embedding for: {doc['title']}")

        # Generate embedding for the content
        embedding = openai_service.generate_embedding(doc["content"])

        # Add embedding to document
        doc_with_vector = {
            "id": doc["id"],
            "title": doc["title"],
            "content": doc["content"],
            "contentVector": embedding,
        }
        documents_to_upload.append(doc_with_vector)

    # Upload all documents
    result = search_client.upload_documents(documents=documents_to_upload)

    # Check results
    succeeded = sum(1 for r in result if r.succeeded)
    logger.info(f"✓ Uploaded {succeeded}/{len(mock_docs)} documents successfully")

    # Print document titles
    for doc in mock_docs:
        logger.info(f"  - {doc['title']}")

    return len(mock_docs)


def main():
    """Main setup function."""
    logger.info("=" * 60)
    logger.info("Azure AI Search Setup - Helpdesk Simple")
    logger.info("=" * 60)

    # Validate settings
    if not settings.SEARCH_ENDPOINT:
        logger.error("❌ AZURE_SEARCH_ENDPOINT not set in .env file")
        return

    if not settings.SEARCH_API_KEY:
        logger.error("❌ AZURE_SEARCH_API_KEY not set in .env file")
        return

    if not settings.OPENAI_ENDPOINT:
        logger.error("❌ AZURE_OPENAI_ENDPOINT not set in .env file")
        return

    if not settings.OPENAI_API_KEY:
        logger.error("❌ AZURE_OPENAI_API_KEY not set in .env file")
        return

    try:
        # Step 1: Create index
        create_search_index()

        # Step 2: Upload mock documents
        doc_count = upload_mock_documents()

        if doc_count == 0:
            logger.error("❌ No documents were uploaded. Please check data/helpdesk_docs.json")
            return

        logger.info("=" * 60)
        logger.info("✓ Setup completed successfully!")
        logger.info("=" * 60)
        logger.info(f"Index Name: {settings.SEARCH_INDEX_NAME}")
        logger.info(f"Documents: {doc_count} mock helpdesk articles")
        logger.info("")
        logger.info("You can now start the application:")
        logger.info("  python app.py")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"❌ Setup failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
