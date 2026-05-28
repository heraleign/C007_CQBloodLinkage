"""Script parse dispatcher — routes scripts to the appropriate adapter.

Implements the multi-vendor adapter architecture described in §5.2.2.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from app.services.parsing.sql_parser import ScriptSQLExtractor


class ScriptParseDispatcher:
    """Main entry point for script parsing — dispatches to vendor-specific adapters."""

    async def parse(
        self,
        script_content: str,
        vendor_code: str = "DIKE",
        script_type: str = "SHELL_SPARK",
        variable_map: dict[str, str] | None = None,
        enable_ai: bool = True,
    ) -> dict[str, Any]:
        """Parse a script and extract lineage.

        Args:
            script_content: Raw script content
            vendor_code: DIKE / STQ / SHUPAI / DF
            script_type: SHELL_SPARK / SHELL_HBASE / etc.
            variable_map: Variable substitutions
            enable_ai: Whether to attempt AI-based completion

        Returns:
            Parsed result with table and column lineage
        """
        start_time = datetime.now()

        extractor = ScriptSQLExtractor(variable_map or {})
        extracted_sqls = extractor.extract_sqls(script_content)

        if not extracted_sqls:
            return {
                "parseId": f"PARSE_{start_time.strftime('%Y%m%d_%H%M%S')}",
                "sqlsExtracted": 0,
                "tableLineages": [],
                "columnLineages": [],
                "warnings": ["未从脚本中提取到SQL语句"],
            }

        # Parse each extracted SQL
        from app.services.parsing.sql_parser import SQLParser

        parser = SQLParser(dialect=self._resolve_dialect(vendor_code, script_type))
        all_table_lineages = []
        all_column_lineages = []

        for item in extracted_sqls:
            sql = item["sql"]
            table_result = parser.parse_table_lineage(sql)
            all_table_lineages.extend(table_result.get("tableLineages", []))

            col_result = parser.parse_column_lineage(sql)
            all_column_lineages.extend(col_result.get("columnLineages", []))

        duration = (datetime.now() - start_time).total_seconds() * 1000

        result = {
            "parseId": f"PARSE_{start_time.strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:4]}",
            "sqlsExtracted": len(extracted_sqls),
            "tableLineages": all_table_lineages,
            "columnLineages": all_column_lineages,
            "parseMethod": "RULE+AST",
            "confidence": 0.85 if all_table_lineages else 0.0,
            "parseDurationMs": int(duration),
            "warnings": [],
        }

        # AI supplement if enabled
        if enable_ai and (not all_table_lineages or not all_column_lineages):
            try:
                from app.services.parsing.ai.ai_service import AILineageService

                ai_service = AILineageService()
                ai_result = await ai_service.supplement_lineage(
                    script_content=script_content,
                    extracted_sqls=[e["sql"] for e in extracted_sqls],
                    table_lineages=all_table_lineages,
                    column_lineages=all_column_lineages,
                )
                if ai_result:
                    result["tableLineages"].extend(ai_result.get("supplementTableLineages", []))
                    result["columnLineages"].extend(ai_result.get("supplementColumnLineages", []))
                    result["parseMethod"] = "RULE+AST+AI"
                    result["confidence"] = 0.92
            except Exception:
                result["warnings"].append("AI补充服务调用失败，仅使用规则解析结果")

        return result

    def _resolve_dialect(self, vendor_code: str, script_type: str) -> str:
        mapping = {
            ("DIKE", "SHELL_SPARK"): "SparkSQL",
            ("DIKE", "SHELL_HBASE"): "HiveQL",
            ("STQ", "SHELL_SPARK"): "SparkSQL",
            ("SHUPAI", "SHELL_SPARK"): "SparkSQL",
            ("DF", "SHELL"): "SparkSQL",
        }
        return mapping.get((vendor_code, script_type), "SparkSQL")
