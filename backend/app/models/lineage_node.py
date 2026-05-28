"""Lineage node model — core entity for data lineage graph."""

from __future__ import annotations

from sqlalchemy import Column, DateTime, String, Text, SmallInteger
from sqlalchemy import text as sa_text

from app.models.base import Base


class LineageNode(Base):
    __tablename__ = "lineage_node"
    __table_args__ = {"comment": "血缘节点表"}

    node_id = Column(String(64), primary_key=True, comment="节点唯一ID")
    node_type = Column(String(20), nullable=False, comment="节点类型编码")
    node_name = Column(String(256), nullable=False, comment="节点显示名称")
    node_unique_key = Column(String(512), nullable=False, comment="跨集群唯一标识")

    system_code = Column(String(64), comment="归属系统编码")
    system_name = Column(String(128), comment="归属系统名称")
    cluster_id = Column(String(64), comment="集群ID")
    cluster_name = Column(String(128), comment="集群名称")
    database_name = Column(String(128), comment="数据库/Schema名称")

    table_name = Column(String(256), comment="表名/文件名/Topic名")
    table_cn_name = Column(String(256), comment="表中文名")
    table_remark = Column(Text, comment="表备注")

    server_ip = Column(String(64), comment="服务器IP")
    server_port = Column(String(10), comment="端口")
    protocol = Column(String(20), comment="协议类型")

    source_type = Column(String(20), comment="来源：AUTO/MANUAL/IMPORT")
    status = Column(SmallInteger, default=1, comment="1有效 0无效")
    create_time = Column(DateTime, nullable=False, server_default=sa_text("CURRENT_TIMESTAMP"))
    update_time = Column(DateTime, nullable=False, server_default=sa_text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"))
    create_user = Column(String(64))
    update_user = Column(String(64))
