"""Column-level lineage edge model."""

from __future__ import annotations

from sqlalchemy import Column, DateTime, DECIMAL, SmallInteger, String, Text, text as sa_text

from app.models.base import Base


class LineageColumnEdge(Base):
    __tablename__ = "lineage_column_edge"
    __table_args__ = {"comment": "字段级血缘边表"}

    column_edge_id = Column(String(64), primary_key=True)
    edge_id = Column(String(64), nullable=False, comment="所属表级血缘边ID")
    source_column_id = Column(String(64), nullable=False, comment="上游字段ID")
    target_column_id = Column(String(64), nullable=False, comment="下游字段ID")
    transform_expr = Column(String(1024), comment="转换表达式")
    parse_method = Column(String(20), comment="解析方式")
    operator_detail = Column(Text, comment="算子加工详情(JSON): {operator_types, detail, filter_condition}")
    confidence = Column(DECIMAL(3, 2), default=1.00)
    status = Column(SmallInteger, default=1)
    create_time = Column(DateTime, nullable=False, server_default=sa_text("CURRENT_TIMESTAMP"))
    update_time = Column(DateTime, nullable=False, server_default=sa_text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"))
