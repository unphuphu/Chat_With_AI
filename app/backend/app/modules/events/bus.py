"""Phân phối sự kiện tới kết nối SSE theo workspace (BLUEPRINT 3.4.2).

Chế độ một tiến trình (DB_MODE=single): phát trực tiếp trong bộ nhớ. Chế độ nhiều bản API sẽ thay
`publish` bằng `pg_notify` + một kết nối LISTEN mỗi bản (cùng interface).
"""

from __future__ import annotations

import asyncio
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

QUEUE_MAX = 100


@dataclass
class Event:
    name: str
    data: dict[str, Any]
    id: int = field(default_factory=lambda: int(time.time() * 1000))


class Subscription:
    def __init__(self, bus: EventBus, ws: UUID) -> None:
        self.bus, self.ws = bus, ws
        self.queue: asyncio.Queue[Event | None] = asyncio.Queue(maxsize=QUEUE_MAX)
        self.closed = False

    def close(self) -> None:
        if not self.closed:
            self.closed = True
            self.bus._subs[self.ws].discard(self)


class EventBus:
    def __init__(self) -> None:
        self._subs: dict[UUID, set[Subscription]] = defaultdict(set)

    def subscribe(self, ws: UUID) -> Subscription:
        sub = Subscription(self, ws)
        self._subs[ws].add(sub)
        return sub

    def publish(self, ws: UUID, name: str, data: dict[str, Any]) -> None:
        ev = Event(name, data)
        for sub in list(self._subs.get(ws, ())):
            try:
                sub.queue.put_nowait(ev)
            except asyncio.QueueFull:
                # Client chậm: đóng kết nối, client tự kết nối lại và đồng bộ (CA-03)
                sub.close()
                sub.queue = asyncio.Queue(maxsize=1)
                sub.queue.put_nowait(None)

    def subscriber_count(self, ws: UUID) -> int:
        return len(self._subs.get(ws, ()))
