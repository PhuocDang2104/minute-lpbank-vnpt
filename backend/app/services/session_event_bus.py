import asyncio
from collections import defaultdict
from typing import Any, Dict, Set


class SessionEventBus:
    """
    Lightweight in-memory pub/sub for session-scoped realtime events.
    Each subscriber gets an asyncio.Queue. Best-effort delivery; slow
    consumers may drop messages when their queue is full.
    """

    def __init__(self, max_queue_size: int = 100) -> None:
        self.subscribers: Dict[str, Set[asyncio.Queue]] = defaultdict(set)
        self.seq_counter: Dict[str, int] = defaultdict(int)
        self.max_queue_size = max_queue_size

    def subscribe(self, session_id: str) -> asyncio.Queue:
        queue: asyncio.Queue = asyncio.Queue(maxsize=self.max_queue_size)
        self.subscribers[session_id].add(queue)
        return queue

    def unsubscribe(self, session_id: str, queue: asyncio.Queue) -> None:
        subscribers = self.subscribers.get(session_id)
        if not subscribers:
            return
        subscribers.discard(queue)
        if not subscribers:
            self.subscribers.pop(session_id, None)
            # Keep seq_counter to preserve monotonic ordering even if all clients disconnect.
            # A session can be explicitly cleaned up by calling `clear_session()`.

    def clear_session(self, session_id: str) -> None:
        """Remove all subscribers and reset seq counter for a session (explicit cleanup)."""
        self.subscribers.pop(session_id, None)
        self.seq_counter.pop(session_id, None)

    def _next_seq(self, session_id: str) -> int:
        self.seq_counter[session_id] = self.seq_counter.get(session_id, 0) + 1
        return self.seq_counter[session_id]

    async def publish(self, session_id: str, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Publish an event to all subscribers of a session.
        Returns the envelope with seq/session_id attached.
        """
        envelope = dict(event or {})
        envelope["session_id"] = session_id
        envelope.setdefault("seq", self._next_seq(session_id))

        for queue in list(self.subscribers.get(session_id, [])):
            try:
                queue.put_nowait(envelope)
            except asyncio.QueueFull:
                try:
                    queue.get_nowait()  # drop oldest
                    queue.put_nowait(envelope)
                except Exception:
                    # If the consumer is still too slow, drop the event for that subscriber
                    pass

        return envelope
