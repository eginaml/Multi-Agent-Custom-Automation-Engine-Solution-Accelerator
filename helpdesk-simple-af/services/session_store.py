"""In-session memory store for conversation thread persistence.

Maps session_id + agent type to an OpenAI Assistants thread_id so that
follow-up messages within the same session continue on the same thread.

Uses an in-memory dict for development. For production, swap the backend
to Redis (with TTL) or Cosmos DB by implementing the same get/set interface.
"""
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class SessionStore:
    """Stores session_id -> {agent: thread_id} mappings in memory."""

    def __init__(self):
        # TODO: For production, replace this dict with Redis:
        #   import redis.asyncio as redis
        #   self._redis = redis.from_url(settings.REDIS_URL)
        # Then in set_thread: self._redis.setex(key, TTL_SECONDS, thread_id)
        # And in get_thread: self._redis.get(key)
        # This gives you: (1) persistence across restarts, (2) auto-expiry via TTL,
        # (3) shared state across multiple app instances.
        # Do this if you expect to have multiple instances of your app running (e.g. in production)
        # or if you want session memory to survive app restarts. or for log running sessions.
        # long-running sessions will need a TTL longer than the default 1 hour.
        self._store: Dict[str, str] = {}

    def get_thread(self, session_id: str, agent: str) -> Optional[str]:
        """Look up existing thread_id for this session + agent.

        Returns None if no thread exists yet (first message in session).
        """
        key = f"{session_id}:{agent}"
        thread_id = self._store.get(key)
        if thread_id:
            logger.debug(f"Session hit: {key} -> {thread_id}")
        return thread_id

    def set_thread(self, session_id: str, agent: str, thread_id: str) -> None:
        """Store a thread_id for this session + agent."""
        key = f"{session_id}:{agent}"
        self._store[key] = thread_id
        logger.debug(f"Session store: {key} -> {thread_id}")

    def clear_session(self, session_id: str) -> int:
        """Remove all threads for a session. Returns number of entries cleared."""
        prefix = f"{session_id}:"
        keys_to_remove = [k for k in self._store if k.startswith(prefix)]
        for k in keys_to_remove:
            del self._store[k]
        if keys_to_remove:
            logger.info(f"Cleared {len(keys_to_remove)} thread(s) for session {session_id}")
        return len(keys_to_remove)

    def list_sessions(self) -> Dict[str, str]:
        """Return a copy of the full store (for debugging/testing)."""
        return dict(self._store)

    def __len__(self) -> int:
        return len(self._store)
