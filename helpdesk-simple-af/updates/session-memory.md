# Session Memory - In-Session Conversation Persistence

**Why:** Without session memory, every message to the orchestrator created a brand new OpenAI thread -- the agent had zero context of what the user said 30 seconds ago, making follow-up questions impossible.

## Files changed

### New

| File | What it does |
|------|-------------|
| `services/session_store.py` | In-memory `session_id:agent -> thread_id` mapping. Swap to Redis for prod (same get/set interface). |
| `scripts/test_session_memory.py` | 4 tests: 5-turn RAG memory stress test, session isolation, backwards compatibility, and SessionStore unit tests. |

### Modified

| File | What changed |
|------|-------------|
| `agents/orchestrator.py` | `process()` now accepts `session_id`. Before routing, looks up existing `thread_id` from `SessionStore`. After the agent responds, saves the `thread_id` back. Fully backwards compatible -- no `session_id` = fresh thread every time. |
| `models/requests.py` | Added `session_id` field to `QueryRequest`. |
| `models/responses.py` | Added `session_id` field to `QueryResponse`. |
| `api/router.py` | Both `/query` and `/query/stream` pass `session_id` through to the orchestrator. |

## How it works

```
Client sends: { session_id: "sess-123", message: "elaborate on step 1" }
                    |
    Orchestrator.process(message, session_id="sess-123")
                    |
    1. SessionStore.get_thread("sess-123", "rag")  ->  "thread_abc"  (from turn 1)
    2. RAGAgent.invoke(message, thread_id="thread_abc")               (continues same thread)
    3. Agent sees full history: turn 1 + turn 2 in the same thread
    4. SessionStore.set_thread("sess-123", "rag", "thread_abc")       (persists for turn 3)
```

## How to test

```bash
cd helpdesk-simple-af
python scripts/test_session_memory.py
```

## Production note

`SessionStore` uses an in-memory Python dict. For production, swap to Redis with a TTL so sessions auto-expire. The get/set interface is identical -- only the `__init__` changes.
