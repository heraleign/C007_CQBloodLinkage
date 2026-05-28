"""Add is_pk/is_fk to node_column, operator_detail to column_edge.

Revision ID: 003
Revises: 002
Create Date: 2026-05-21
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add constraint fields to lineage_node_column
    op.add_column("lineage_node_column", sa.Column("is_pk", sa.SmallInteger, default=0, comment="是否主键 0-否 1-是"))
    op.add_column("lineage_node_column", sa.Column("is_fk", sa.SmallInteger, default=0, comment="是否外键 0-否 1-是"))

    # Add operator_detail to lineage_column_edge
    op.add_column("lineage_column_edge", sa.Column("operator_detail", sa.Text, nullable=True, comment="算子加工详情(JSON)"))


def downgrade() -> None:
    op.drop_column("lineage_node_column", "is_pk")
    op.drop_column("lineage_node_column", "is_fk")
    op.drop_column("lineage_column_edge", "operator_detail")
