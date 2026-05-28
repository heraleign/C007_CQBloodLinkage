from __future__ import annotations

from sqlalchemy import Column, BigInteger, DateTime, Integer, String, Text

from app.models.base import Base


class ScriptParseResult(Base):
    __tablename__ = "script_parse_result"
    __table_args__ = {"comment": "脚本解析结果表"}

    result_id = Column(String(64), primary_key=True)
    script_path = Column(String(512), nullable=False, comment="脚本文件路径")
    vendor_code = Column(String(32), nullable=False)
    script_type = Column(String(32), nullable=False)
    parse_status = Column(String(20), nullable=False, comment="SUCCESS/PARTIAL/FAILED")

    sql_count = Column(Integer, default=0, comment="提取SQL数量")
    table_lineage_count = Column(Integer, default=0, comment="表级血缘数量")
    column_lineage_count = Column(Integer, default=0, comment="字段级血缘数量")

    ast_parsed_count = Column(Integer, default=0, comment="AST成功解析数")
    ai_supplement_count = Column(Integer, default=0, comment="AI补充数")
    manual_count = Column(Integer, default=0, comment="需人工处理数")

    error_message = Column(Text, comment="错误信息")
    unparsed_sqls = Column(Text, comment="未能解析的SQL片段")

    parse_time = Column(DateTime, nullable=False)
    parse_duration_ms = Column(BigInteger, comment="解析耗时(ms)")
