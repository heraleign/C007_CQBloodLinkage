"""Create ai_call_config table for LLM configuration.

Revision ID: 002
Revises: 001
Create Date: 2026-05-18
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "ai_call_config",
        sa.Column("config_id", sa.String(64), primary_key=True),
        sa.Column("ai_capability", sa.String(32), nullable=False, comment="SQL_EXTRACT / LINEAGE_PARSE"),
        sa.Column("model_name", sa.String(64), nullable=False, comment="模型名称"),
        sa.Column("api_endpoint", sa.String(256), nullable=False, comment="API端点"),
        sa.Column("api_key", sa.String(256), default="", comment="API密钥"),
        sa.Column("max_tokens", sa.Integer, default=4096, comment="最大Token数"),
        sa.Column("temperature", sa.DECIMAL(2, 1), default=0.1, comment="温度参数"),
        sa.Column("timeout_ms", sa.Integer, default=30000, comment="超时毫秒"),
        sa.Column("retry_count", sa.Integer, default=2, comment="重试次数"),
        sa.Column("enabled", sa.SmallInteger, default=1, comment="1启用 0禁用"),
        sa.Column("create_time", sa.DateTime, server_default=sa.func.now(), comment="创建时间"),
        sa.Column("update_time", sa.DateTime, server_default=sa.func.now(), comment="更新时间"),
        comment="AI调用配置表",
    )


def downgrade() -> None:
    op.drop_table("ai_call_config")
