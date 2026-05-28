from __future__ import annotations

from sqlalchemy import Column, DateTime, String, SmallInteger

from app.models.base import Base


class LineagePermission(Base):
    __tablename__ = "lineage_permission"
    __table_args__ = {"comment": "血缘权限表"}

    perm_id = Column(String(64), primary_key=True)
    user_id = Column(String(64), nullable=False)
    perm_type = Column(String(32), nullable=False, comment="REMARK_EDIT/REMARK_VIEW/LINEAGE_ADMIN")
    scope_type = Column(String(20), comment="ALL/SYSTEM/CLUSTER")
    scope_value = Column(String(64), comment="范围值")
    granted_by = Column(String(64), nullable=False)
    granted_time = Column(DateTime, nullable=False)
    expire_time = Column(DateTime, comment="过期时间，NULL为永久")
    status = Column(SmallInteger, default=1)
