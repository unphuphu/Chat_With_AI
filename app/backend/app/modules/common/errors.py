"""Lỗi nghiệp vụ có mã HTTP và `code` API (openapi.yaml `ErrorCode`). Tầng API chuyển thành RFC 9457."""

from __future__ import annotations

from typing import Any


class AppError(Exception):
    def __init__(self, status: int, code: str, detail: str | None = None, *,
                 headers: dict[str, str] | None = None, **extra: Any) -> None:
        super().__init__(code)
        self.status = status
        self.code = code
        self.detail = detail
        self.headers = headers or {}
        self.extra = extra
