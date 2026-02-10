"""Test Azure connections individually - no app.py needed.

Use this to verify each Azure service is configured correctly
before running the full application.

Run from helpdesk-simple-af/ folder:
    python scripts/test_connections.py
"""
import sys
import asyncio
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(level=logging.WARNING)  # Quiet mode for clean output
logger = logging.getLogger(__name__)


def test_env():
    """Check all required .env variables are set."""
    from config.settings import settings

    print("\n" + "=" * 60)
    print("CHECK: Environment Variables")
    print("=" * 60)

    checks = {
        "AZURE_AI_PROJECT_ENDPOINT": settings.AI_PROJECT_ENDPOINT,
        "AZURE_OPENAI_ENDPOINT":     settings.OPENAI_ENDPOINT,
        "AZURE_OPENAI_API_KEY":      settings.OPENAI_API_KEY,
        "AZURE_OPENAI_DEPLOYMENT":   settings.OPENAI_DEPLOYMENT,
        "AZURE_SEARCH_ENDPOINT":     settings.SEARCH_ENDPOINT,
        "AZURE_SEARCH_API_KEY":      settings.SEARCH_API_KEY,
        "AZURE_SEARCH_INDEX_NAME":   settings.SEARCH_INDEX_NAME,
        "AZURE_DEVOPS_ORG_URL":      settings.DEVOPS_ORG_URL,
        "AZURE_DEVOPS_PROJECT":      settings.DEVOPS_PROJECT,
        "AZURE_DEVOPS_PAT":          settings.DEVOPS_PAT,
    }

    all_ok = True
    for name, value in checks.items():
        if value:
            # Mask secrets
            if "KEY" in name or "PAT" in name:
                display = value[:6] + "..." + value[-4:] if len(value) > 10 else "***"
            else:
                display = value
            print(f"  ✓ {name:<40} {display}")
        else:
            print(f"  ✗ {name:<40} NOT SET")
            all_ok = False

    return all_ok


def test_openai():
    """Test Azure OpenAI connection."""
    from services.openai_service import OpenAIService

    print("\n" + "=" * 60)
    print("CHECK: Azure OpenAI")
    print("=" * 60)

    try:
        svc = OpenAIService()
        # Test chat completion
        response = svc.chat_completion(
            messages=[{"role": "user", "content": "Say 'OK' in one word only."}],
            max_tokens=5,
        )
        print(f"  ✓ Chat completion works. Response: {response.strip()}")
        return True
    except Exception as e:
        print(f"  ✗ Chat completion failed: {e}")
        return False


def test_embedding():
    """Test Azure OpenAI embedding generation."""
    from services.openai_service import OpenAIService

    print("\n" + "=" * 60)
    print("CHECK: Azure OpenAI Embeddings")
    print("=" * 60)

    try:
        svc = OpenAIService()
        embedding = svc.generate_embedding("test query")
        print(f"  ✓ Embeddings work. Dimensions: {len(embedding)}")
        return True
    except Exception as e:
        print(f"  ✗ Embedding failed: {e}")
        return False


def test_search():
    """Test Azure AI Search connection and query."""
    from services.search_service import SearchService

    print("\n" + "=" * 60)
    print("CHECK: Azure AI Search")
    print("=" * 60)

    try:
        svc = SearchService()
        result = svc.search("password reset", top_k=1, score_threshold=0.0)
        doc_count = len(result["documents"])
        print(f"  ✓ Search works. Documents returned: {doc_count}")
        print(f"    Max score: {result['max_score']:.4f}")
        if result["documents"]:
            print(f"    Top result: {result['documents'][0]['title']}")
        return True
    except Exception as e:
        print(f"  ✗ Search failed: {e}")
        print("    → Did you run: python scripts/setup_search.py ?")
        return False


def test_devops():
    """Test Azure DevOps connection."""
    from services.devops_service import DevOpsService

    print("\n" + "=" * 60)
    print("CHECK: Azure DevOps")
    print("=" * 60)

    try:
        svc = DevOpsService()
        # Just test the connection is established (don't create a ticket)
        _ = svc.wit_client
        print("  ✓ DevOps client initialized successfully")
        return True
    except Exception as e:
        print(f"  ✗ DevOps connection failed: {e}")
        print("    → Check AZURE_DEVOPS_ORG_URL and AZURE_DEVOPS_PAT in .env")
        return False


def test_foundry():
    """Test Azure AI Foundry connection and list connections."""
    from services.foundry_service import FoundryService

    print("\n" + "=" * 60)
    print("CHECK: Azure AI Foundry")
    print("=" * 60)

    try:
        connections = FoundryService.list_connections()
        print(f"  ✓ Foundry connected. Found {len(connections)} connection(s):")
        for conn in connections:
            print(f"    - [{conn['type']}] {conn['name']}")

        # Check for search connection
        search_conn = FoundryService.get_search_connection()
        if search_conn:
            print(f"\n  ✓ Search connection found: {search_conn['name']}")
        else:
            print("\n  ✗ No Azure AI Search connection found in Foundry")
            print("    → Add a search connection in Foundry → Connected resources")

        return len(connections) > 0
    except Exception as e:
        print(f"  ✗ Foundry connection failed: {e}")
        print("    → Check AZURE_AI_PROJECT_ENDPOINT in .env")
        print("    → Must be the full project connection string, e.g.:")
        print("       https://eastus.api.azureml.ms/subscriptions/xxx/resourceGroups/xxx/")
        print("       providers/Microsoft.MachineLearningServices/workspaces/xxx")
        return False


def main():
    """Run connection checks."""
    print("=" * 60)
    print("Helpdesk-Simple-AF - Connection Checks")
    print("=" * 60)
    print("This checks each Azure service independently.")
    print()

    results = {}

    # Always check env first
    results["env"] = test_env()

    if not results["env"]:
        print("\n⚠️  Fix missing .env variables before continuing.")
        return

    print("\nWhich checks to run?")
    print("  1 - OpenAI only")
    print("  2 - Search only")
    print("  3 - DevOps only")
    print("  4 - Foundry only")
    print("  all - Run all checks")
    print()

    choice = input("Enter choice (1/2/3/4/all): ").strip().lower()

    if choice == "1" or choice == "all":
        results["openai"] = test_openai()
        results["embedding"] = test_embedding()

    if choice == "2" or choice == "all":
        results["search"] = test_search()

    if choice == "3" or choice == "all":
        results["devops"] = test_devops()

    if choice == "4" or choice == "all":
        results["foundry"] = test_foundry()

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    for name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {status}  {name}")

    all_passed = all(results.values())
    print()
    if all_passed:
        print("All checks passed! You can run: python app.py")
    else:
        print("Some checks failed. Fix the issues above before running app.py")


if __name__ == "__main__":
    main()
