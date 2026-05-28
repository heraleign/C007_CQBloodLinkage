"""AI call configuration model — Capability 9 (§12.4.1)."""

from __future__ import annotations

from sqlalchemy import Column, DateTime, String, Text, Integer, SmallInteger, DECIMAL, func

from app.models.base import Base


class AiCallConfig(Base):
    __tablename__ = "ai_call_config"
    __table_args__ = {"comment": "AI调用配置表"}

    config_id = Column(String(64), primary_key=True, comment="配置唯一ID")
    ai_capability = Column(String(32), nullable=False, comment="SQL_EXTRACT / LINEAGE_PARSE")
    model_name = Column(String(64), nullable=False, comment="模型名称")
    api_endpoint = Column(String(256), nullable=False, comment="API端点")
    api_key = Column(String(256), default="", comment="API密钥")
    max_tokens = Column(Integer, default=4096, comment="最大Token数")
    temperature = Column(DECIMAL(2, 1), default=0.1, comment="低温度确保确定性输出")
    timeout_ms = Column(Integer, default=30000, comment="超时时间(毫秒)")
    retry_count = Column(Integer, default=2, comment="重试次数")
    enabled = Column(SmallInteger, default=1, comment="1启用 0禁用")
    create_time = Column(DateTime, server_default=func.now(), comment="创建时间")
    update_time = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")
