"""Initial schema — create all 12 lineage tables.

Revision ID: 001
Revises:
Create Date: 2026-05-18
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- lineage_node ---
    op.create_table(
        "lineage_node",
        sa.Column("node_id", sa.String(64), primary_key=True),
        sa.Column("node_type", sa.String(20), nullable=False),
        sa.Column("node_name", sa.String(256), nullable=False),
        sa.Column("node_unique_key", sa.String(512), nullable=False),
        sa.Column("system_code", sa.String(64)),
        sa.Column("system_name", sa.String(128)),
        sa.Column("cluster_id", sa.String(64)),
        sa.Column("cluster_name", sa.String(128)),
        sa.Column("database_name", sa.String(128)),
        sa.Column("table_name", sa.String(256)),
        sa.Column("table_cn_name", sa.String(256)),
        sa.Column("table_remark", sa.Text),
        sa.Column("server_ip", sa.String(64)),
        sa.Column("server_port", sa.String(10)),
        sa.Column("protocol", sa.String(20)),
        sa.Column("source_type", sa.String(20)),
        sa.Column("status", sa.SmallInteger, default=1),
        sa.Column("create_time", sa.DateTime, server_default=sa.func.now()),
        sa.Column("update_time", sa.DateTime, server_default=sa.func.now()),
        sa.Column("create_user", sa.String(64)),
        sa.Column("update_user", sa.String(64)),
        sa.UniqueConstraint("node_unique_key"),
        comment="血缘节点表",
    )

    # --- lineage_node_column ---
    op.create_table(
        "lineage_node_column",
        sa.Column("column_id", sa.String(64), primary_key=True),
        sa.Column("node_id", sa.String(64), nullable=False),
        sa.Column("column_name", sa.String(256), nullable=False),
        sa.Column("column_cn_name", sa.String(256)),
        sa.Column("column_type", sa.String(64)),
        sa.Column("column_remark", sa.Text),
        sa.Column("column_order", sa.Integer),
        sa.Column("status", sa.SmallInteger, default=1),
        sa.Column("create_time", sa.DateTime, server_default=sa.func.now()),
        sa.Column("update_time", sa.DateTime, server_default=sa.func.now()),
        comment="血缘节点字段表",
    )
    op.create_index("idx_node_column_node_id", "lineage_node_column", ["node_id"])

    # --- lineage_edge ---
    op.create_table(
        "lineage_edge",
        sa.Column("edge_id", sa.String(64), primary_key=True),
        sa.Column("source_node_id", sa.String(64), nullable=False),
        sa.Column("target_node_id", sa.String(64), nullable=False),
        sa.Column("lineage_stage", sa.String(20), nullable=False),
        sa.Column("lineage_type", sa.String(20), nullable=False),
        sa.Column("source_program", sa.String(256)),
        sa.Column("source_system", sa.String(64)),
        sa.Column("parse_method", sa.String(20)),
        sa.Column("collect_method", sa.String(20)),
        sa.Column("collect_config_id", sa.String(64)),
        sa.Column("confidence", sa.DECIMAL(3, 2), default=1.00),
        sa.Column("status", sa.SmallInteger, default=1),
        sa.Column("create_time", sa.DateTime, server_default=sa.func.now()),
        sa.Column("update_time", sa.DateTime, server_default=sa.func.now()),
        comment="血缘边表（表级/字段级/算子级）",
    )
    op.create_index("idx_edge_source", "lineage_edge", ["source_node_id"])
    op.create_index("idx_edge_target", "lineage_edge", ["target_node_id"])
    op.create_index("idx_edge_stage", "lineage_edge", ["lineage_stage"])

    # --- lineage_column_edge ---
    op.create_table(
        "lineage_column_edge",
        sa.Column("column_edge_id", sa.String(64), primary_key=True),
        sa.Column("edge_id", sa.String(64), nullable=False),
        sa.Column("source_column_id", sa.String(64), nullable=False),
        sa.Column("target_column_id", sa.String(64), nullable=False),
        sa.Column("transform_expr", sa.String(1024)),
        sa.Column("parse_method", sa.String(20)),
        sa.Column("confidence", sa.DECIMAL(3, 2), default=1.00),
        sa.Column("status", sa.SmallInteger, default=1),
        sa.Column("create_time", sa.DateTime, server_default=sa.func.now()),
        sa.Column("update_time", sa.DateTime, server_default=sa.func.now()),
        comment="字段级血缘边表",
    )
    op.create_index("idx_cedge_edge", "lineage_column_edge", ["edge_id"])
    op.create_index("idx_cedge_source", "lineage_column_edge", ["source_column_id"])
    op.create_index("idx_cedge_target", "lineage_column_edge", ["target_column_id"])

    # --- lineage_node_remark_log ---
    op.create_table(
        "lineage_node_remark_log",
        sa.Column("log_id", sa.String(64), primary_key=True),
        sa.Column("node_id", sa.String(64), nullable=False),
        sa.Column("field_name", sa.String(64), nullable=False),
        sa.Column("old_value", sa.String(1024)),
        sa.Column("new_value", sa.String(1024)),
        sa.Column("operator", sa.String(64), nullable=False),
        sa.Column("operate_time", sa.DateTime, nullable=False),
        comment="血缘节点备注修改日志",
    )

    # --- cluster_registry ---
    op.create_table(
        "cluster_registry",
        sa.Column("cluster_id", sa.String(64), primary_key=True),
        sa.Column("cluster_name", sa.String(128), nullable=False),
        sa.Column("cluster_type", sa.String(20), nullable=False),
        sa.Column("cluster_version", sa.String(32)),
        sa.Column("api_endpoint", sa.String(256)),
        sa.Column("auth_config", sa.Text),
        sa.Column("status", sa.SmallInteger, default=1),
        sa.Column("create_time", sa.DateTime, server_default=sa.func.now()),
        comment="集群注册表",
    )

    # --- cross_cluster_table_mapping ---
    op.create_table(
        "cross_cluster_table_mapping",
        sa.Column("mapping_id", sa.String(64), primary_key=True),
        sa.Column("source_cluster", sa.String(64), nullable=False),
        sa.Column("source_database", sa.String(128), nullable=False),
        sa.Column("source_table", sa.String(256), nullable=False),
        sa.Column("target_cluster", sa.String(64), nullable=False),
        sa.Column("target_database", sa.String(128), nullable=False),
        sa.Column("target_table", sa.String(256), nullable=False),
        sa.Column("sync_type", sa.String(20)),
        sa.Column("status", sa.SmallInteger, default=1),
        sa.Column("create_time", sa.DateTime, server_default=sa.func.now()),
        comment="跨集群表映射关系表",
    )

    # --- script_parse_config ---
    op.create_table(
        "script_parse_config",
        sa.Column("config_id", sa.String(64), primary_key=True),
        sa.Column("vendor_code", sa.String(32), nullable=False),
        sa.Column("script_type", sa.String(32), nullable=False),
        sa.Column("adapter_class", sa.String(256), nullable=False),
        sa.Column("sql_dialect", sa.String(20), nullable=False),
        sa.Column("exec_engine", sa.String(20), nullable=False),
        sa.Column("exec_command", sa.String(64)),
        sa.Column("variable_pattern", sa.String(256)),
        sa.Column("script_base_path", sa.String(512)),
        sa.Column("has_nested_call", sa.SmallInteger, default=0),
        sa.Column("log_parse_enabled", sa.SmallInteger, default=0),
        sa.Column("log_path_pattern", sa.String(512)),
        sa.Column("status", sa.SmallInteger, default=1),
        sa.Column("create_time", sa.DateTime, server_default=sa.func.now()),
        comment="脚本解析配置表",
    )

    # --- script_parse_result ---
    op.create_table(
        "script_parse_result",
        sa.Column("result_id", sa.String(64), primary_key=True),
        sa.Column("script_path", sa.String(512), nullable=False),
        sa.Column("vendor_code", sa.String(32), nullable=False),
        sa.Column("script_type", sa.String(32), nullable=False),
        sa.Column("parse_status", sa.String(20), nullable=False),
        sa.Column("sql_count", sa.Integer, default=0),
        sa.Column("table_lineage_count", sa.Integer, default=0),
        sa.Column("column_lineage_count", sa.Integer, default=0),
        sa.Column("ast_parsed_count", sa.Integer, default=0),
        sa.Column("ai_supplement_count", sa.Integer, default=0),
        sa.Column("manual_count", sa.Integer, default=0),
        sa.Column("error_message", sa.Text),
        sa.Column("unparsed_sqls", sa.Text),
        sa.Column("parse_time", sa.DateTime, nullable=False),
        sa.Column("parse_duration_ms", sa.BigInteger),
        comment="脚本解析结果表",
    )

    # --- log_collect_config ---
    op.create_table(
        "log_collect_config",
        sa.Column("config_id", sa.String(64), primary_key=True),
        sa.Column("vendor_code", sa.String(32), nullable=False),
        sa.Column("log_source_type", sa.String(20), nullable=False),
        sa.Column("log_path_pattern", sa.String(512)),
        sa.Column("log_file_encoding", sa.String(20), default="UTF-8"),
        sa.Column("log_date_format", sa.String(64)),
        sa.Column("sql_start_marker", sa.String(256)),
        sa.Column("sql_end_marker", sa.String(256)),
        sa.Column("task_id_pattern", sa.String(256)),
        sa.Column("filter_patterns", sa.Text),
        sa.Column("collect_schedule", sa.String(32), default="0 30 2 * * ?"),
        sa.Column("enabled", sa.SmallInteger, default=1),
        sa.Column("create_time", sa.DateTime, server_default=sa.func.now()),
        comment="日志采集配置表",
    )

    # --- lineage_permission ---
    op.create_table(
        "lineage_permission",
        sa.Column("perm_id", sa.String(64), primary_key=True),
        sa.Column("user_id", sa.String(64), nullable=False),
        sa.Column("perm_type", sa.String(32), nullable=False),
        sa.Column("scope_type", sa.String(20)),
        sa.Column("scope_value", sa.String(64)),
        sa.Column("granted_by", sa.String(64), nullable=False),
        sa.Column("granted_time", sa.DateTime, nullable=False),
        sa.Column("expire_time", sa.DateTime),
        sa.Column("status", sa.SmallInteger, default=1),
        comment="血缘权限表",
    )

    # --- user_preference ---
    op.create_table(
        "user_preference",
        sa.Column("user_id", sa.String(64), nullable=False),
        sa.Column("preference_key", sa.String(64), nullable=False),
        sa.Column("preference_value", sa.String(256)),
        sa.Column("update_time", sa.DateTime),
        sa.PrimaryKeyConstraint("user_id", "preference_key"),
        comment="用户偏好设置表",
    )

    # Seed data: script_parse_config for DIKE and STQ
    op.execute(
        """
        INSERT INTO script_parse_config (config_id, vendor_code, script_type, adapter_class, sql_dialect, exec_engine, exec_command, variable_pattern, script_base_path, has_nested_call, log_parse_enabled, log_path_pattern, status, create_time) VALUES
        ('CFG_DIKE_01', 'DIKE', 'SHELL_SPARK', 'com.lineage.adapter.DikeSparkAdapter', 'SparkSQL', 'Spark', 'spark-sql', '\\\\$\\\\{[^}]+\\\\}', '/analysis_cloud/', 1, 0, NULL, 1, NOW()),
        ('CFG_DIKE_02', 'DIKE', 'SHELL_HBASE', 'com.lineage.adapter.DikeHBaseAdapter', 'HiveQL', 'Hive', 'beeline', '\\\\$\\\\{[^}]+\\\\}', '/analysis_cloud/', 0, 0, NULL, 1, NOW()),
        ('CFG_STQ_01', 'STQ', 'SHELL_SPARK', 'com.lineage.adapter.StqSparkAdapter', 'SparkSQL', 'Spark', 'spark-sql', '\\\\$\\\\{[^}]+\\\\}', '/user/hive/warehouse/eda_zqda.db/', 1, 1, '/logs/stq/', 1, NOW())
        """
    )


def downgrade() -> None:
    op.drop_table("user_preference")
    op.drop_table("lineage_permission")
    op.drop_table("log_collect_config")
    op.drop_table("script_parse_result")
    op.drop_table("script_parse_config")
    op.drop_table("cross_cluster_table_mapping")
    op.drop_table("cluster_registry")
    op.drop_table("lineage_node_remark_log")
    op.drop_table("lineage_column_edge")
    op.drop_table("lineage_edge")
    op.drop_table("lineage_node_column")
    op.drop_table("lineage_node")
