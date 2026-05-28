from __future__ import annotations

from sqlalchemy import Column, DateTime, String, Text, SmallInteger, text as sa_text

from app.models.base import Base


class ScriptParseConfig(Base):
    __tablename__ = "script_parse_config"
    __table_args__ = {"comment": "脚本解析配置表"}

    config_id = Column(String(64), primary_key=True)
    vendor_code = Column(String(32), nullable=False, comment="厂商编码")
    script_type = Column(String(32), nullable=False, comment="脚本类型编码")
    adapter_class = Column(String(256), nullable=False, comment="适配器类全路径")
    sql_dialect = Column(String(20), nullable=False, comment="SQL方言")
    exec_engine = Column(String(20), nullable=False, comment="执行引擎")
    exec_command = Column(String(64), comment="执行命令模式")
    variable_pattern = Column(String(256), comment="变量占位符正则")
    script_base_path = Column(String(512), comment="脚本存储基础路径")
    has_nested_call = Column(SmallInteger, default=0, comment="是否有嵌套调用")
    log_parse_enabled = Column(SmallInteger, default=0, comment="是否启用日志解析")
    log_path_pattern = Column(String(512), comment="日志路径模式")
    status = Column(SmallInteger, default=1)
    create_time = Column(DateTime, server_default=sa_text("CURRENT_TIMESTAMP"))
