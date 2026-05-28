"""Table-level lineage edge model."""

from __future__ import annotations

from sqlalchemy import Column, DateTime, DECIMAL, String, SmallInteger, text as sa_text

from app.models.base import Base


class LineageEdge(Base):
    __tablename__ = "lineage_edge"
    __table_args__ = {"comment": "血缘边表（表级）"}

    edge_id = Column(String(64), primary_key=True, comment="边唯一ID")
    source_node_id = Column(String(64), nullable=False, comment="上游节点ID")
    target_node_id = Column(String(64), nullable=False, comment="下游节点ID")

    lineage_stage = Column(String(20), nullable=False, comment="阶段：INGEST/PROCESS/OUTPUT")
    lineage_type = Column(String(20), nullable=False, comment="类型：TABLE/COLUMN/OPERATOR")

    source_program = Column(String(256), comment="产生该血缘的程序/脚本")
    source_system = Column(String(64), comment="来源系统")
    parse_method = Column(String(20), comment="解析方式：AST/AI/MANUAL/API")

    collect_method = Column(String(20), comment="采集方式：FILE/DB/KAFKA")
    collect_config_id = Column(String(64), comment="采集配置ID")

    confidence = Column(DECIMAL(3, 2), default=1.00, comment="置信度 0-1")
    status = Column(SmallInteger, default=1)
    create_time = Column(DateTime, nullable=False, server_default=sa_text("CURRENT_TIMESTAMP"))
    update_time = Column(DateTime, nullable=False, server_default=sa_text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"))
