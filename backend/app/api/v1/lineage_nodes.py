"""CRUD API for lineage nodes."""

from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.response import Result, fail, success
from app.models.lineage_node import LineageNode
from app.models.lineage_node_column import LineageNodeColumn
from app.schemas.lineage import (
    LineageNodeCreate,
    LineageNodeOut,
    LineageNodeUpdate,
)

router = APIRouter(prefix="/nodes", tags=["血缘节点"])


@router.get("/", response_model=Result)
async def list_nodes(
    node_type: str | None = Query(None),
    system_code: str | None = Query(None),
    table_name: str | None = Query(None),
    cluster_id: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(LineageNode).where(LineageNode.status == 1)
    if node_type:
        stmt = stmt.where(LineageNode.node_type == node_type)
    if system_code:
        stmt = stmt.where(LineageNode.system_code == system_code)
    if table_name:
        stmt = stmt.where(LineageNode.table_name.like(f"%{table_name}%"))
    if cluster_id:
        stmt = stmt.where(LineageNode.cluster_id == cluster_id)

    # Count (apply same filters)
    count_stmt = select(func.count()).select_from(LineageNode).where(LineageNode.status == 1)
    if node_type:
        count_stmt = count_stmt.where(LineageNode.node_type == node_type)
    if system_code:
        count_stmt = count_stmt.where(LineageNode.system_code == system_code)
    if table_name:
        count_stmt = count_stmt.where(LineageNode.table_name.like(f"%{table_name}%"))
    if cluster_id:
        count_stmt = count_stmt.where(LineageNode.cluster_id == cluster_id)
    count_result = await db.execute(count_stmt)
    total = count_result.scalar() or 0

    # Paginate
    stmt = stmt.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(stmt)
    nodes = result.scalars().all()
    return success(data={"items": [LineageNodeOut.model_validate(n) for n in nodes], "total": total})


@router.get("/{node_id}", response_model=Result)
async def get_node(node_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(LineageNode).where(LineageNode.node_id == node_id))
    node = result.scalar_one_or_none()
    if not node:
        return fail(code=404, message="节点不存在")
    return success(data=LineageNodeOut.model_validate(node))


@router.post("/", response_model=Result)
async def create_node(body: LineageNodeCreate, db: AsyncSession = Depends(get_db)):
    from datetime import datetime

    import uuid

    node = LineageNode(
        node_id=str(uuid.uuid4()),
        **body.model_dump(exclude_none=True),
    )
    now = datetime.now()
    node.create_time = now
    node.update_time = now
    db.add(node)
    await db.flush()
    return success(data=LineageNodeOut.model_validate(node), message="节点创建成功")


@router.put("/{node_id}", response_model=Result)
async def update_node(node_id: str, body: LineageNodeUpdate, db: AsyncSession = Depends(get_db)):
    data = body.model_dump(exclude_none=True)
    if not data:
        return fail(code=400, message="无更新内容")
    data["update_time"] = __import__("datetime").datetime.now()
    stmt = update(LineageNode).where(LineageNode.node_id == node_id).values(**data)
    await db.execute(stmt)
    return success(message="节点更新成功")


@router.delete("/{node_id}", response_model=Result)
async def delete_node(node_id: str, db: AsyncSession = Depends(get_db)):
    stmt = update(LineageNode).where(LineageNode.node_id == node_id).values(status=0)
    await db.execute(stmt)
    return success(message="节点已删除")


@router.get("/{node_id}/columns", response_model=Result)
async def list_node_columns(node_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(LineageNodeColumn)
        .where(LineageNodeColumn.node_id == node_id)
        .order_by(LineageNodeColumn.column_order)
    )
    columns = result.scalars().all()
    from app.schemas.lineage import LineageNodeColumnOut
    return success(data=[LineageNodeColumnOut.model_validate(c) for c in columns])
