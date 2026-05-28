from __future__ import annotations

from sqlalchemy import Column, DateTime, String, Text, SmallInteger, text as sa_text

from app.models.base import Base


class LogCollectConfig(Base):
    __tablename__ = "log_collect_config"
    __table_args__ = {"comment": "日志采集配置表"}

    config_id = Column(String(64), primary_key=True)
    vendor_code = Column(String(32), nullable=False, comment="厂商编码")
    log_source_type = Column(String(20), nullable=False, comment="TDP/FILE/STDOUT")
    log_path_pattern = Column(String(512), comment="日志路径模式，支持通配符")
    log_file_encoding = Column(String(20), default="UTF-8")
    log_date_format = Column(String(64), comment="日志时间格式")
    sql_start_marker = Column(String(256), comment="SQL起始标记正则")
    sql_end_marker = Column(String(256), comment="SQL结束标记正则")
    task_id_pattern = Column(String(256), comment="任务ID提取正则")
    filter_patterns = Column(Text, comment="噪声过滤规则JSON数组")
    collect_schedule = Column(String(32), default="0 30 2 * * ?", comment="采集调度表达式")
    enabled = Column(SmallInteger, default=1)
    create_time = Column(DateTime, server_default=sa_text("CURRENT_TIMESTAMP"))
