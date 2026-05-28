"""Lineage analysis & graph query API."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.response import Result, fail, success
from app.models.lineage_column_edge import LineageColumnEdge
from app.models.lineage_edge import LineageEdge
from app.models.lineage_node import LineageNode
from app.models.lineage_node_column import LineageNodeColumn
from app.schemas.lineage import (
    LineageColumnEdgeOut,
    LineageEdgeOut,
    LineageGraphOut,
    LineageNodeColumnOut,
    LineageNodeOut,
    LineageQueryRequest,
)

router = APIRouter(prefix="/analysis", tags=["血缘分析"])


@router.post("/query", response_model=Result)
async def query_lineage(body: LineageQueryRequest, db: AsyncSession = Depends(get_db)):
    """Query lineage graph centered on a table."""
    # 1. Find the center node
    stmt = select(LineageNode).where(
        LineageNode.table_name == body.table_name,
        LineageNode.status == 1,
    )
    if body.cluster_id:
        stmt = stmt.where(LineageNode.cluster_id == body.cluster_id)
    if body.system_code:
        stmt = stmt.where(LineageNode.system_code == body.system_code)
    result = await db.execute(stmt)
    center_node = result.scalar_one_or_none()
    if not center_node:
        return fail(code=404, message=f"未找到表 {body.table_name}")

    center_id = center_node.node_id
    upstream_nodes = []
    downstream_nodes = []
    edges = []

    visited = {center_id}
    if body.direction in ("UPSTREAM", "BOTH"):
        upstream_nodes, upstream_edges = await _traverse(
            db, center_id, "UPSTREAM", body.depth, body.lineage_type, visited
        )
        edges.extend(upstream_edges)

    if body.direction in ("DOWNSTREAM", "BOTH"):
        down_nodes, down_edges = await _traverse(
            db, center_id, "DOWNSTREAM", body.depth, body.lineage_type, visited
        )
        downstream_nodes.extend(down_nodes)
        edges.extend(down_edges)

    # If COLUMN edges exist, also fetch column-level mapping details
    column_edges = []
    col_edge_ids = [e.edge_id for e in edges if e.lineage_type == "COLUMN"]

    # Query column definitions for all involved nodes
    node_columns = []
    all_node_ids = [center_id] + [n.node_id for n in upstream_nodes] + [n.node_id for n in downstream_nodes]

    # For OPERATOR mode, also fetch COLUMN edge IDs to surface operator detail
    if body.lineage_type == "OPERATOR" and all_node_ids:
        extra_ce_stmt = select(LineageEdge.edge_id).where(
            or_(
                LineageEdge.source_node_id.in_(all_node_ids),
                LineageEdge.target_node_id.in_(all_node_ids),
            ),
            LineageEdge.lineage_type == "COLUMN",
            LineageEdge.status == 1,
        )
        extra_result = await db.execute(extra_ce_stmt)
        col_edge_ids.extend([r[0] for r in extra_result])

    if col_edge_ids:
        ce_stmt = select(LineageColumnEdge).where(
            LineageColumnEdge.edge_id.in_(col_edge_ids),
            LineageColumnEdge.status == 1,
        )
        ce_result = await db.execute(ce_stmt)
        column_edges = [LineageColumnEdgeOut.model_validate(r) for r in ce_result.scalars().all()]

    if all_node_ids and body.lineage_type in ("COLUMN", "OPERATOR", "ALL"):
        nc_stmt = select(LineageNodeColumn).where(
            LineageNodeColumn.node_id.in_(all_node_ids),
            LineageNodeColumn.status == 1,
        ).order_by(LineageNodeColumn.node_id, LineageNodeColumn.column_order)
        nc_result = await db.execute(nc_stmt)
        node_columns = [LineageNodeColumnOut.model_validate(r) for r in nc_result.scalars().all()]

    return success(
        data=LineageGraphOut(
            center_node=LineageNodeOut.model_validate(center_node),
            upstream_nodes=[LineageNodeOut.model_validate(n) for n in upstream_nodes],
            downstream_nodes=[LineageNodeOut.model_validate(n) for n in downstream_nodes],
            edges=[LineageEdgeOut.model_validate(e) for e in edges],
            column_edges=column_edges,
            node_columns=node_columns,
            total_nodes=1 + len(upstream_nodes) + len(downstream_nodes),
            total_edges=len(edges),
        )
    )


async def _traverse(
    db: AsyncSession,
    start_id: str,
    direction: str,
    max_depth: int,
    lineage_type: str,
    visited: set,
) -> tuple[list, list]:
    """BFS traversal of lineage graph, filtered by lineage_type (TABLE/COLUMN/OPERATOR/ALL)."""
    nodes = []
    edges = []
    current_level = [start_id]
    depth = 0

    while current_level and depth < max_depth:
        depth += 1
        next_level = []

        if direction == "UPSTREAM":
            edge_stmt = select(LineageEdge).where(
                LineageEdge.target_node_id.in_(current_level),
                LineageEdge.status == 1,
            )
        else:
            edge_stmt = select(LineageEdge).where(
                LineageEdge.source_node_id.in_(current_level),
                LineageEdge.status == 1,
            )

        if lineage_type != "ALL":
            if lineage_type == "OPERATOR":
                edge_stmt = edge_stmt.where(LineageEdge.lineage_type.in_(["TABLE", "OPERATOR"]))
            else:
                edge_stmt = edge_stmt.where(LineageEdge.lineage_type == lineage_type)

        result = await db.execute(edge_stmt)
        level_edges = result.scalars().all()

        for edge in level_edges:
            if edge not in edges:
                edges.append(edge)

            if direction == "UPSTREAM":
                neighbor_id = edge.source_node_id
            else:
                neighbor_id = edge.target_node_id

            if neighbor_id not in visited:
                visited.add(neighbor_id)
                next_level.append(neighbor_id)

        if next_level:
            node_stmt = select(LineageNode).where(
                LineageNode.node_id.in_(next_level),
                LineageNode.status == 1,
            )
            result = await db.execute(node_stmt)
            nodes.extend(result.scalars().all())

        current_level = next_level

    return nodes, edges


@router.get("/search", response_model=Result)
async def search_tables(
    keyword: str = Query(..., min_length=1),
    db: AsyncSession = Depends(get_db),
):
    """Search tables by name (fuzzy match)."""
    stmt = (
        select(LineageNode)
        .where(
            LineageNode.table_name.like(f"%{keyword}%"),
            LineageNode.status == 1,
        )
        .limit(20)
    )
    result = await db.execute(stmt)
    nodes = result.scalars().all()
    return success(data=[LineageNodeOut.model_validate(n) for n in nodes])


@router.get("/systems", response_model=Result)
async def list_systems(db: AsyncSession = Depends(get_db)):
    """List distinct systems that have lineage data."""
    stmt = select(LineageNode.system_code, LineageNode.system_name).where(
        LineageNode.system_code.isnot(None),
        LineageNode.status == 1,
    ).distinct()
    result = await db.execute(stmt)
    systems = [{"code": row[0], "name": row[1]} for row in result]
    return success(data=systems)


@router.get("/clusters", response_model=Result)
async def list_clusters(db: AsyncSession = Depends(get_db)):
    """List distinct clusters that have lineage data."""
    stmt = select(LineageNode.cluster_id, LineageNode.cluster_name).where(
        LineageNode.cluster_id.isnot(None),
        LineageNode.status == 1,
    ).distinct()
    result = await db.execute(stmt)
    clusters = [{"cluster_id": row[0], "cluster_name": row[1]} for row in result if row[0]]
    return success(data=clusters)
