"""Neo4j graph database service for high-performance lineage traversal.

Implements the graph storage model described in §3.5.
"""

from __future__ import annotations

from typing import Any

from neo4j import AsyncGraphDatabase, AsyncSession

from app.core.config import settings


class Neo4jService:
    """Manages Neo4j graph database operations for lineage data."""

    def __init__(self):
        self.driver = None

    async def initialize(self):
        """Initialize Neo4j connection."""
        self.driver = AsyncGraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_user, settings.neo4j_password),
        )

    async def close(self):
        """Close Neo4j connection."""
        if self.driver:
            await self.driver.close()

    async def upsert_node(self, node: dict[str, Any]) -> None:
        """Create or update a lineage node in Neo4j."""
        async with self.driver.session() as session:
            await session.run(
                """
                MERGE (n:LineageNode {nodeId: $node_id})
                SET n.nodeType = $node_type,
                    n.nodeName = $node_name,
                    n.nodeUniqueKey = $node_unique_key,
                    n.systemCode = $system_code,
                    n.systemName = $system_name,
                    n.clusterID = $cluster_id,
                    n.databaseName = $database_name,
                    n.tableName = $table_name,
                    n.tableCnName = $table_cn_name,
                    n.tableRemark = $table_remark
                """,
                **node,
            )

    async def upsert_edge(self, edge: dict[str, Any]) -> None:
        """Create or update a lineage relationship in Neo4j."""
        async with self.driver.session() as session:
            await session.run(
                """
                MATCH (source:LineageNode {nodeId: $source_node_id})
                MATCH (target:LineageNode {nodeId: $target_node_id})
                MERGE (source)-[r:LINEAGE_TO {edgeId: $edge_id}]->(target)
                SET r.lineageStage = $lineage_stage,
                    r.lineageType = $lineage_type,
                    r.sourceProgram = $source_program,
                    r.parseMethod = $parse_method,
                    r.confidence = $confidence
                """,
                **edge,
            )

    async def query_lineage(
        self,
        node_id: str,
        direction: str = "BOTH",
        max_depth: int = 3,
    ) -> dict[str, Any]:
        """Traverse lineage graph from a starting node."""
        async with self.driver.session() as session:
            if direction == "UPSTREAM":
                result = await session.run(
                    """
                    MATCH path = (source:LineageNode)-[:LINEAGE_TO*1..$depth]->(center:LineageNode {nodeId: $node_id})
                    UNWIND nodes(path) AS n
                    RETURN DISTINCT n.nodeId AS nodeId, labels(n) AS labels, properties(n) AS props
                    """,
                    node_id=node_id,
                    depth=max_depth,
                )
            elif direction == "DOWNSTREAM":
                result = await session.run(
                    """
                    MATCH path = (center:LineageNode {nodeId: $node_id})-[:LINEAGE_TO*1..$depth]->(target:LineageNode)
                    UNWIND nodes(path) AS n
                    RETURN DISTINCT n.nodeId AS nodeId, labels(n) AS labels, properties(n) AS props
                    """,
                    node_id=node_id,
                    depth=max_depth,
                )
            else:
                result = await session.run(
                    """
                    MATCH path = (start:LineageNode)-[:LINEAGE_TO*1..$depth]-(center:LineageNode {nodeId: $node_id})
                    UNWIND nodes(path) AS n
                    RETURN DISTINCT n.nodeId AS nodeId, labels(n) AS labels, properties(n) AS props
                    """,
                    node_id=node_id,
                    depth=max_depth,
                )

            records = await result.fetch()
            nodes = []
            for record in records:
                nodes.append(record.data())

            return {"nodes": nodes, "total": len(nodes)}

    async def delete_node(self, node_id: str) -> None:
        """Delete a node and its relationships."""
        async with self.driver.session() as session:
            await session.run(
                "MATCH (n:LineageNode {nodeId: $node_id}) DETACH DELETE n",
                node_id=node_id,
            )

    async def sync_from_queue(self) -> dict[str, Any]:
        """Sync pending lineage data from MySQL to Neo4j.

        In production, this reads from a sync queue/table.
        For now, returns status.
        """
        return {"status": "synced", "nodes_synced": 0, "edges_synced": 0}
