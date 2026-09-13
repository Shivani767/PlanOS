"""Knowledge routes: tenant-scoped ingest + search (Phase 12)."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from planos.app.api.dependencies import AuthenticatedUser, require_permission_factory
from planos.app.core.permissions import Permission
from planos.app.db.session import get_session
from planos.app.services.knowledge import KnowledgeService

router = APIRouter(prefix="/knowledge", tags=["Knowledge"])

require_read = require_permission_factory(Permission.PLAN_READ)
require_write = require_permission_factory(Permission.PLAN_CREATE)


class IngestRequest(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    content: str = Field(min_length=1, max_length=200000)
    document_type: str = Field(default="policy", max_length=50)
    department: str | None = Field(default=None, max_length=100)


@router.post("/documents", status_code=status.HTTP_201_CREATED)
async def ingest_document(
    data: IngestRequest,
    current_user: Annotated[AuthenticatedUser, Depends(require_write)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict[str, Any]:
    doc = await KnowledgeService(session).ingest(
        current_user.organization_id,
        data.title,
        data.content,
        data.document_type,
        data.department,
        created_by=current_user.user_id,
    )
    return {"id": doc.id, "title": doc.title, "document_type": doc.document_type}


@router.get("/search")
async def search(
    current_user: Annotated[AuthenticatedUser, Depends(require_read)],
    session: Annotated[AsyncSession, Depends(get_session)],
    q: str = "",
    top_k: int = 5,
) -> dict[str, Any]:
    chunks = await KnowledgeService(session).search(
        current_user.organization_id, q, max(1, min(top_k, 20))
    )
    return {"query": q, "chunks": chunks}


@router.get("/documents")
async def list_documents(
    current_user: Annotated[AuthenticatedUser, Depends(require_read)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[dict[str, Any]]:
    from planos.app.models import KnowledgeDocument

    rows = (
        (
            await session.execute(
                select(KnowledgeDocument)
                .where(KnowledgeDocument.organization_id == current_user.organization_id)
                .order_by(KnowledgeDocument.created_at.desc())
                .limit(100)
            )
        )
        .scalars()
        .all()
    )
    return [
        {"id": d.id, "title": d.title, "document_type": d.document_type, "department": d.department}
        for d in rows
    ]
