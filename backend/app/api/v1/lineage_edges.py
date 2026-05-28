"""CRUD API for lineage edges."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.response import Result, fail, success
from app.models.lineage_edge import LineageEdge
from app.schemas.lineage import LineageEdgeCreate, LineageEdgeOut

router = APIRouter(prefix="/edges", tags=["血缘边"])


@router.get("/", response_model=Result)
async def list_edges(
    source_node_id: str | None = None,
    target_node_id: str | None = None,
    lineage_stage: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(LineageEdge).where(LineageEdge.status == 1)
    if source_node_id:
        stmt = stmt.where(LineageEdge.source_node_id == source_node_id)
    if target_node_id:
        stmt = stmt.where(LineageEdge.target_node_id == target_node_id)
    if lineage_stage:
        stmt = stmt.where(LineageEdge.lineage_stage == lineage_stage)
    result = await db.execute(stmt)
    edges = result.scalars().all()
    return success(data=[LineageEdgeOut.model_validate(e) for e in edges])


@router.post("/", response_model=Result)
async def create_edge(body: LineageEdgeCreate, db: AsyncSession = Depends(get_db)):
    import uuid
    from datetime import datetime

    edge = LineageEdge(
        edge_id=str(uuid.uuid4()),
        **body.model_dump(exclude_none=True),
    )
    now = datetime.now()
    edge.create_time = now
    edge.update_time = now
    db.add(edge)
    await db.flush()
    return success(data=LineageEdgeOut.model_validate(edge), message="边创建成功")


@router.delete("/{edge_id}", response_model=Result)
async def delete_edge(edge_id: str, db: AsyncSession = Depends(get_db)):
    stmt = update(LineageEdge).where(LineageEdge.edge_id == edge_id).values(status=0)
    await db.execute(stmt)
    return success(message="边已删除")
