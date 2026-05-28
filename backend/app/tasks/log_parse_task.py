"""Log-based lineage parsing task — Capability 7 (§10).

Runs daily at 02:30 to collect and parse execution logs.
"""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.log_collect_config import LogCollectConfig


async def run_log_parse(db: AsyncSession):
    """Execute log-based lineage parsing."""
    # Load enabled log collection configs
    stmt = select(LogCollectConfig).where(LogCollectConfig.enabled == 1)
    result = await db.execute(stmt)
    configs = result.scalars().all()

    if not configs:
        return {"status": "no_configs", "message": "无可用的日志采集配置"}

    target_date = date.today()
    total_sqls = 0
    results_by_vendor = {}

    for config in configs:
        vendor = config.vendor_code
        if vendor not in results_by_vendor:
            results_by_vendor[vendor] = {"collected": 0, "parsed": 0}

        # Collect logs based on source type
        if config.log_source_type == "TDP":
            from app.services.log_collector import TDPLogCollector

            collector = TDPLogCollector(
                api_endpoint=config.log_path_pattern or "",
                auth_token="",
            )
            entries = await collector.collect(target_date)
        else:
            from app.services.log_collector import FileLogCollector

            collector = FileLogCollector(
                {
                    "sql_start_marker": config.sql_start_marker or "",
                    "sql_end_marker": config.sql_end_marker or "",
                    "task_id_pattern": config.task_id_pattern or "",
                    "filter_patterns": [],
                }
            )
            entries = await collector.collect(target_date)

        # Parse collected SQLs
        from app.services.parsing.sql_parser import SQLParser

        parser = SQLParser(dialect="SparkSQL")
        for entry in entries:
            lineage = parser.parse_table_lineage(entry.sql)
            total_sqls += 1
            results_by_vendor[vendor]["collected"] += 1
            if lineage.get("tableLineages"):
                results_by_vendor[vendor]["parsed"] += 1

    return {
        "status": "completed",
        "target_date": target_date.isoformat(),
        "total_sqls": total_sqls,
        "results_by_vendor": results_by_vendor,
    }
