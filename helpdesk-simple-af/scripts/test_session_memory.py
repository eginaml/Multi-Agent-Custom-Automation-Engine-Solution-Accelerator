"""Test in-session memory: 5-turn conversation proving the agent remembers context.

Run from helpdesk-simple-af/ folder:
    venv\Scripts\python.exe scripts\test_session_memory.py
"""
import sys
import os
import asyncio
import uuid
from pathlib import Path

os.environ["PYTHONUNBUFFERED"] = "1"
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import logging
logging.disable(logging.CRITICAL)

from agents.orchestrator import Orchestrator


async def main():
    session_id = f"test-{uuid.uuid4().hex[:8]}"

    print("=" * 70, flush=True)
    print("Session Memory Test - 5-turn RAG conversation", flush=True)
    print("=" * 70, flush=True)
    print(f"Session ID: {session_id}", flush=True)

    turns = [
        "How do I reset my Windows password?",
        "Can you elaborate on the first step you just mentioned?",
        "What happens if my account gets locked out during that process?",
        "Are there any company security policies I should know about regarding passwords?",
        "Going back to the very first thing you told me about resetting my password - can you summarize that original answer in one sentence?",
    ]

    thread_ids = []

    try:
        orch = Orchestrator()
        await orch.initialize()
        print("Orchestrator ready.", flush=True)

        for turn_num, msg in enumerate(turns, 1):
            print(f"\n--- Turn {turn_num}/5 ---", flush=True)
            print(f"User: {msg}", flush=True)
            print("", flush=True)
            sys.stdout.write("Agent: ")
            sys.stdout.flush()

            thread_id = None
            async for update in orch.process(msg, session_id=session_id):
                t = update.get("type")
                if t == "text_delta":
                    sys.stdout.write(update["text"])
                    sys.stdout.flush()
                elif t == "final":
                    thread_id = update.get("thread_id")
                elif t == "error":
                    sys.stdout.write(f"\nERROR: {update.get('message')}")
                    sys.stdout.flush()

            thread_ids.append(thread_id)
            print("", flush=True)

        await orch.cleanup()

    except Exception as ex:
        print(f"\nFATAL ERROR: {ex}", flush=True)
        import traceback
        traceback.print_exc()
        return

    # Results
    print("", flush=True)
    print("=" * 70, flush=True)
    print("Results", flush=True)
    print("=" * 70, flush=True)

    store = orch.session_store.list_sessions()
    print(f"Session store entries: {len(store)}", flush=True)
    for key, tid in store.items():
        print(f"  {key} -> {tid}", flush=True)

    print("", flush=True)
    unique = set(t for t in thread_ids if t)
    if len(unique) == 1:
        print(f"PASS: Same thread reused across all 5 turns ({unique.pop()})", flush=True)
    elif len(unique) > 1:
        print("FAIL: Multiple threads created:", flush=True)
        for i, tid in enumerate(thread_ids, 1):
            print(f"  Turn {i}: {tid}", flush=True)
    else:
        print("WARN: No thread_ids captured", flush=True)

    print("", flush=True)
    print("If the turn 5 response above references the original password", flush=True)
    print("reset answer from turn 1, session memory is working.", flush=True)
    print("=" * 70, flush=True)


if __name__ == "__main__":
    asyncio.run(main())
