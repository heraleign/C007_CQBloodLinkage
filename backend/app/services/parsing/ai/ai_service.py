"""AI-powered lineage parsing service.

Implements Capability 9 (§12) — AI-assisted SQL extraction and lineage completion.
"""

from __future__ import annotations

import json
from typing import Any

import httpx

from app.core.config import settings


class AILineageService:
    """Service for AI-assisted lineage extraction and completion."""

    def __init__(self):
        self.api_endpoint = settings.ai_api_endpoint
        self.api_key = settings.ai_api_key
        self.model = settings.ai_model
        self.timeout = settings.ai_timeout / 1000  # Convert to seconds

    async def extract_sql(
        self, script_content: str, rule_extracted_sqls: list[str]
    ) -> dict[str, Any] | None:
        """AI-assisted SQL extraction from Shell scripts (§12.2).

        Uses AI to find SQL statements that rule-based extraction missed.
        """
        if not self.api_key:
            return None

        prompt = self._build_sql_extract_prompt(script_content, rule_extracted_sqls)
        return await self._call_ai(prompt)

    async def supplement_lineage(
        self,
        script_content: str | None = None,
        extracted_sqls: list[str] | None = None,
        table_lineages: list[dict] | None = None,
        column_lineages: list[dict] | None = None,
    ) -> dict[str, Any] | None:
        """AI-assisted lineage supplement (§12.3).

        Uses AI to fill gaps in AST-based lineage parsing.
        """
        if not self.api_key:
            return None

        if not extracted_sqls:
            return None

        sql = extracted_sqls[0] if extracted_sqls else ""

        prompt = self._build_lineage_supplement_prompt(
            sql=sql,
            table_lineages=table_lineages or [],
            column_lineages=column_lineages or [],
        )
        return await self._call_ai(prompt)

    def _build_sql_extract_prompt(
        self, script_content: str, rule_extracted_sqls: list[str]
    ) -> str:
        return f"""You are a data engineer specializing in extracting SQL from Shell scripts.

## Task
Analyze the Shell script and extract all SQL statements.

## Rule-extracted SQLs
{json.dumps(rule_extracted_sqls, ensure_ascii=False, indent=2)}

## Script Content
```bash
{script_content[:8000]}
```

## Output (strict JSON only)
{{
    "verified_sqls": [
        {{"sql": "...", "source": "RULE_VERIFIED|AI_DISCOVERED", "confidence": 0.95}}
    ],
    "corrections": [],
    "dynamic_tables": []
}}"""

    def _build_lineage_supplement_prompt(
        self, sql: str, table_lineages: list[dict], column_lineages: list[dict]
    ) -> str:
        return f"""You are a SQL lineage analysis expert proficient in SparkSQL and HiveQL.

## Task
Supplement and improve the lineage relationships for the given SQL.

## SQL
```sql
{sql[:6000]}
```

## AST-parsed table lineages
{json.dumps(table_lineages, ensure_ascii=False, indent=2)}

## AST-parsed column lineages
{json.dumps(column_lineages, ensure_ascii=False, indent=2)}

## Output (strict JSON only)
{{
    "supplementTableLineages": [
        {{"sourceTable": "...", "targetTable": "...", "relationType": "...", "confidence": 0.9, "reason": "..."}}
    ],
    "supplementColumnLineages": [
        {{"sourceTable": "...", "sourceColumn": "...", "targetTable": "...", "targetColumn": "...", "transformExpr": "...", "confidence": 0.85, "reason": "..."}}
    ],
    "corrections": []
}}"""

    async def _call_ai(self, prompt: str) -> dict[str, Any] | None:
        """Call the AI model API."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    self.api_endpoint,
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {self.api_key}",
                    },
                    json={
                        "model": self.model,
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.1,
                        "max_tokens": 4096,
                    },
                )
                response.raise_for_status()
                data = response.json()
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                return self._parse_json_response(content)
        except Exception:
            return None

    def _parse_json_response(self, content: str) -> dict[str, Any] | None:
        """Extract JSON from AI response (handles markdown code fences)."""
        # Strip markdown fences if present
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return None
