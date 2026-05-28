"""Ingest lineage sync task — Capability 1 (§4.1).

Pulls data from the data aggregation system APIs to auto-generate
ingest-stage lineage nodes and edges.
"""

from __future__ import annotations

import uuid
from datetime import datetime

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.lineage_edge import LineageEdge
from app.models.lineage_node import LineageNode


async def run_ingest_sync(db: AsyncSession):
    """Execute ingest lineage sync.

    In production this calls the 4 data aggregation APIs:
      - /api/lineage/file-collect
      - /api/lineage/db-collect
      - /api/lineage/kafka-collect
      - /api/lineage/table-structure

    For development, this is a stub that demonstrates the flow.
    """
    results = {
        "file_collect": {"processed": 0, "nodes": 0, "edges": 0},
        "db_collect": {"processed": 0, "nodes": 0, "edges": 0},
        "kafka_collect": {"processed": 0, "nodes": 0, "edges": 0},
        "table_structure": {"processed": 0},
    }

    # In production, call actual APIs here
    # For now, this is a no-op that can be tested

    return results


async def _process_file_collect(record: dict, db: AsyncSession) -> None:
    """Process a single file collection record.

    Generates: EXT_FILE -> LAKE_TABLE lineage edge.
    """
    from app.core.config import settings

    # Source node (EXT_FILE)
    source_key = f"{record.get('protocol', 'sftp')}://{record.get('serverIP')}:{record.get('serverPort')}{record.get('filePath')}/{record.get('fileNameFormat', '')}"

    stmt = select(LineageNode).where(LineageNode.node_unique_key == source_key)
    result = await db.execute(stmt)
    source_node = result.scalar_one_or_none()

    if not source_node:
        source_node = LineageNode(
            node_id=str(uuid.uuid4()),
            node_type="EXT_FILE",
            node_name=record.get("tableName", "unknown_file"),
            node_unique_key=source_key,
            system_name=record.get("systemName"),
            table_name=record.get("tableName"),
            server_ip=record.get("serverIP"),
            server_port=str(record.get("serverPort", "")),
            protocol=record.get("protocol", "sftp"),
            source_type="AUTO",
            create_time=datetime.now(),
            update_time=datetime.now(),
        )
        db.add(source_node)

    # Target node (LAKE_TABLE)
    target_key = f"{settings.system_code}::default::{record.get('tableName', 'unknown')}"
    stmt = select(LineageNode).where(LineageNode.node_unique_key == target_key)
    result = await db.execute(stmt)
    target_node = result.scalar_one_or_none()

    if not target_node:
        target_node = LineageNode(
            node_id=str(uuid.uuid4()),
            node_type="LAKE_TABLE",
            node_name=record.get("tableName", "unknown"),
            node_unique_key=target_key,
            system_name=record.get("systemName"),
            table_name=record.get("tableName"),
            cluster_id=settings.system_code,
            database_name="default",
            source_type="AUTO",
            create_time=datetime.now(),
            update_time=datetime.now(),
        )
        db.add(target_node)

    # Edge
    edge_key = f"{source_node.node_id}|{target_node.node_id}|INGEST"
    stmt = select(LineageEdge).where(
        LineageEdge.source_node_id == source_node.node_id,
        LineageEdge.target_node_id == target_node.node_id,
        LineageEdge.lineage_stage == "INGEST",
    )
    result = await db.execute(stmt)
    if not result.scalar_one_or_none():
        edge = LineageEdge(
            edge_id=str(uuid.uuid4()),
            source_node_id=source_node.node_id,
            target_node_id=target_node.node_id,
            lineage_stage="INGEST",
            lineage_type="TABLE",
            collect_method="FILE",
            collect_config_id=record.get("id"),
            parse_method="API",
            confidence=1.0,
            create_time=datetime.now(),
            update_time=datetime.now(),
        )
        db.add(edge)
