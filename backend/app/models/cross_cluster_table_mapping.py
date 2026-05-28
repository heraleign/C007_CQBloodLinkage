from __future__ import annotations

from sqlalchemy import Column, DateTime, String, SmallInteger, text as sa_text

from app.models.base import Base


class CrossClusterTableMapping(Base):
    __tablename__ = "cross_cluster_table_mapping"
    __table_args__ = {"comment": "跨集群表映射关系表"}

    mapping_id = Column(String(64), primary_key=True)
    source_cluster = Column(String(64), nullable=False)
    source_database = Column(String(128), nullable=False)
    source_table = Column(String(256), nullable=False)
    target_cluster = Column(String(64), nullable=False)
    target_database = Column(String(128), nullable=False)
    target_table = Column(String(256), nullable=False)
    sync_type = Column(String(20), comment="DISTCP/SQOOP/SPARK/MANUAL")
    status = Column(SmallInteger, default=1)
    create_time = Column(DateTime, server_default=sa_text("CURRENT_TIMESTAMP"))
