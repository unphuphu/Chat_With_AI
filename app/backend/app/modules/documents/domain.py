from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Literal
from uuid import UUID


class DocumentStatus(StrEnum):
    PROCESSING = "PROCESSING"
    READY = "READY"
    FAILED = "FAILED"


class FailureCode(StrEnum):
    R01 = "R-01"  # không đọc được
    R02 = "R-02"  # có mật khẩu
    R03 = "R-03"  # không có văn bản (PDF scan)
    R04 = "R-04"  # lỗi tạm thời – được xử lý lại


RETRYABLE: frozenset[FailureCode] = frozenset({FailureCode.R04})

RejectCode = Literal["not_pdf", "too_large", "too_many_pages", "encrypted"]


@dataclass(frozen=True)
class InspectionResult:
    ok: bool
    page_count: int | None = None
    reject_code: RejectCode | None = None


@dataclass(frozen=True)
class Document:
    id: UUID
    file_name: str
    status: DocumentStatus
    failure_code: FailureCode | None
    page_count: int
    size_bytes: int
    uploaded_at: datetime
    ready_at: datetime | None

    @property
    def retryable(self) -> bool:
        return self.failure_code in RETRYABLE

    def to_api(self) -> dict[str, object]:
        return {
            "id": str(self.id), "file_name": self.file_name, "status": self.status.value,
            "failure_code": self.failure_code.value if self.failure_code else None,
            "retryable": self.retryable, "page_count": self.page_count, "size_bytes": self.size_bytes,
            "uploaded_at": self.uploaded_at.isoformat().replace("+00:00", "Z"),
            "ready_at": self.ready_at.isoformat().replace("+00:00", "Z") if self.ready_at else None,
        }
