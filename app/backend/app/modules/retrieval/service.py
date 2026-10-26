"""ALG-05 – truy xuất kết hợp vector + full-text, hợp nhất RRF, cổng ngưỡng (SAD ADR-009).

Theo bất biến "đoạn tồn tại ⇔ tài liệu READY và chưa xóa", truy vấn chỉ quét bảng `chunk` (B-DEF-003).
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from uuid import UUID

from app.infra.db import Database
from app.infra.settings import Settings
from app.ports.embedding import EmbeddingPort

HYBRID_SQL = """
WITH v_raw AS (
    SELECT c.id, c.embedding <=> %(qvec)s::vector AS dist
    FROM chunk c
    WHERE c.workspace_id = %(ws)s AND c.embedding_model = %(model)s
    ORDER BY c.embedding <=> %(qvec)s::vector
    LIMIT %(candidates)s
),
v AS (SELECT id, 1 - dist AS sim, row_number() OVER (ORDER BY dist) AS r FROM v_raw),
t_raw AS (
    SELECT c.id, ts_rank_cd(c.tsv, q) AS rank
    FROM chunk c, to_tsquery('simple', %(qtext)s) q
    WHERE %(qtext)s <> '' AND c.workspace_id = %(ws)s AND c.embedding_model = %(model)s AND c.tsv @@ q
    ORDER BY rank DESC
    LIMIT %(candidates)s
),
t AS (SELECT id, row_number() OVER (ORDER BY rank DESC) AS r FROM t_raw),
fused AS (
    SELECT id, sum(1.0 / (%(rrf_k)s + r)) AS rrf, max(sim) AS sim
    FROM (SELECT id, r, sim FROM v UNION ALL SELECT id, r, NULL::float8 FROM t) u
    GROUP BY id
)
SELECT f.id, f.rrf, f.sim, c.document_id, d.file_name, c.page_number, c.content,
       (SELECT max(sim) FROM v) AS top_similarity, (SELECT count(*) FROM t) AS fulltext_hits
FROM fused f JOIN chunk c ON c.id = f.id JOIN document d ON d.id = c.document_id
ORDER BY f.rrf DESC
LIMIT %(top_k)s
"""


@dataclass(frozen=True)
class RetrievedChunk:
    chunk_id: UUID
    document_id: UUID
    document_name: str
    page_number: int
    content: str
    rrf_score: float
    vector_similarity: float | None


@dataclass(frozen=True)
class RetrievalResult:
    chunks: list[RetrievedChunk]
    top_similarity: float | None
    fulltext_hits: int
    min_similarity: float

    @property
    def below_gate(self) -> bool:
        if not self.chunks:
            return True
        return (self.top_similarity is None or self.top_similarity < self.min_similarity) and self.fulltext_hits == 0


_WORD = re.compile(r"\w+", re.UNICODE)
# Từ hỏi/hư từ: không mang nội dung, nếu đưa vào truy vấn AND thì gần như không đoạn nào khớp
STOPWORDS = frozenset("""
là gì của và các những có không cho với trong thế nào bao nhiêu được một này đó khi thì tại theo về từ đến ở
ai sao hay như bị ra vào lên đã đang sẽ cần phải nên hơn nhất rất làm nếu hỏi biết tôi bạn chúng ta mình
a an of and or is are what which who how much many in on for to does do with by about from this that be it as the
""".split())


def fulltext_query(question: str, max_terms: int = 12) -> str:
    """Câu hỏi → tsquery OR các từ có nghĩa ('giá | gói | premium'); xếp hạng bằng ts_rank_cd (ALG-05)."""
    words = _WORD.findall(unicodedata.normalize("NFC", question).lower())
    terms = list(dict.fromkeys(w for w in words if w not in STOPWORDS and (len(w) > 1 or w.isdigit())))
    return " | ".join(terms[:max_terms])


def to_vector_literal(v: list[float]) -> str:
    return "[" + ",".join(f"{x:.6f}" for x in v) + "]"


class RetrievalService:
    def __init__(self, db: Database, embedding: EmbeddingPort, settings: Settings) -> None:
        self._db, self._emb, self._s = db, embedding, settings

    async def retrieve(self, ws: UUID, question: str, *, top_k: int | None = None) -> RetrievalResult:
        qvec = (await self._emb.embed([question], purpose="query", timeout_s=2))[0]
        params = {"qvec": to_vector_literal(qvec), "ws": ws, "model": self._emb.model_id,
                  "qtext": fulltext_query(question),
                  "candidates": self._s.retrieval_candidates, "rrf_k": self._s.rrf_k,
                  "top_k": top_k or self._s.retrieval_top_k}
        async with self._db.tx("app_api", ws) as conn:
            await conn.execute(f"SET LOCAL hnsw.ef_search = {int(self._s.hnsw_ef_search)}")
            await conn.execute("SET LOCAL hnsw.iterative_scan = relaxed_order")
            cur = await conn.execute(HYBRID_SQL, params)  # type: ignore[arg-type]
            rows = await cur.fetchall()
        chunks = [RetrievedChunk(r["id"], r["document_id"], r["file_name"], r["page_number"], r["content"],
                                 float(r["rrf"]), float(r["sim"]) if r["sim"] is not None else None) for r in rows]
        top = float(rows[0]["top_similarity"]) if rows and rows[0]["top_similarity"] is not None else None
        hits = int(rows[0]["fulltext_hits"]) if rows else 0
        return RetrievalResult(chunks, top, hits, self._s.retrieval_min_similarity)
