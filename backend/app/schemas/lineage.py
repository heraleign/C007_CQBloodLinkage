"""Pydantic schemas for lineage nodes, edges, and queries."""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


# ---------- Node ----------
class LineageNodeCreate(BaseModel):
    node_type: str
    node_name: str
    node_unique_key: str
    system_code: Optional[str] = None
    system_name: Optional[str] = None
    cluster_id: Optional[str] = None
    cluster_name: Optional[str] = None
    database_name: Optional[str] = None
    table_name: Optional[str] = None
    table_cn_name: Optional[str] = None
    table_remark: Optional[str] = None
    server_ip: Optional[str] = None
    server_port: Optional[str] = None
    protocol: Optional[str] = None
    source_type: Optional[str] = "AUTO"


class LineageNodeUpdate(BaseModel):
    node_name: Optional[str] = None
    table_cn_name: Optional[str] = None
    table_remark: Optional[str] = None
    system_code: Optional[str] = None
    system_name: Optional[str] = None


class LineageNodeOut(BaseModel):
    node_id: str
    node_type: str
    node_name: str
    node_unique_key: str
    system_code: Optional[str] = None
    system_name: Optional[str] = None
    cluster_id: Optional[str] = None
    cluster_name: Optional[str] = None
    database_name: Optional[str] = None
    table_name: Optional[str] = None
    table_cn_name: Optional[str] = None
    table_remark: Optional[str] = None
    status: int = 1
    create_time: Optional[datetime] = None
    update_time: Optional[datetime] = None

    class Config:
        from_attributes = True


# ---------- Node Column ----------
class LineageNodeColumnOut(BaseModel):
    column_id: str
    node_id: str
    column_name: str
    column_cn_name: Optional[str] = None
    column_type: Optional[str] = None
    column_remark: Optional[str] = None
    column_order: Optional[int] = None
    is_pk: Optional[int] = 0
    is_fk: Optional[int] = 0

    class Config:
        from_attributes = True


# ---------- Edge ----------
class LineageEdgeCreate(BaseModel):
    source_node_id: str
    target_node_id: str
    lineage_stage: str = "INGEST"  # INGEST / PROCESS / OUTPUT
    lineage_type: str = "TABLE"  # TABLE / COLUMN / OPERATOR
    source_program: Optional[str] = None
    source_system: Optional[str] = None
    parse_method: Optional[str] = "API"
    collect_method: Optional[str] = None
    collect_config_id: Optional[str] = None
    confidence: Optional[float] = 1.0


class LineageEdgeOut(BaseModel):
    edge_id: str
    source_node_id: str
    target_node_id: str
    lineage_stage: str
    lineage_type: str
    source_program: Optional[str] = None
    parse_method: Optional[str] = None
    collect_method: Optional[str] = None
    confidence: Optional[float] = None
    status: int = 1
    create_time: Optional[datetime] = None

    class Config:
        from_attributes = True


# ---------- Column Edge ----------
class LineageColumnEdgeOut(BaseModel):
    column_edge_id: str
    edge_id: str
    source_column_id: str
    target_column_id: str
    transform_expr: Optional[str] = None
    parse_method: Optional[str] = None
    operator_detail: Optional[str] = None
    confidence: Optional[float] = None

    class Config:
        from_attributes = True


# ---------- Query ----------
class LineageQueryRequest(BaseModel):
    table_name: str
    system_code: Optional[str] = None
    cluster_id: Optional[str] = None
    direction: str = "BOTH"  # UPSTREAM / DOWNSTREAM / BOTH
    depth: int = 3
    lineage_type: str = "TABLE"  # TABLE / COLUMN / OPERATOR / ALL
    include_column_lineage: bool = False


class LineageGraphOut(BaseModel):
    center_node: Optional[LineageNodeOut] = None
    upstream_nodes: List[LineageNodeOut] = Field(default_factory=list)
    downstream_nodes: List[LineageNodeOut] = Field(default_factory=list)
    edges: List[LineageEdgeOut] = Field(default_factory=list)
    column_edges: List[LineageColumnEdgeOut] = Field(default_factory=list)
    node_columns: List[LineageNodeColumnOut] = Field(default_factory=list, description="All column definitions for all involved nodes")
    total_nodes: int = 0
    total_edges: int = 0


# ---------- Remark ----------
class RemarkUpdateRequest(BaseModel):
    node_id: str
    table_remark: Optional[str] = None
    columns: Optional[List[dict]] = None  # [{column_id, column_remark}]


# ---------- Export ----------
class LineageExportRequest(BaseModel):
    table_names: List[str]
    direction: str = "BOTH"
    depth: int = 3
    lineage_type: str = "ALL"  # TABLE / COLUMN / OPERATOR / ALL
    export_format: str = "EXCEL"  # EXCEL / WORD / PDF
    sync_to_doc_center: bool = False
    include_columns: bool = True


# ---------- Atom API ----------
class AtomParseSQLRequest(BaseModel):
    sql: str
    sql_dialect: str = "SparkSQL"
    cluster_id: Optional[str] = None
    enable_ai: bool = True


class AtomParseScriptRequest(BaseModel):
    script_content: str
    vendor_code: str = "DIKE"
    script_type: str = "SHELL_SPARK"
    variable_map: Optional[dict] = None
    enable_ai: bool = True


class AtomSaveLineageRequest(BaseModel):
    source_system: str
    nodes: List[LineageNodeCreate]
    edges: List[LineageEdgeCreate]


class AtomQueryLineageRequest(BaseModel):
    table_name: str
    cluster_id: Optional[str] = None
    direction: str = "BOTH"
    depth: int = 5
    lineage_type: str = "TABLE"  # TABLE / COLUMN / OPERATOR / ALL
    include_column_lineage: bool = False
