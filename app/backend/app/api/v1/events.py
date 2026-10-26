"""GET /events – Server-Sent Events theo workspace (T03-06, BLUEPRINT 3.4.2, openapi.yaml)."""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse

from app.api.deps import current_session, get_container
from app.container import Container
from app.modules.identity.domain import SessionContext

router = APIRouter(tags=["events"])
PING_S = 25


@router.get("/events")
async def events(request: Request, ctx: SessionContext = Depends(current_session),
                 c: Container = Depends(get_container)) -> StreamingResponse:
    sub = c.bus.subscribe(ctx.workspace_id)

    async def stream() -> AsyncIterator[str]:
        warned = False
        try:
            yield "retry: 5000\n\n"
            while True:
                if await request.is_disconnected():
                    break
                if not warned and ctx.expires_at - datetime.now(UTC) <= timedelta(minutes=5):
                    warned = True
                    data = json.dumps({"expires_at": ctx.expires_at.isoformat().replace("+00:00", "Z")})
                    yield f"event: session.expiring\ndata: {data}\n\n"
                try:
                    ev = await asyncio.wait_for(sub.queue.get(), timeout=PING_S)
                except TimeoutError:
                    yield ": ping\n\n"
                    continue
                if ev is None:  # client chậm bị đóng – client tự kết nối lại
                    break
                yield f"id: {ev.id}\nevent: {ev.name}\ndata: {json.dumps(ev.data, ensure_ascii=False)}\n\n"
        finally:
            sub.close()

    return StreamingResponse(stream(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})
