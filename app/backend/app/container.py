"""Composition root (BLUEPRINT 3.3): nơi DUY NHẤT khởi tạo adapter và tiêm vào service."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.infra.circuit import CircuitBreaker
from app.infra.db import Database
from app.infra.jobs import JobSignal
from app.infra.sandbox import Sandbox
from app.infra.settings import Settings
from app.modules.documents.service import DocumentService
from app.modules.events.bus import EventBus
from app.modules.identity.service import IdentityService
from app.modules.ingestion.pipeline import IngestionPipeline
from app.modules.qa.answerer import Answerer
from app.modules.qa.service import QAService
from app.modules.retrieval.service import RetrievalService
from app.ports.blob import BlobPort
from app.ports.embedding import EmbeddingPort
from app.ports.identity import IdentityPort
from app.ports.llm import LlmPort


def build_blob(s: Settings) -> BlobPort:
    if s.blob_provider == "memory":
        from app.adapters.blob_memory import MemoryBlobStore

        return MemoryBlobStore()
    from app.adapters.blob_local import LocalBlobStore

    return LocalBlobStore(s.blob_dir)


def build_embedding(s: Settings) -> EmbeddingPort:
    if s.embedding_provider == "http":
        from app.adapters.embedding_http import HttpEmbedding

        return HttpEmbedding(s.embedding_url, s.embedding_token, s.embedding_model_id)
    from app.adapters.embedding_hashing import HashingEmbedding

    return HashingEmbedding(s.embedding_model_id)


def build_llm(s: Settings) -> LlmPort:
    if s.llm_provider == "anthropic":
        from app.adapters.llm_anthropic import AnthropicLlm

        return AnthropicLlm(s.llm_api_key, s.llm_model, s.llm_effort, s.llm_fallbacks)
    if s.llm_provider == "fake":
        from app.adapters.llm_fake import FakeLlm

        return FakeLlm()
    from app.adapters.llm_extractive import ExtractiveLlm

    return ExtractiveLlm()


def build_identity(s: Settings) -> IdentityPort:
    from app.adapters.oidc import OidcClient

    return OidcClient(s.oidc_issuer, s.oidc_client_id, s.oidc_client_secret, s.oidc_groups_claim)


@dataclass
class Container:
    settings: Settings
    db: Database
    blob: BlobPort
    embedding: EmbeddingPort
    llm: LlmPort
    idp: IdentityPort
    bus: EventBus = field(default_factory=EventBus)
    job_signal: JobSignal = field(default_factory=JobSignal)
    sandbox: Sandbox = field(init=False)
    breaker: CircuitBreaker = field(init=False)
    identity: IdentityService = field(init=False)
    documents: DocumentService = field(init=False)
    ingestion: IngestionPipeline = field(init=False)
    retrieval: RetrievalService = field(init=False)
    answerer: Answerer = field(init=False)
    qa: QAService = field(init=False)
    extras: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        s = self.settings
        self.sandbox = Sandbox(s.sandbox_concurrency, s.sandbox_wait_s)
        self.breaker = CircuitBreaker(s.cb_failure_threshold, s.cb_window_s, s.cb_open_s)
        self.identity = IdentityService(self.db, self.idp, s)
        self.documents = DocumentService(self.db, self.blob, self.sandbox, self.bus, self.job_signal, s)
        self.ingestion = IngestionPipeline(self.db, self.blob, self.embedding, self.sandbox, self.bus, s)
        self.retrieval = RetrievalService(self.db, self.embedding, s)
        self.answerer = Answerer(self.llm, self.breaker, s)
        self.qa = QAService(self.db, self.retrieval, self.answerer, s)

    @classmethod
    def from_settings(cls, s: Settings, **overrides: Any) -> Container:
        return cls(
            settings=s,
            db=overrides.get("db") or Database(s.database_url, s.db_mode, s.db_pool_size),
            blob=overrides.get("blob") or build_blob(s),
            embedding=overrides.get("embedding") or build_embedding(s),
            llm=overrides.get("llm") or build_llm(s),
            idp=overrides.get("idp") or build_identity(s),
        )
