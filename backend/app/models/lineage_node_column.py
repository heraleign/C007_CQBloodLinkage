"""Column-level metadata for lineage nodes."""

from __future__ import annotations

from sqlalchemy import Column, DateTime, Integer, String, Text, SmallInteger
from sqlalchemy import text as sa_text

from app.models.base import Base


class LineageNodeColumn(Base):
    __tablename__ = "lineage_node_column"
    __table_args__ = {"comment": "血缘节点字段表"}

    column_id = Column(String(64), primary_key=True, comment="字段唯一ID")
    node_id = Column(String(64), nullable=False, comment="所属节点ID")
    column_name = Column(String(256), nullable=False, comment="字段名")
    column_cn_name = Column(String(256), comment="字段中文名")
    column_type = Column(String(64), comment="字段类型")
    column_remark = Column(Text, comment="字段备注")
    column_order = Column(Integer, comment="字段顺序")
    is_pk = Column(SmallInteger, default=0, comment="是否主键 0-否 1-是")
    is_fk = Column(SmallInteger, default=0, comment="是否外键 0-否 1-是")

    status = Column(SmallInteger, default=1)
    create_time = Column(DateTime, nullable=False, server_default=sa_text("CURRENT_TIMESTAMP"))
    update_time = Column(DateTime, nullable=False, server_default=sa_text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"))
