"""AI fusion engine — merges AST parsing results with AI supplement results.

Implements the fusion logic described in §12.3.3.
"""

from __future__ import annotations

from typing import Any


class AILineageFusionEngine:
    """Fuse AST-parsed lineage with AI-supplemented lineage results."""

    @staticmethod
    def fuse(
        ast_table_lineages: list[dict[str, Any]],
        ast_column_lineages: list[dict[str, Any]],
        ai_result: dict[str, Any] | None,
    ) -> dict[str, Any]:
        """Merge AST and AI results, with AST taking priority for exact matches."""
        final = {
            "tableLineages": [],
            "columnLineages": [],
            "parseMethod": "AST",
            "confidence": 0.0,
        }

        # Track keys for deduplication
        table_keys: set[str] = set()
        column_keys: set[str] = set()

        # 1. AST results (high confidence baseline)
        for tl in ast_table_lineages:
            key = f"{tl.get('sourceTable', '')}|{tl.get('targetTable', '')}"
            if key not in table_keys:
                tl["confidence"] = 0.98
                tl["parseMethod"] = "AST"
                table_keys.add(key)
                final["tableLineages"].append(tl)

        for cl in ast_column_lineages:
            key = f"{cl.get('sourceTable', '')}.{cl.get('sourceColumn', '')}|{cl.get('targetTable', '')}.{cl.get('targetColumn', '')}"
            key2 = f"{cl.get('sourceColumn', '')}|{cl.get('targetColumn', '')}"
            if key not in column_keys and key2 not in column_keys:
                cl["confidence"] = 0.95
                cl["parseMethod"] = "AST"
                column_keys.add(key)
                final["columnLineages"].append(cl)

        # 2. AI supplement results (fill gaps only)
        if ai_result:
            for stl in ai_result.get("supplementTableLineages", []):
                key = f"{stl.get('sourceTable', '')}|{stl.get('targetTable', '')}"
                if key not in table_keys:
                    stl["parseMethod"] = "AI"
                    table_keys.add(key)
                    final["tableLineages"].append(stl)

            for scl in ai_result.get("supplementColumnLineages", []):
                key = f"{scl.get('sourceTable', '')}.{scl.get('sourceColumn', '')}|{scl.get('targetTable', '')}.{scl.get('targetColumn', '')}"
                key2 = f"{scl.get('sourceColumn', '')}|{scl.get('targetColumn', '')}"
                if key not in column_keys and key2 not in column_keys:
                    scl["parseMethod"] = "AI"
                    column_keys.add(key)
                    final["columnLineages"].append(scl)

        # 3. Compute overall confidence
        if final["tableLineages"] and final["columnLineages"]:
            final["confidence"] = 0.95
            final["parseMethod"] = "AST+AI"
        elif final["tableLineages"]:
            final["confidence"] = 0.90
            final["parseMethod"] = "AST+AI"

        return final
