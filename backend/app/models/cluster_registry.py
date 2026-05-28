from __future__ import annotations

from sqlalchemy import Column, DateTime, String, Text, SmallInteger
from sqlalchemy import text as sa_text

from app.models.base import Base


class ClusterRegistry(Base):
    __tablename__ = "cluster_registry"
    __table_args__ = {"comment": "集群注册表"}

    cluster_id = Column(String(64), primary_key=True)
    cluster_name = Column(String(128), nullable=False)
    cluster_type = Column(String(20), nullable=False, comment="TDP/CDH/自建等")
    cluster_version = Column(String(32))
    api_endpoint = Column(String(256))
    auth_config = Column(Text, comment="认证配置JSON")
    status = Column(SmallInteger, default=1)
    create_time = Column(DateTime, server_default=sa_text("CURRENT_TIMESTAMP"))
