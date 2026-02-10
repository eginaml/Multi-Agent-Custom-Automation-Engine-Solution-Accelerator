"""Azure AI Search service for vector search operations."""
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery
from azure.core.credentials import AzureKeyCredential
from typing import Dict, Any, List
from config.settings import settings
from services.openai_service import OpenAIService


class SearchService:
    """Service for Azure AI Search operations."""

    def __init__(self):
        """Initialize search client."""
        self.client = SearchClient(
            endpoint=settings.SEARCH_ENDPOINT,
            index_name=settings.SEARCH_INDEX_NAME,
            credential=AzureKeyCredential(settings.SEARCH_API_KEY),
        )
        self.openai_service = OpenAIService()

    def search(
        self, query: str, top_k: int = None, score_threshold: float = None
    ) -> Dict[str, Any]:
        """Search for documents using hybrid (vector + keyword) search.

        Args:
            query: Search query
            top_k: Number of results to return
            score_threshold: Minimum relevance score

        Returns:
            Dictionary with search results and metadata
        """
        if top_k is None:
            top_k = settings.RAG_TOP_K
        if score_threshold is None:
            score_threshold = settings.RAG_SCORE_THRESHOLD

        # Generate query embedding
        query_vector = self.openai_service.generate_embedding(query)

        # Create vector query
        vector_query = VectorizedQuery(
            vector=query_vector, k_nearest_neighbors=top_k, fields="contentVector"
        )

        # Execute hybrid search
        results = self.client.search(
            search_text=query, vector_queries=[vector_query], top=top_k
        )

        # Process results
        documents = []
        max_score = 0.0

        for result in results:
            score = result["@search.score"]
            if score > max_score:
                max_score = score

            if score >= score_threshold:
                documents.append(
                    {
                        "id": result["id"],
                        "title": result["title"],
                        "content": result["content"],
                        "score": score,
                    }
                )

        return {
            "documents": documents,
            "max_score": max_score,
            "has_relevant": len(documents) > 0,
            "query": query,
        }
