"""Standalone test script for the orchestrator - no app.py needed.

Run from helpdesk-simple-af/ folder:
    python scripts/test_orchestrator.py
"""
import sys
import asyncio
import logging
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def test_rag_query():
    """Test RAG agent with a knowledge base question."""
    from agents.orchestrator import Orchestrator

    print("\n" + "=" * 60)
    print("TEST 1: RAG Query")
    print("=" * 60)
    query = "How do I reset my password?"
    print(f"Query: {query}\n")

    async with Orchestrator() as orch:
        async for update in orch.process(query):
            if update.get("type") == "text_delta":
                print(update["text"], end="", flush=True)
            elif update.get("type") == "final":
                print(f"\n\nIntent:   {update.get('intent')}")
                print(f"Fallback: {update.get('fallback')}")
                print(f"Sources:  {update.get('sources')}")
                print(f"Thread:   {update.get('thread_id')}")
            elif update.get("type") == "error":
                print(f"\nERROR: {update.get('message')}")


async def test_ticket_creation():
    """Test ticket agent with a ticket creation request."""
    from agents.orchestrator import Orchestrator

    print("\n" + "=" * 60)
    print("TEST 2: Ticket Creation")
    print("=" * 60)
    query = "Create a ticket: My VPN keeps disconnecting every 30 minutes"
    print(f"Query: {query}\n")

    async with Orchestrator() as orch:
        async for update in orch.process(query):
            if update.get("type") == "text_delta":
                print(update["text"], end="", flush=True)
            elif update.get("type") == "function_call":
                print(f"\n[Tool Called] {update['function']}")
                print(f"[Args]        {update['arguments']}")
                print(f"[Result]      {update['result']}")
            elif update.get("type") == "final":
                print(f"\n\nIntent:     {update.get('intent')}")
                print(f"Ticket ID:  {update.get('ticket_id')}")
                print(f"Ticket URL: {update.get('ticket_url')}")
            elif update.get("type") == "error":
                print(f"\nERROR: {update.get('message')}")


async def test_fallback():
    """Test RAG fallback when no relevant docs found."""
    from agents.orchestrator import Orchestrator

    print("\n" + "=" * 60)
    print("TEST 3: RAG Fallback (question not in knowledge base)")
    print("=" * 60)
    query = "How do I configure SAP HANA database replication?"
    print(f"Query: {query}\n")

    async with Orchestrator() as orch:
        async for update in orch.process(query):
            if update.get("type") == "text_delta":
                print(update["text"], end="", flush=True)
            elif update.get("type") == "final":
                print(f"\n\nIntent:         {update.get('intent')}")
                print(f"Fallback:       {update.get('fallback')}")
                print(f"Suggest Ticket: {update.get('suggest_ticket')}")
            elif update.get("type") == "error":
                print(f"\nERROR: {update.get('message')}")


async def test_ticket_status():
    """Test Status agent — check an existing ADO ticket and get LLM explanation."""
    from agents.orchestrator import Orchestrator

    print("\n" + "=" * 60)
    print("TEST 5: Ticket Status (needs Azure + DevOps)")
    print("=" * 60)

    ticket_number = input("Enter an existing ADO ticket number to check: ").strip()
    if not ticket_number.isdigit():
        print("  Skipping — no valid ticket number provided.")
        return

    query = f"What is the status of ticket #{ticket_number}?"
    print(f"Query: {query}\n")

    async with Orchestrator() as orch:
        async for update in orch.process(query):
            if update.get("type") == "text_delta":
                print(update["text"], end="", flush=True)
            elif update.get("type") == "final":
                print(f"\n\nIntent:       {update.get('intent')}")
                print(f"Ticket ID:    {update.get('ticket_id')}")
                print(f"State:        {update.get('ticket_state')}")
                print(f"Title:        {update.get('ticket_title')}")
                print(f"Ticket URL:   {update.get('ticket_url')}")
            elif update.get("type") == "error":
                print(f"\nERROR: {update.get('message')}")


async def test_intent_only():
    """Test the LLM-based intent classifier (requires Azure OpenAI)."""
    from agents.intent_classifier import IntentClassifier

    print("\n" + "=" * 60)
    print("TEST 4: Intent Classifier (requires Azure OpenAI)")
    print("=" * 60)

    classifier = IntentClassifier()
    test_messages = [
        "How do I reset my password?",
        "Create a ticket for VPN issue",
        "Check ticket #1234",
        "I need to open a new ticket",
        "What is the status of ticket 567?",
        "How do I set up the printer?",
        "I'd like to log this problem",
        "My laptop keeps crashing, can someone raise this for me?",
        "I've been struggling with slow internet for a week, please help",
    ]

    for msg in test_messages:
        intent = await classifier.classify(msg)
        print(f"  [{intent:8}]  {msg}")


async def main():
    """Run selected tests."""
    print("=" * 60)
    print("Helpdesk-Simple-AF - Standalone Tests")
    print("=" * 60)
    print("Choose what to test:")
    print("  1 - RAG query (needs Azure)")
    print("  2 - Ticket creation (needs Azure + DevOps)")
    print("  3 - RAG fallback (needs Azure)")
    print("  4 - Intent classifier (needs Azure OpenAI)")
    print("  5 - Ticket status check (needs Azure + DevOps)")
    print("  all - Run all tests")
    print()

    choice = input("Enter choice (1/2/3/4/5/all): ").strip().lower()

    if choice == "1":
        await test_rag_query()
    elif choice == "2":
        await test_ticket_creation()
    elif choice == "3":
        await test_fallback()
    elif choice == "4":
        await test_intent_only()
    elif choice == "5":
        await test_ticket_status()
    elif choice == "all":
        await test_intent_only()
        await test_rag_query()
        await test_ticket_creation()
        await test_fallback()
        await test_ticket_status()
    else:
        print("Invalid choice. Running intent classifier test...")
        await test_intent_only()

    print("\n" + "=" * 60)
    print("Tests complete.")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
