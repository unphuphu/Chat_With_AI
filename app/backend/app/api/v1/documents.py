"""/upload-batches, /documents (T02-03…T02-05, T07-01, T11-01, T11-04; openapi.yaml)."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any
from urllib.parse import quote
from uuid import UUID

from fastapi import APIRouter, Depends, File, Query, Request, Response, UploadFile
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, ConfigDict, Field

from app.api.deps import csrf_protected, current_session, get_container, rate_limited, request_id
from app.container import Container
from app.modules.identity.domain import SessionContext

router = APIRouter()


class FileIntent(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1, max_length=255)
    size_bytes: int = Field(ge=1)


class CreateBatchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    files: list[FileIntent] = Field(min_length=1)


@router.post("/upload-batches", status_code=201, tags=["uploads"])
async def create_batch(body: CreateBatchRequest, ctx: SessionContext = Depends(csrf_protected),
                       c: Container = Depends(get_container)) -> dict[str, Any]:
    return await c.documents.create_batch(ctx, [f.model_dump() for f in body.files])


async def _chunks(upload: UploadFile) -> AsyncIterator[bytes]:
    while chunk := await upload.read(256 * 1024):
        yield chunk


@router.put("/upload-batches/{batch_id}/files/{client_file_id}", tags=["uploads"],
            dependencies=[Depends(rate_limited("upload_file"))])
async def upload_file(batch_id: UUID, client_file_id: UUID, request: Request, response: Response,
                      file: UploadFile = File(...), ctx: SessionContext = Depends(csrf_protected),
                      c: Container = Depends(get_container)) -> JSONResponse:
    result = await c.documents.accept_file(ctx, batch_id, client_file_id, file.filename or "tai-lieu.pdf",
                                           _chunks(file), request_id(request))
    headers = {k: v for k, v in response.headers.items() if k.lower().startswith("ratelimit")}
    return JSONResponse(result.document.to_api(), status_code=201 if result.created else 200, headers=headers)


@router.get("/documents", tags=["documents"])
async def list_documents(ctx: SessionContext = Depends(current_session),
                         c: Container = Depends(get_container)) -> dict[str, Any]:
    docs = await c.documents.list(ctx.workspace_id)
    used, limit = await c.documents.quota(ctx.workspace_id)
    return {"items": [d.to_api() for d in docs], "documents_used": used, "documents_limit": limit}


@router.delete("/documents/{document_id}", status_code=204, tags=["documents"])
async def delete_document(document_id: UUID, request: Request, ctx: SessionContext = Depends(csrf_protected),
                          c: Container = Depends(get_container)) -> Response:
    await c.documents.soft_delete(ctx, document_id, request_id(request))
    return Response(status_code=204)


@router.post("/documents/{document_id}/reprocess", status_code=202, tags=["documents"])
async def reprocess(document_id: UUID, request: Request, ctx: SessionContext = Depends(csrf_protected),
                    c: Container = Depends(get_container)) -> dict[str, Any]:
    return (await c.documents.reprocess(ctx, document_id, request_id(request))).to_api()


@router.get("/documents/{document_id}/file", tags=["documents"])
async def document_file(document_id: UUID, from_: str | None = Query(None, alias="from"),
                        page: int | None = Query(None, ge=1), ctx: SessionContext = Depends(current_session),
                        c: Container = Depends(get_container)) -> StreamingResponse:
    name, stream = await c.documents.open_file(ctx, document_id, from_citation=from_ == "citation", page=page)
    return StreamingResponse(stream, media_type="application/pdf", headers={
        "Content-Disposition": f"inline; filename*=UTF-8''{quote(name)}",
        "Cache-Control": "private, no-store",
        # SPA nhúng file vào iframe (S06) bằng trình xem PDF của trình duyệt: chỉ cho phép cùng origin
        "X-Frame-Options": "SAMEORIGIN",
        "Content-Security-Policy": "frame-ancestors 'self'"})
