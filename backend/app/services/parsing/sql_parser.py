"""SQL parser for lineage extraction using sqlparse.

Implements the parsing engine described in the design document §5 & §11.
Uses sqlparse for initial implementation; ANTLR4 can be added later.
"""

from __future__ import annotations

import re
from typing import Any

import sqlparse
from sqlparse.sql import Identifier, IdentifierList, TokenList, Where, Comparison
from sqlparse.tokens import Keyword, Name, Punctuation, Whitespace


class SQLParser:
    """Parse SQL to extract table-level and column-level lineage."""

    def __init__(self, dialect: str = "SparkSQL"):
        self.dialect = dialect
        # SparkSQL/HiveQL specific keywords
        self.dml_keywords = {"INSERT", "CREATE", "SELECT", "MERGE", "OVERWRITE", "INTO", "TABLE"}

    def parse_table_lineage(self, sql: str) -> dict[str, Any]:
        """Extract table-level lineage from SQL.

        Returns:
            dict with parseId, parseMethod, confidence, tableLineages[]
        """
        import uuid
        from datetime import datetime

        parsed = sqlparse.parse(sql)
        table_lineages = []

        for stmt in parsed:
            tables = self._extract_tables(stmt)
            if not tables:
                continue

            # Identify target table (INSERT INTO / CREATE TABLE ... AS)
            target = self._find_target_table(stmt)

            # Identify source tables (FROM / JOIN)
            sources = self._find_source_tables(stmt)

            if target:
                for source in sources:
                    table_lineages.append(
                        {
                            "sourceTable": source,
                            "targetTable": target,
                            "relationType": "INSERT_SELECT",
                        }
                    )
            elif sources:
                # SELECT-only, no INSERT — treat as standalone
                pass

        return {
            "parseId": f"PARSE_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:4]}",
            "parseMethod": "AST",
            "confidence": 0.95 if table_lineages else 0.0,
            "tableLineages": table_lineages,
            "sqlCount": len(parsed),
        }

    def parse_column_lineage(self, sql: str) -> dict[str, Any]:
        """Extract column-level lineage from SQL.

        Returns:
            dict with parseId, columnLineages[]
        """
        import uuid
        from datetime import datetime

        parsed = sqlparse.parse(sql)
        column_lineages = []

        for stmt in parsed:
            target = self._find_target_table(stmt)
            if not target:
                continue

            # Extract SELECT columns and map to target columns
            select_cols = self._extract_select_columns(stmt)
            target_cols = self._extract_target_columns(stmt)

            # Simple positional mapping
            for i, col in enumerate(select_cols):
                if i < len(target_cols):
                    column_lineages.append(
                        {
                            "sourceTable": self._resolve_source_table(col, stmt),
                            "sourceColumn": col,
                            "targetTable": target,
                            "targetColumn": target_cols[i],
                            "transformExpr": "DIRECT",
                        }
                    )

        return {
            "parseId": f"PARSE_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:4]}",
            "parseMethod": "AST",
            "confidence": 0.90 if column_lineages else 0.0,
            "columnLineages": column_lineages,
        }

    def _extract_tables(self, stmt: TokenList) -> list[str]:
        """Extract all table references from a statement."""
        tables = []
        from_seen = False
        for token in stmt.tokens:
            if token.is_group:
                tables.extend(self._extract_tables(token))
            if self._is_keyword_token(token) and token.value.upper() in ("FROM", "JOIN"):
                from_seen = True
            if from_seen and isinstance(token, Identifier):
                tables.append(self._clean_table_name(str(token)))
                from_seen = False
            if isinstance(token, Where):
                break
        return tables

    @staticmethod
    def _is_keyword_token(token) -> bool:
        """Check if a token is a keyword (handles nested types like Keyword.DML)."""
        tt = token.ttype
        if tt is None:
            return False
        return str(tt).startswith("Token.Keyword")

    def _find_target_table(self, stmt: TokenList) -> str | None:
        """Find the target table in INSERT INTO or CREATE TABLE statements."""
        tokens = list(stmt.tokens)
        for i, token in enumerate(tokens):
            if not self._is_keyword_token(token):
                continue
            upper = token.value.upper()

            if upper == "INSERT":
                # Look for the next Identifier after INSERT/INTO
                for j in range(i + 1, len(tokens)):
                    if isinstance(tokens[j], Identifier):
                        return self._clean_table_name(str(tokens[j]))
                    # Skip whitespace and keywords (INTO, OVERWRITE, etc.)
                    tt_str = str(tokens[j].ttype) if tokens[j].ttype else ""
                    if "Whitespace" in tt_str or "Keyword" in tt_str:
                        continue
                    break

            elif upper == "CREATE":
                # Check if followed by TABLE or VIEW
                for j in range(i + 1, len(tokens)):
                    val = tokens[j].value.upper()
                    if val in ("TABLE", "VIEW") and self._is_keyword_token(tokens[j]):
                        # Look for the Identifier after TABLE/VIEW
                        for k in range(j + 1, len(tokens)):
                            if isinstance(tokens[k], Identifier):
                                return self._clean_table_name(str(tokens[k]))
                            if str(tokens[k].ttype or "").startswith("Token.Text"):
                                continue
                            break
                    if str(tokens[j].ttype or "").startswith("Token.Text"):
                        continue
                    break

        return None

    def _find_source_tables(self, stmt: TokenList) -> list[str]:
        """Find source tables from FROM/JOIN clauses."""
        sources = []
        in_from = False
        in_join = False

        for token in stmt.tokens:
            if isinstance(token, Where):
                break

            if isinstance(token, Comparison):
                continue

            upper = token.value.upper()

            # Check for FROM keyword
            if upper == "FROM" and self._is_keyword_token(token):
                in_from = True
                in_join = False
                continue

            # Check for JOIN keywords (JOIN, LEFT JOIN, etc.)
            if "JOIN" in upper and self._is_keyword_token(token):
                in_join = True
                in_from = False
                continue

            if in_from and isinstance(token, Identifier):
                table_name = self._clean_table_name(str(token))
                if table_name:
                    sources.append(table_name)
                in_from = False

            if in_join and isinstance(token, Identifier):
                table_name = self._clean_table_name(str(token))
                if table_name:
                    sources.append(table_name)
                in_join = False

        return sources

    @staticmethod
    def _clean_table_name(name: str) -> str:
        """Extract the actual table reference (strip alias)."""
        # Handle "db.table alias" or "table alias"
        parts = name.split()
        return parts[0].strip()

    def _extract_select_columns(self, stmt: TokenList) -> list[str]:
        """Extract column names from SELECT clause."""
        columns = []
        select_seen = False

        for token in stmt.tokens:
            if self._is_keyword_token(token) and token.value.upper() == "SELECT":
                select_seen = True
                continue

            if select_seen:
                if self._is_keyword_token(token):
                    if token.value.upper() in ("FROM", "INTO", "WHERE", "GROUP", "ORDER", "LIMIT"):
                        break
                if isinstance(token, Identifier):
                    columns.append(str(token))
                elif isinstance(token, IdentifierList):
                    for ident in token.get_identifiers():
                        columns.append(str(ident))
                elif token.ttype is Name:
                    columns.append(str(token))

        return columns

    def _extract_target_columns(self, stmt: TokenList) -> list[str]:
        """Extract target columns from INSERT INTO table(col1, col2) part."""
        # Look for parenthesized column list after INSERT INTO table
        tokens = list(stmt.tokens)
        for i, token in enumerate(tokens):
            if token.value.upper() == "INSERT" and self._is_keyword_token(token):
                # Look ahead for parenthesized list
                for j in range(i + 1, len(tokens)):
                    if isinstance(tokens[j], TokenList):
                        inner = str(tokens[j])
                        if inner.startswith("(") and inner.endswith(")"):
                            cols = inner.strip("()").split(",")
                            return [c.strip() for c in cols if c.strip()]
        return []  # No explicit column list — target columns match SELECT

    def _resolve_source_table(self, column: str, stmt: TokenList) -> str:
        """Resolve which source table a column belongs to."""
        # Handle alias.column pattern
        if "." in column:
            parts = column.split(".")
            if len(parts) == 2:
                return parts[0]  # Return alias/table name
        return "UNKNOWN"


