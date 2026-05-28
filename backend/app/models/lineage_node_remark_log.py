from __future__ import annotations

from sqlalchemy import Column, DateTime, String, Text

from app.models.base import Base


class LineageNodeRemarkLog(Base):
    __tablename__ = "lineage_node_remark_log"
    __table_args__ = {"comment": "血缘节点备注修改日志"}

    log_id = Column(String(64), primary_key=True)
    node_id = Column(String(64), nullable=False)
    field_name = Column(String(64), nullable=False, comment="修改字段")
    old_value = Column(String(1024))
    new_value = Column(String(1024))
    operator = Column(String(64), nullable=False)
    operate_time = Column(DateTime, nullable=False)
