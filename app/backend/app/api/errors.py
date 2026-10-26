"""Lỗi theo RFC 9457 với `code` máy đọc được (openapi.yaml `Problem`, API_DESIGN 3.5, AD-10)."""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.infra.logging import get_logger
from app.modules.common.errors import AppError

log = get_logger("api.errors")

TITLES: dict[str, str] = {
    "unauthenticated": "Chưa đăng nhập",
    "session_expired": "Phiên làm việc đã hết hạn",
    "csrf_invalid": "Phiên không hợp lệ",
    "not_found": "Không tìm thấy",
    "batch_expired": "Phiên tải lên đã hết hạn",
    "batch_full": "Đã tải đủ số file của lần này",
    "no_ready_documents": "Chưa có tài liệu Sẵn sàng",
    "not_retryable": "Không thể xử lý lại tài liệu này",
    "request_in_progress": "Câu hỏi đang được xử lý",
    "deleted": "Tài liệu đã bị xóa",
    "too_many_files": "Quá số file cho phép mỗi lần",
    "quota_exceeded": "Vượt hạn mức tài liệu",
    "not_pdf": "File không hợp lệ",
    "too_large": "File quá dung lượng",
    "too_many_pages": "File quá số trang",
    "encrypted": "File có mật khẩu",
    "empty_question": "Câu hỏi trống",
    "question_too_long": "Câu hỏi quá dài",
    "idempotency_mismatch": "Không gửi được câu hỏi",
    "rate_limited": "Thao tác quá nhanh",
    "ai_unavailable": "Không thể tạo câu trả lời lúc này",
    "storage_unavailable": "Chưa lưu được file",
    "server_busy": "Hệ thống đang bận",
    "ai_timeout": "Câu trả lời mất quá nhiều thời gian",
    "invalid_request": "Yêu cầu không hợp lệ",
    "internal_error": "Đã có lỗi xảy ra",
}


ProblemException = AppError  # tên cũ, dùng trong tầng API


def problem_body(request: Request, status: int, code: str, detail: str | None, **extra: Any) -> dict[str, Any]:
    body: dict[str, Any] = {
        "type": f"https://errors.aichat.local/{code}",
        "title": TITLES.get(code, code),
        "status": status,
        "code": code,
        "detail": detail or TITLES.get(code, code),
        "request_id": getattr(request.state, "request_id", "00000000-0000-0000-0000-000000000000"),
    }
    body.update(extra)
    return body


def _resp(request: Request, status: int, code: str, detail: str | None = None,
          headers: dict[str, str] | None = None, **extra: Any) -> JSONResponse:
    return JSONResponse(problem_body(request, status, code, detail, **extra), status_code=status,
                        media_type="application/problem+json", headers=headers)


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def _problem(request: Request, exc: AppError) -> JSONResponse:
        return _resp(request, exc.status, exc.code, exc.detail, exc.headers, **exc.extra)

    @app.exception_handler(RequestValidationError)
    async def _validation(request: Request, exc: RequestValidationError) -> JSONResponse:
        code = "invalid_request"
        for err in exc.errors():
            loc = err.get("loc", ())
            if "question" in loc:
                code = "question_too_long" if err.get("type") == "string_too_long" else "empty_question"
                break
        return _resp(request, 422, code)

    @app.exception_handler(StarletteHTTPException)
    async def _http(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        mapping = {404: "not_found", 405: "invalid_request", 401: "unauthenticated", 413: "too_large"}
        return _resp(request, exc.status_code, mapping.get(exc.status_code, "invalid_request"))

    @app.exception_handler(Exception)
    async def _unexpected(request: Request, exc: Exception) -> JSONResponse:
        log.exception("unhandled_error", error_type=type(exc).__name__)
        return _resp(request, 500, "internal_error",
                     f"Đã có lỗi xảy ra. Mã tham chiếu: {getattr(request.state, 'request_id', '')}")
