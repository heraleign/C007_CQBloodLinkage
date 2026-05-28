"""Log-based lineage parsing — Capability 7 (§10).

Collects and parses execution logs to extract SQL for lineage generation.
"""

from __future__ import annotations

import re
from datetime import date, datetime
from typing import Any

import httpx


class LogEntry:
    """Represents a single SQL entry extracted from logs."""

    def __init__(self, sql: str, task_id: str | None = None, log_file: str | None = None):
        self.sql = sql
        self.task_id = task_id
        self.log_file = log_file
        self.timestamp: datetime | None = None


class FileLogCollector:
    """Collect SQL from file-system logs."""

    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.sql_start_marker = re.compile(config.get("sql_start_marker", r"Executing SQL:"))
        self.sql_end_marker = re.compile(config.get("sql_end_marker", r";\s*$"))
        self.task_id_pattern = re.compile(config.get("task_id_pattern", r"taskId=(\w+)"))
        self.filter_patterns = [re.compile(p) for p in config.get("filter_patterns", [])]

    async def collect(self, target_date: date) -> list[LogEntry]:
        """Collect SQL entries from logs for the given date."""
        entries = []
        # In production, this reads from actual log files on the filesystem
        # For now, return empty list (requires actual log path configuration)
        return entries

    def _process_line(self, line: str, entries: list[LogEntry]):
        """Process a single log line to extract SQL."""
        # Noise filtering
        for pattern in self.filter_patterns:
            if pattern.match(line):
                return

        # SQL start detection
        if self.sql_start_marker.search(line):
            sql_part = self.sql_start_marker.split(line, 1)[-1].strip()
            task_match = self.task_id_pattern.search(line)
            task_id = task_match.group(1) if task_match else None
            entries.append(LogEntry(sql=sql_part, task_id=task_id))


class TDPLogCollector:
    """Collect SQL from TDP platform API."""

    def __init__(self, api_endpoint: str, auth_token: str):
        self.api_endpoint = api_endpoint
        self.auth_token = auth_token

    async def collect(self, target_date: date) -> list[LogEntry]:
        """Call TDP API to get execution logs for the target date."""
        entries = []
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(
                    f"{self.api_endpoint}/api/executions",
                    params={"date": target_date.isoformat()},
                    headers={"Authorization": f"Bearer {self.auth_token}"},
                )
                if response.status_code == 200:
                    data = response.json()
                    for execution in data.get("executions", []):
                        log_content = execution.get("log", "")
                        sqls = self._extract_sqls_from_log(log_content)
                        for sql in sqls:
                            entry = LogEntry(sql=sql, task_id=execution.get("taskId"))
                            entries.append(entry)
        except Exception:
            pass  # Log error in production
        return entries

    def _extract_sqls_from_log(self, log_content: str) -> list[str]:
        """Extract SQL statements from raw log content."""
        sqls = []
        # Simple heuristic: find lines containing SELECT/INSERT/CREATE
        for line in log_content.split("\n"):
            upper = line.strip().upper()
            if any(upper.startswith(kw) for kw in ["SELECT", "INSERT", "CREATE", "MERGE", "ALTER"]):
                sqls.append(line.strip())
        return sqls
