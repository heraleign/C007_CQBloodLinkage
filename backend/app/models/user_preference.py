from __future__ import annotations

from sqlalchemy import Column, DateTime, String, PrimaryKeyConstraint

from app.models.base import Base


class UserPreference(Base):
    __tablename__ = "user_preference"
    __table_args__ = (
        PrimaryKeyConstraint("user_id", "preference_key"),
        {"comment": "用户偏好设置表"},
    )

    user_id = Column(String(64), nullable=False)
    preference_key = Column(String(64), nullable=False)
    preference_value = Column(String(256))
    update_time = Column(DateTime)
