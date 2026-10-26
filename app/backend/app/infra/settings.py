"""Cấu hình ứng dụng (BLUEPRINT 3.6.6). Giá trị sai kiểu/ngoài khoảng → không khởi động được."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

APP_ROOT = Path(__file__).resolve().parents[3]  # .../app


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=(APP_ROOT / ".env", APP_ROOT / "backend" / ".env"),
                                      env_file_encoding="utf-8", extra="ignore")

    env: Literal["dev", "test", "staging", "production"] = "dev"

    # --- CSDL
    database_url: str = "postgresql://postgres:postgres@127.0.0.1:54329/postgres?sslmode=disable"
    # single: một kết nối dùng chung, tuần tự hóa (PGlite dev); pool: nhiều kết nối (PostgreSQL thật)
    db_mode: Literal["single", "pool"] = "single"
    db_pool_size: int = Field(10, ge=1, le=100)

    # --- Giao diện / URL công khai
    public_base_url: str = "http://localhost:8080"
    cookie_secure: bool = False  # True ở staging/production (HTTPS)

    # --- OIDC
    oidc_issuer: str = "http://localhost:8090"
    oidc_client_id: str = "aichat-dev"
    oidc_client_secret: str = "dev-secret-change-me"  # noqa: S105 – chỉ dev
    oidc_groups_claim: str = "groups"
    oidc_allowed_groups: str = "aichat-users,aichat-admins"
    oidc_admin_group: str = "aichat-admins"

    # --- Bí mật
    session_signing_key: str = "dev-session-signing-key-change-me-0123456789"
    actor_hash_key: str = "dev-actor-hash-key-change-me"
    llm_api_key: str = ""
    embedding_token: str = "dev-embedding-token"  # noqa: S105

    # --- Lưu trữ file
    blob_provider: Literal["local", "memory"] = "local"
    blob_dir: Path = APP_ROOT / ".data" / "blobs"

    # --- Giới hạn tải lên (NFR-006, NFR-019…NFR-021)
    max_file_mb: int = Field(20, ge=1, le=500)
    max_pages: int = Field(300, ge=1)
    max_files_per_batch: int = Field(10, ge=1, le=100)
    max_docs_per_workspace: int = Field(100, ge=1)
    batch_ttl_s: int = Field(600, ge=60)

    # --- Sandbox
    inspect_timeout_s: float = Field(10, gt=0)
    inspect_mem_mb: int = Field(256, ge=64)
    ingest_timeout_s: float = Field(120, gt=0)
    ingest_mem_mb: int = Field(1024, ge=128)
    sandbox_concurrency: int = Field(2, ge=1)
    sandbox_wait_s: float = Field(30, gt=0)

    # --- Ingest
    ingest_concurrency: int = Field(2, ge=1)
    ingest_max_attempts: int = Field(3, ge=1)
    min_chars_per_page: int = Field(20, ge=0)
    chunk_target_tokens: int = Field(500, ge=50)
    chunk_max_tokens: int = Field(800, ge=100)
    chunk_overlap_tokens: int = Field(80, ge=0)
    embed_batch: int = Field(32, ge=1, le=256)

    # --- Embedding
    embedding_provider: Literal["hashing", "http"] = "hashing"
    embedding_url: str = "http://localhost:8070"
    embedding_model_id: str = "hashing-ngram@v1"

    # --- Truy xuất (ALG-05)
    retrieval_candidates: int = Field(30, ge=1)
    retrieval_top_k: int = Field(8, ge=1, le=8)
    rrf_k: int = Field(60, ge=1)
    retrieval_min_similarity: float = Field(0.45, ge=0, le=1)
    hnsw_ef_search: int = Field(80, ge=10)

    # --- LLM (ALG-06)
    llm_provider: Literal["extractive", "anthropic", "fake"] = "extractive"
    llm_model: str = "claude-opus-5-5"  # ADR-007 đề xuất Sonnet 5.5 – đổi qua LLM_MODEL
    llm_effort: Literal["low", "medium", "high", "xhigh", "max"] = "medium"
    llm_fallbacks: bool = True
    answer_budget_s: float = Field(15, gt=0)
    llm_timeout_s: float = Field(10, gt=0)
    llm_retry_window_s: float = Field(3, ge=0)
    llm_safety_margin_s: float = Field(1.5, ge=0)
    llm_max_output_tokens: int = Field(16000, ge=256)  # gồm cả token thinking (Opus 5.5 luôn bật thinking)
    cb_failure_threshold: int = Field(5, ge=1)
    cb_window_s: float = Field(60, gt=0)
    cb_open_s: float = Field(30, gt=0)

    # --- Hỏi đáp, giới hạn tần suất
    question_max_chars: int = Field(2000, ge=1)
    rate_questions_per_min: int = Field(10, ge=1)
    rate_files_per_hour: int = Field(30, ge=1)

    # --- Phiên
    session_idle_min: int = Field(120, ge=1)
    session_absolute_h: int = Field(10, ge=1)

    # --- Lưu giữ
    purge_deadline_h: int = Field(24, ge=1)
    audit_retention_days: int = Field(90, ge=1)
    analytics_retention_days: int = Field(180, ge=1)

    # --- Chế độ chạy
    run_worker_in_api: bool = True  # bắt buộc khi db_mode=single
    log_level: str = "INFO"

    @model_validator(mode="after")
    def _check(self) -> Settings:
        if self.chunk_target_tokens > self.chunk_max_tokens:
            raise ValueError("CHUNK_TARGET_TOKENS phải ≤ CHUNK_MAX_TOKENS")
        if self.chunk_overlap_tokens >= self.chunk_target_tokens:
            raise ValueError("CHUNK_OVERLAP_TOKENS phải < CHUNK_TARGET_TOKENS")
        if self.db_mode == "single" and not self.run_worker_in_api:
            raise ValueError("DB_MODE=single yêu cầu RUN_WORKER_IN_API=true (chỉ một kết nối)")
        if self.env in ("staging", "production"):
            if not self.cookie_secure:
                raise ValueError("COOKIE_SECURE phải bật ở staging/production")
            for name in ("session_signing_key", "actor_hash_key", "oidc_client_secret"):
                if "change-me" in getattr(self, name):
                    raise ValueError(f"{name.upper()} chưa được đặt cho {self.env}")
        return self

    @property
    def allowed_groups(self) -> frozenset[str]:
        return frozenset(g.strip() for g in self.oidc_allowed_groups.split(",") if g.strip())

    @property
    def max_file_bytes(self) -> int:
        return self.max_file_mb * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    return Settings()
