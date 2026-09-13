"""Knowledge service: tenant-scoped ingest + ranked retrieval (Phase 12)."""

from __future__ import annotations

import hashlib
import math
import re
from collections import Counter

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from planos.app.core.exceptions import NotFoundError
from planos.app.models import KnowledgeChunk, KnowledgeDocument

_WORD = re.compile(r"[a-z0-9]+")


def _tokens(text: str) -> list[str]:
    return _WORD.findall(text.lower())


def _embed(text: str, dim: int = 64) -> list[float]:
    """Deterministic hash-bucket embedding (no external dependency)."""
    vec = [0.0] * dim
    for tok in _tokens(text):
        h = int(hashlib.sha256(tok.encode()).hexdigest(), 16)
        vec[h % dim] += 1.0
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]


def _cosine(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def chunk_text(content: str, max_tokens: int = 200) -> list[str]:
    words = content.split()
    chunks, cur = [], []
    for w in words:
        cur.append(w)
        if len(cur) >= max_tokens:
            chunks.append(" ".join(cur))
            cur = []
    if cur:
        chunks.append(" ".join(cur))
    return chunks or [content]


class KnowledgeService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def ingest(
        self,
        organization_id: str,
        title: str,
        content: str,
        document_type: str = "policy",
        department: str | None = None,
        created_by: str | None = None,
    ) -> KnowledgeDocument:
        doc = KnowledgeDocument(
            organization_id=organization_id,
            title=title,
            content=content,
            document_type=document_type,
            department=department,
            created_by=created_by,
        )
        self.session.add(doc)
        await self.session.flush()
        for i, piece in enumerate(chunk_text(content)):
            self.session.add(
                KnowledgeChunk(
                    organization_id=organization_id,
                    document_id=doc.id,
                    chunk_index=i,
                    content=piece,
                    embedding=_embed(piece),
                    token_count=len(piece.split()),
                )
            )
        await self.session.commit()
        await self.session.refresh(doc)
        return doc

    async def search(self, organization_id: str, query: str, top_k: int = 5) -> list[dict]:
        """Tenant-scoped: never touches other orgs' chunks."""
        rows = (
            (
                await self.session.execute(
                    select(KnowledgeChunk)
                    .where(KnowledgeChunk.organization_id == organization_id)
                    .limit(2000)
                )
            )
            .scalars()
            .all()
        )
        q_emb = _embed(query)
        q_terms = Counter(_tokens(query))
        scored = []
        for c in rows:
            emb = c.embedding or _embed(c.content)
            overlap = sum(q_terms[t] for t in _tokens(c.content) if t in q_terms)
            score = 0.7 * _cosine(q_emb, emb) + 0.3 * min(overlap / 5.0, 1.0)
            scored.append((score, c))
        scored.sort(key=lambda t: t[0], reverse=True)
        return [
            {
                "document_id": c.document_id,
                "chunk_index": c.chunk_index,
                "content": c.content[:2000],
                "score": round(s, 4),
            }
            for s, c in scored[:top_k]
        ]

    async def count(self, organization_id: str) -> int:
        total = await self.session.execute(
            select(func.count(KnowledgeDocument.id)).where(
                KnowledgeDocument.organization_id == organization_id
            )
        )
        return int(total.scalar() or 0)

    async def get(self, document_id: str, organization_id: str) -> KnowledgeDocument:
        row = await self.session.execute(
            select(KnowledgeDocument).where(
                KnowledgeDocument.id == document_id,
                KnowledgeDocument.organization_id == organization_id,
            )
        )
        doc = row.scalar_one_or_none()
        if doc is None:
            raise NotFoundError("KnowledgeDocument", document_id)
        return doc
