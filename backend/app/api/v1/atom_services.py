"""Atom API services — lineage capabilities exposed as REST APIs."""

from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.response import Result, success
from app.models.lineage_edge import LineageEdge
from app.models.lineage_node import LineageNode
from app.schemas.lineage import (
    AtomParseScriptRequest,
    AtomParseSQLRequest,
    AtomQueryLineageRequest,
    AtomSaveLineageRequest,
    LineageEdgeOut,
    LineageNodeOut,
)

router = APIRouter(prefix="/atom", tags=["原子能力"])


@router.post("/parse-table-lineage", response_model=Result)
async def atom_parse_table_lineage(body: AtomParseSQLRequest):
    """ATOM_001: Parse table-level lineage from SQL text."""
    from app.services.parsing.sql_parser import SQLParser

    parser = SQLParser(dialect=body.sql_dialect)
    result = parser.parse_table_lineage(body.sql)
    return success(data=result)


@router.post("/parse-column-lineage", response_model=Result)
async def atom_parse_column_lineage(body: AtomParseSQLRequest):
    """ATOM_002: Parse column-level lineage from SQL text."""
    from app.services.parsing.sql_parser import SQLParser

    parser = SQLParser(dialect=body.sql_dialect)
    result = parser.parse_column_lineage(body.sql)
    return success(data=result)


@router.post("/parse-script-lineage", response_model=Result)
async def atom_parse_script_lineage(body: AtomParseScriptRequest):
    """ATOM_003: Parse lineage from Shell script."""
    from app.services.parsing.dispatcher import ScriptParseDispatcher

    dispatcher = ScriptParseDispatcher()
    result = await dispatcher.parse(
        script_content=body.script_content,
        vendor_code=body.vendor_code,
        script_type=body.script_type,
        variable_map=body.variable_map or {},
        enable_ai=body.enable_ai,
    )
    return success(data=result)


@router.post("/save-lineage", response_model=Result)
async def atom_save_lineage(body: AtomSaveLineageRequest, db: AsyncSession = Depends(get_db)):
    """ATOM_004: Save lineage data."""
    node_id_map = {}
    saved_nodes = 0
    saved_edges = 0

    for node_data in body.nodes:
        node_id = str(uuid.uuid4())
        node = LineageNode(
            node_id=node_id,
            **node_data.model_dump(exclude_none=True),
        )
        now = datetime.now()
        node.create_time = now
        node.update_time = now
        db.add(node)
        node_id_map[id(node_data)] = node_id
        saved_nodes += 1

    for edge_data in body.edges:
        edge_id = str(uuid.uuid4())
        edge = LineageEdge(
            edge_id=edge_id,
            **edge_data.model_dump(exclude_none=True),
        )
        now = datetime.now()
        edge.create_time = now
        edge.update_time = now
        db.add(edge)
        saved_edges += 1

    await db.flush()
    return success(data={"saved_nodes": saved_nodes, "saved_edges": saved_edges})


@router.post("/query-lineage", response_model=Result)
async def atom_query_lineage(body: AtomQueryLineageRequest, db: AsyncSession = Depends(get_db)):
    """ATOM_005: Query lineage for a table."""
    from sqlalchemy import select

    from app.models.lineage_edge import LineageEdge
    from app.models.lineage_node import LineageNode

    stmt = select(LineageNode).where(
        LineageNode.table_name == body.table_name,
        LineageNode.status == 1,
    )
    if body.cluster_id:
        stmt = stmt.where(LineageNode.cluster_id == body.cluster_id)
    result = await db.execute(stmt)
    center = result.scalar_one_or_none()
    if not center:
        from app.core.response import fail
        return fail(code=404, message=f"Table {body.table_name} not found")

    # Simple BFS to get upstream/downstream
    upstream_nodes = []
    downstream_nodes = []
    edges_result = []

    # Get all edges connected to the center node
    stmt_edges = select(LineageEdge).where(
        (LineageEdge.source_node_id == center.node_id) | (LineageEdge.target_node_id == center.node_id),
        LineageEdge.status == 1,
    )
    result_edges = await db.execute(stmt_edges)
    for edge in result_edges.scalars().all():
        edges_result.append(edge)
        if edge.source_node_id == center.node_id:
            n_stmt = select(LineageNode).where(LineageNode.node_id == edge.target_node_id)
            n_result = await db.execute(n_stmt)
            n = n_result.scalar_one_or_none()
            if n:
                downstream_nodes.append(n)
        if edge.target_node_id == center.node_id:
            n_stmt = select(LineageNode).where(LineageNode.node_id == edge.source_node_id)
            n_result = await db.execute(n_stmt)
            n = n_result.scalar_one_or_none()
            if n:
                upstream_nodes.append(n)

    return success(
        data={
            "centerNode": LineageNodeOut.model_validate(center),
            "upstreamNodes": [LineageNodeOut.model_validate(n) for n in upstream_nodes],
            "downstreamNodes": [LineageNodeOut.model_validate(n) for n in downstream_nodes],
            "edges": [LineageEdgeOut.model_validate(e) for e in edges_result],
            "totalNodes": 1 + len(upstream_nodes) + len(downstream_nodes),
            "totalEdges": len(edges_result),
        }
    )