class ScriptSQLExtractor:
    """Extract SQL from Shell scripts using regex patterns.

    Implements §5.2 — handles spark-sql, beeline, hive commands.
    """

    SQL_PATTERNS = [
        # spark-sql -e "..." (double-quoted SQL)
        re.compile(r'spark-sql\s+(?:-[a-z]+\s+)*?-e\s+"(.*?)"', re.DOTALL),
        # spark-sql -e '...' (single-quoted SQL)
        re.compile(r"spark-sql\s+(?:-[a-z]+\s+)*?-e\s+'(.*?)'", re.DOTALL),
        # beeline -e "..."
        re.compile(r'beeline\s+(?:-[a-z]+\s+)*?-e\s+"(.*?)"', re.DOTALL),
        # beeline -e '...'
        re.compile(r"beeline\s+(?:-[a-z]+\s+)*?-e\s+'(.*?)'", re.DOTALL),
        # hive -e "..."
        re.compile(r'hive\s+(?:-[a-z]+\s+)*?-e\s+"(.*?)"', re.DOTALL),
        # hive -e '...'
        re.compile(r"hive\s+(?:-[a-z]+\s+)*?-e\s+'(.*?)'", re.DOTALL),
        # heredoc pattern: << EOF ... EOF
        re.compile(r'<<\s*(\w+)\s*\n(.*?)\n\s*\1', re.DOTALL),
        # sql="..." pattern
        re.compile(r'(?:sql|SQL)\s*=\s*"(.*?)"', re.DOTALL),
        # sql='...' pattern
        re.compile(r"(?:sql|SQL)\s*=\s*'(.*?)'", re.DOTALL),
    ]

    VARIABLE_PATTERN = re.compile(r'\$\{?(\w+)\}?')

    def __init__(self, variable_map: dict[str, str] | None = None):
        self.variable_map = variable_map or {}

    def extract_sqls(self, script_content: str) -> list[dict[str, str | float]]:
        """Extract SQL statements from Shell script content."""
        results = []
        seen = set()

        for pattern in self.SQL_PATTERNS:
            for match in pattern.finditer(script_content):
                sql = match.group(1).strip()
                if not sql or sql in seen:
                    continue
                seen.add(sql)
                resolved_sql = self._resolve_variables(sql)
                results.append({
                    "sql": resolved_sql,
                    "original_sql": sql,
                    "source": "RULE",
                    "confidence": 0.85,
                })

        return results

    def _resolve_variables(self, sql: str) -> str:
        """Replace ${var} placeholders with provided values."""

        def replacer(m: re.Match) -> str:
            var_name = m.group(1)
            return self.variable_map.get(var_name, f"${{{var_name}}}")

        return self.VARIABLE_PATTERN.sub(replacer, sql)
