"""Tests for the SQL parser."""

from app.services.parsing.sql_parser import SQLParser, ScriptSQLExtractor


def test_parse_table_lineage_insert_select():
    parser = SQLParser(dialect="SparkSQL")
    sql = "INSERT INTO dw.target_table SELECT a.id, b.name FROM ods.table_a a JOIN ods.table_b b ON a.id = b.id"
    result = parser.parse_table_lineage(sql)
    assert len(result["tableLineages"]) > 0
    assert any(t["targetTable"] == "dw.target_table" for t in result["tableLineages"])
    assert any(t["sourceTable"] == "ods.table_a" for t in result["tableLineages"])
    assert any(t["sourceTable"] == "ods.table_b" for t in result["tableLineages"])


def test_parse_table_lineage_create_as():
    parser = SQLParser(dialect="SparkSQL")
    sql = "CREATE TABLE dw.agg_table AS SELECT * FROM ods.source_table"
    result = parser.parse_table_lineage(sql)
    assert len(result["tableLineages"]) > 0


def test_script_sql_extractor_spark():
    extractor = ScriptSQLExtractor(variable_map={"day_id": "20260515"})
    script = '#!/bin/bash\nday_id=$1\nspark-sql -e "INSERT INTO dw.target SELECT * FROM ods.source WHERE day_id=\'${day_id}\'"'
    results = extractor.extract_sqls(script)
    assert len(results) > 0
    assert "20260515" in results[0]["sql"] or "${day_id}" in results[0]["sql"]

    # Test variable resolution
    resolved = extractor._resolve_variables("SELECT * FROM table WHERE day_id = '${day_id}'")
    assert "20260515" in resolved


def test_script_sql_extractor_heredoc():
    extractor = ScriptSQLExtractor()
    script = """#!/bin/bash
spark-sql << EOF
INSERT INTO dw.target SELECT * FROM ods.source;
EOF
"""
    results = extractor.extract_sqls(script)
    assert len(results) > 0
