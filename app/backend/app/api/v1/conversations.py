"""/conversations/current, POST /conversations/{id}/messages (T04-04, T09-02, T11-02)."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Request, Response
from pydantic import BaseModel, ConfigDict, Field

from app.api.deps import csrf_protected, current_session, get_container, rate_limited, request_id
from app.container import Container
from app.modules.identity.domain import SessionContext

router = APIRouter(tags=["conversations"])


class AskRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    client_request_id: UUID
    question: str = Field(min_length=1)


@router.get("/conversations/current")
async def current(ctx: SessionContext = Depends(current_session),
                  c: Container = Depends(get_container)) -> dict[str, Any]:
    return await c.qa.current_conversation(ctx)


@router.post("/conversations/{conversation_id}/messages",
             dependencies=[Depends(rate_limited("question"))])
async def ask(conversation_id: UUID, body: AskRequest, request: Request, response: Response,
              ctx: SessionContext = Depends(csrf_protected), c: Container = Depends(get_container)) -> dict[str, Any]:
    return await c.qa.ask(ctx, conversation_id, body.client_request_id, body.question, request_id(request))
