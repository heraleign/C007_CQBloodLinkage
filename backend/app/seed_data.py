"""重庆电信行业种子数据 — 用于串联验证全链路血缘功能。

运行方式：
  cd backend
  source venv/Scripts/activate
  python -m app.seed_data

依赖：需要 MySQL 数据库 lineage 已创建，表结构已通过 alembic upgrade head 初始化。
"""

import uuid
from datetime import datetime

from sqlalchemy import create_engine, text

from app.core.config import settings

# ---------- 同步引擎（非异步，seed 脚本专用） ----------
sync_url = settings.database_url.replace("asyncmy", "pymysql")
engine = create_engine(sync_url)

NOW = datetime.now()


def run():
    with engine.begin() as conn:
        # ========== 0. 清理旧数据（幂等重置）==========
        # 避免重复运行时 INSERT IGNORE 跳过节点导致 node_map 中的 UUID 与数据库不一致
        conn.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
        for tbl in ["lineage_column_edge", "lineage_edge", "lineage_node_column", "lineage_node_remark_log", "lineage_node", "cluster_registry", "ai_call_config"]:
            conn.execute(text(f"DELETE FROM {tbl}"))
        conn.execute(text("SET FOREIGN_KEY_CHECKS = 1"))

        # ========== 1. 集群注册 ==========
        clusters = [
            {"cluster_id": "TDP_PROD", "cluster_name": "TDP生产集群", "cluster_type": "TDP", "api_endpoint": "http://tdp.cqtelecom.cn:8080"},
            {"cluster_id": "ANALYSIS_CLOUD", "cluster_name": "分析云集群", "cluster_type": "CDH", "api_endpoint": "http://analytics.cqtelecom.cn:8888"},
        ]
        for c in clusters:
            conn.execute(
                text("""INSERT IGNORE INTO cluster_registry (cluster_id, cluster_name, cluster_type, api_endpoint, status, create_time)
                        VALUES (:cid, :cn, :ct, :ae, 1, :now)"""),
                {"cid": c["cluster_id"], "cn": c["cluster_name"], "ct": c["cluster_type"], "ae": c["api_endpoint"], "now": NOW},
            )

        # ========== 2. 血缘节点 ==========
        nodes = [
            # ---- 源系统（EXT_DB） ----
            {"id": uid(), "type": "EXT_DB", "name": "CRM用户表", "uk": "10.10.1.10:3306/crm/crmdb/t_user", "sys": "CRM", "db": "crmdb", "tbl": "t_user", "cn": "用户信息表", "ip": "10.10.1.10", "port": "3306"},
            {"id": uid(), "type": "EXT_DB", "name": "CRM账户表", "uk": "10.10.1.10:3306/crm/crmdb/t_account", "sys": "CRM", "db": "crmdb", "tbl": "t_account", "cn": "账户信息表", "ip": "10.10.1.10", "port": "3306"},
            {"id": uid(), "type": "EXT_DB", "name": "计费详单表", "uk": "10.10.1.20:3306/billing/billdb/t_cdr", "sys": "计费系统", "db": "billdb", "tbl": "t_cdr", "cn": "通话详单表", "ip": "10.10.1.20", "port": "3306"},
            {"id": uid(), "type": "EXT_DB", "name": "计费账单表", "uk": "10.10.1.20:3306/billing/billdb/t_bill", "sys": "计费系统", "db": "billdb", "tbl": "t_bill", "cn": "月账单汇总表", "ip": "10.10.1.20", "port": "3306"},
            {"id": uid(), "type": "EXT_DB", "name": "营销订单表", "uk": "10.10.1.30:3306/marketing/mktdb/t_order", "sys": "营销沙盘", "db": "mktdb", "tbl": "t_order", "cn": "营销活动订单表", "ip": "10.10.1.30", "port": "3306"},
            {"id": uid(), "type": "EXT_DB", "name": "营销活动表", "uk": "10.10.1.30:3306/marketing/mktdb/t_campaign", "sys": "营销沙盘", "db": "mktdb", "tbl": "t_campaign", "cn": "营销活动配置表", "ip": "10.10.1.30", "port": "3306"},
            {"id": uid(), "type": "EXT_FILE", "name": "宽带日志文件", "uk": "sftp://10.10.1.40:22/data/broadband/access_*.log", "sys": "宽带系统", "tbl": "宽带接入日志", "ip": "10.10.1.40", "port": "22", "protocol": "sftp"},
            {"id": uid(), "type": "EXT_KAFKA", "name": "实时话单Topic", "uk": "kafka01.cqtelecom.cn:9092/topic_cdr_realtime", "sys": "计费系统", "tbl": "实时话单流"},
            # ---- 湖内ODS层（LAKE_TABLE） ----
            {"id": uid(), "type": "LAKE_TABLE", "name": "ODS用户表", "uk": "TDP_PROD::ods::ods_crm_user", "sys": "CRM", "cluster": "TDP_PROD", "db": "ods", "tbl": "ods_crm_user", "cn": "ODS用户信息表"},
            {"id": uid(), "type": "LAKE_TABLE", "name": "ODS账户表", "uk": "TDP_PROD::ods::ods_crm_account", "sys": "CRM", "cluster": "TDP_PROD", "db": "ods", "tbl": "ods_crm_account", "cn": "ODS账户信息表"},
            {"id": uid(), "type": "LAKE_TABLE", "name": "ODS通话详单", "uk": "TDP_PROD::ods::ods_bill_cdr", "sys": "计费系统", "cluster": "TDP_PROD", "db": "ods", "tbl": "ods_bill_cdr", "cn": "ODS通话详单"},
            {"id": uid(), "type": "LAKE_TABLE", "name": "ODS账单表", "uk": "TDP_PROD::ods::ods_bill_monthly", "sys": "计费系统", "cluster": "TDP_PROD", "db": "ods", "tbl": "ods_bill_monthly", "cn": "ODS月账单"},
            {"id": uid(), "type": "LAKE_TABLE", "name": "ODS营销订单", "uk": "TDP_PROD::ods::ods_mkt_order", "sys": "营销沙盘", "cluster": "TDP_PROD", "db": "ods", "tbl": "ods_mkt_order", "cn": "ODS营销订单"},
            {"id": uid(), "type": "LAKE_TABLE", "name": "ODS宽带日志", "uk": "TDP_PROD::ods::ods_broadband_log", "sys": "宽带系统", "cluster": "TDP_PROD", "db": "ods", "tbl": "ods_broadband_log", "cn": "ODS宽带接入日志"},
            {"id": uid(), "type": "LAKE_TABLE", "name": "ODS实时话单", "uk": "TDP_PROD::ods::ods_cdr_realtime", "sys": "计费系统", "cluster": "TDP_PROD", "db": "ods", "tbl": "ods_cdr_realtime", "cn": "ODS实时话单"},
            # ---- 湖内DWD层（LAKE_TABLE） ----
            {"id": uid(), "type": "LAKE_TABLE", "name": "DWD用户账户宽表", "uk": "TDP_PROD::dwd::dwd_user_account_df", "sys": "CRM", "cluster": "TDP_PROD", "db": "dwd", "tbl": "dwd_user_account_df", "cn": "用户账户关联宽表"},
            {"id": uid(), "type": "LAKE_TABLE", "name": "DWD账单明细", "uk": "TDP_PROD::dwd::dwd_bill_detail_df", "sys": "计费系统", "cluster": "TDP_PROD", "db": "dwd", "tbl": "dwd_bill_detail_df", "cn": "账单明细事实表"},
            {"id": uid(), "type": "LAKE_TABLE", "name": "DWD营销订单明细", "uk": "TDP_PROD::dwd::dwd_mkt_order_detail_df", "sys": "营销沙盘", "cluster": "TDP_PROD", "db": "dwd", "tbl": "dwd_mkt_order_detail_df", "cn": "营销订单明细事实表"},
            # ---- 湖内DWS层（LAKE_TABLE） ----
            {"id": uid(), "type": "LAKE_TABLE", "name": "DWS用户汇总", "uk": "TDP_PROD::dws::dws_user_daily_sum", "sys": "CRM", "cluster": "TDP_PROD", "db": "dws", "tbl": "dws_user_daily_sum", "cn": "用户日汇总表"},
            {"id": uid(), "type": "LAKE_TABLE", "name": "DWS收入汇总", "uk": "TDP_PROD::dws::dws_revenue_daily_sum", "sys": "计费系统", "cluster": "TDP_PROD", "db": "dws", "tbl": "dws_revenue_daily_sum", "cn": "收入日汇总表"},
            {"id": uid(), "type": "LAKE_TABLE", "name": "DWS营销效果汇总", "uk": "TDP_PROD::dws::dws_mkt_effect_daily_sum", "sys": "营销沙盘", "cluster": "TDP_PROD", "db": "dws", "tbl": "dws_mkt_effect_daily_sum", "cn": "营销效果日汇总表"},
            # ---- DM层（LAKE_TABLE） ----
            {"id": uid(), "type": "LAKE_TABLE", "name": "DM经营分析看板", "uk": "TDP_PROD::dm::dm_business_board", "sys": "数据分析平台", "cluster": "TDP_PROD", "db": "dm", "tbl": "dm_business_board", "cn": "经营分析看板"},
            {"id": uid(), "type": "LAKE_TABLE", "name": "DM收入财务表", "uk": "TDP_PROD::dm::dm_income_financial", "sys": "数据分析平台", "cluster": "TDP_PROD", "db": "dm", "tbl": "dm_income_financial", "cn": "收入财务报表"},
            {"id": uid(), "type": "LAKE_TABLE", "name": "DM用户画像表", "uk": "TDP_PROD::dm::dm_user_portrait", "sys": "数据分析平台", "cluster": "TDP_PROD", "db": "dm", "tbl": "dm_user_portrait", "cn": "用户画像标签表"},
            # ---- 出湖（OUT_DB / OUT_FILE） ----
            {"id": uid(), "type": "OUT_DB", "name": "经营分析系统-看板", "uk": "10.10.2.10:3306/analytics/dashboard/dashboard_summary", "sys": "经营分析系统", "db": "dashboard", "tbl": "dashboard_summary", "cn": "经营分析看板数据", "ip": "10.10.2.10", "port": "3306"},
            {"id": uid(), "type": "OUT_ES", "name": "ES收入查询索引", "uk": "es01.cqtelecom.cn:9200/revenue_index", "sys": "数据分析平台", "tbl": "revenue_index", "cn": "收入ES查询索引"},
            {"id": uid(), "type": "OUT_API", "name": "用户画像API", "uk": "api.cqtelecom.cn/portrait/v1/get_tags", "sys": "数据分析平台", "tbl": "用户画像查询接口"},
            {"id": uid(), "type": "OUT_FILE", "name": "财务报表行云文件", "uk": "XINGYUN://fs01/report/finance_daily_*.xlsx", "sys": "财务系统", "tbl": "财务日报"},
        ]

        # 先收集 node_id 映射用于建边
        node_map = {}
        for n in nodes:
            nid = n["id"]
            conn.execute(
                text("""INSERT IGNORE INTO lineage_node
                        (node_id, node_type, node_name, node_unique_key, system_code, system_name, cluster_id, cluster_name, database_name, table_name, table_cn_name, server_ip, server_port, protocol, source_type, status, create_time, update_time)
                        VALUES (:id, :type, :name, :uk, :sys, :sys, :cluster, :cluster, :db, :tbl, :cn, :ip, :port, :proto, 'AUTO', 1, :now, :now)"""),
                {
                    "id": nid, "type": n["type"], "name": n["name"], "uk": n["uk"],
                    "sys": n.get("sys", ""), "cluster": n.get("cluster", ""),
                    "db": n.get("db", ""), "tbl": n.get("tbl", ""), "cn": n.get("cn", ""),
                    "ip": n.get("ip", ""), "port": n.get("port", ""), "proto": n.get("protocol", ""),
                    "now": NOW,
                },
            )
            node_map[n["name"]] = nid

        # ========== 3. 血缘边 ==========
        edges = [
            # ---- 入湖阶段：EXT_DB → ODS ----
            ("CRM用户表", "ODS用户表", "INGEST", "DB", "全量+CDC同步"),
            ("CRM账户表", "ODS账户表", "INGEST", "DB", "全量+CDC同步"),
            ("计费详单表", "ODS通话详单", "INGEST", "DB", "T+1批量同步"),
            ("计费账单表", "ODS账单表", "INGEST", "DB", "T+1批量同步"),
            ("营销订单表", "ODS营销订单", "INGEST", "DB", "实时同步"),
            # ---- 入湖阶段：EXT_FILE → ODS ----
            ("宽带日志文件", "ODS宽带日志", "INGEST", "FILE", "SFTP采集"),
            # ---- 入湖阶段：EXT_KAFKA → ODS ----
            ("实时话单Topic", "ODS实时话单", "INGEST", "KAFKA", "Kafka Flink消费"),
            # ---- 湖内加工：ODS → DWD ----
            ("ODS用户表", "DWD用户账户宽表", "PROCESS", "AST", "spark-sql LEFT JOIN"),
            ("ODS账户表", "DWD用户账户宽表", "PROCESS", "AST", "spark-sql LEFT JOIN"),
            ("ODS通话详单", "DWD账单明细", "PROCESS", "AST", "spark-sql INSERT OVERWRITE"),
            ("ODS账单表", "DWD账单明细", "PROCESS", "AST", "spark-sql UNION ALL"),
            ("ODS营销订单", "DWD营销订单明细", "PROCESS", "AST", "spark-sql INSERT SELECT"),
            # ---- 湖内加工：DWD → DWS ----
            ("DWD用户账户宽表", "DWS用户汇总", "PROCESS", "AST", "spark-sql GROUP BY user_id"),
            ("DWD账单明细", "DWS收入汇总", "PROCESS", "AST", "spark-sql SUM(amount) GROUP BY day"),
            ("DWD营销订单明细", "DWS营销效果汇总", "PROCESS", "AST", "spark-sql GROUP BY campaign_id"),
            # ---- 湖内加工：DWS → DM ----
            ("DWS用户汇总", "DM用户画像表", "PROCESS", "AST+AI", "spark-sql JOIN多维度打标签"),
            ("DWS收入汇总", "DM收入财务表", "PROCESS", "AST", "spark-sql INSERT OVERWRITE"),
            ("DWS用户汇总", "DM经营分析看板", "PROCESS", "AST+AI", "spark-sql UNION多源汇总"),
            ("DWS收入汇总", "DM经营分析看板", "PROCESS", "AST+AI", "spark-sql UNION多源汇总"),
            ("DWS营销效果汇总", "DM经营分析看板", "PROCESS", "AST", "spark-sql UNION多源汇总"),
            # ---- 出湖阶段 ----
            ("DM经营分析看板", "经营分析系统-看板", "OUTPUT", "API", "Sqoop导出"),
            ("DM收入财务表", "ES收入查询索引", "OUTPUT", "API", "DataX ES同步"),
            ("DM收入财务表", "财务报表行云文件", "OUTPUT", "API", "行云文件导出"),
            ("DM用户画像表", "用户画像API", "OUTPUT", "API", "API网关发布"),
        ]

        edge_ids = []
        for src_name, tgt_name, stage, method, program in edges:
            eid = uid()
            edge_ids.append(eid)
            conn.execute(
                text("""INSERT IGNORE INTO lineage_edge
                        (edge_id, source_node_id, target_node_id, lineage_stage, lineage_type, source_program, parse_method, collect_method, confidence, status, create_time, update_time)
                        VALUES (:eid, :src, :tgt, :stage, 'TABLE', :prog, :parse, :method, 0.98, 1, :now, :now)"""),
                {
                    "eid": eid,
                    "src": node_map[src_name],
                    "tgt": node_map[tgt_name],
                    "stage": stage,
                    "prog": program,
                    "parse": method,
                    "method": "DB" if stage == "INGEST" else "",
                    "now": NOW,
                },
            )

        # ========== 4. 节点字段 ==========
        def coldef(nid_key, col, cn, typ, ord, pk=0, fk=0):
            return {"id": uid(), "nid": node_map[nid_key], "col": col, "cn": cn, "type": typ, "ord": ord, "pk": pk, "fk": fk}

        columns = [
            # ---- ODS用户表 (ods_crm_user) ----
            coldef("ODS用户表", "user_id", "用户ID", "BIGINT", 1, pk=1),
            coldef("ODS用户表", "user_name", "用户姓名", "VARCHAR(64)", 2),
            coldef("ODS用户表", "id_card", "身份证号", "VARCHAR(18)", 3),
            coldef("ODS用户表", "phone", "手机号", "VARCHAR(11)", 4),
            coldef("ODS用户表", "open_time", "开户时间", "DATETIME", 5),
            # ---- ODS账户表 (ods_crm_account) ----
            coldef("ODS账户表", "account_id", "账户ID", "BIGINT", 1, pk=1),
            coldef("ODS账户表", "user_id", "用户ID", "BIGINT", 2, fk=1),
            coldef("ODS账户表", "balance", "余额", "DECIMAL(12,2)", 3),
            coldef("ODS账户表", "account_type", "账户类型", "VARCHAR(16)", 4),
            # ---- ODS通话详单 (ods_bill_cdr) ----
            coldef("ODS通话详单", "cdr_id", "详单ID", "BIGINT", 1, pk=1),
            coldef("ODS通话详单", "caller_phone", "主叫号码", "VARCHAR(11)", 2),
            coldef("ODS通话详单", "callee_phone", "被叫号码", "VARCHAR(11)", 3),
            coldef("ODS通话详单", "call_duration", "通话时长(s)", "INT", 4),
            coldef("ODS通话详单", "call_time", "通话时间", "DATETIME", 5),
            coldef("ODS通话详单", "fee", "通话费用", "DECIMAL(10,2)", 6),
            # ---- ODS账单表 (ods_bill_monthly) ----
            coldef("ODS账单表", "bill_id", "账单ID", "BIGINT", 1, pk=1),
            coldef("ODS账单表", "user_id", "用户ID", "BIGINT", 2, fk=1),
            coldef("ODS账单表", "bill_month", "账期月份", "VARCHAR(7)", 3),
            coldef("ODS账单表", "total_fee", "总费用", "DECIMAL(12,2)", 4),
            coldef("ODS账单表", "voice_fee", "语音费用", "DECIMAL(12,2)", 5),
            coldef("ODS账单表", "data_fee", "流量费用", "DECIMAL(12,2)", 6),
            # ---- DWD用户账户宽表 (dwd_user_account_df) ----
            coldef("DWD用户账户宽表", "dwd_id", "宽表ID", "BIGINT", 1, pk=1),
            coldef("DWD用户账户宽表", "user_id", "用户ID", "BIGINT", 2),
            coldef("DWD用户账户宽表", "user_name", "用户姓名", "VARCHAR(64)", 3),
            coldef("DWD用户账户宽表", "account_id", "账户ID", "BIGINT", 4),
            coldef("DWD用户账户宽表", "balance", "余额", "DECIMAL(12,2)", 5),
            coldef("DWD用户账户宽表", "account_type", "账户类型", "VARCHAR(16)", 6),
            coldef("DWD用户账户宽表", "phone", "手机号", "VARCHAR(11)", 7),
            # ---- DWD账单明细 (dwd_bill_detail_df) ----
            coldef("DWD账单明细", "detail_id", "明细ID", "BIGINT", 1, pk=1),
            coldef("DWD账单明细", "user_id", "用户ID", "BIGINT", 2),
            coldef("DWD账单明细", "amount", "金额", "DECIMAL(12,2)", 3),
            coldef("DWD账单明细", "fee_type", "费用类型", "VARCHAR(32)", 4),
            coldef("DWD账单明细", "bill_month", "账期月份", "VARCHAR(7)", 5),
            coldef("DWD账单明细", "call_duration", "通话时长", "INT", 6),
            # ---- DWS用户汇总 (dws_user_daily_sum) ----
            coldef("DWS用户汇总", "stat_date", "统计日期", "DATE", 1),
            coldef("DWS用户汇总", "user_id", "用户ID", "BIGINT", 2),
            coldef("DWS用户汇总", "user_name", "用户姓名", "VARCHAR(64)", 3),
            coldef("DWS用户汇总", "total_balance", "总余额", "DECIMAL(14,2)", 4),
            coldef("DWS用户汇总", "order_count", "订单数", "INT", 5),
            coldef("DWS用户汇总", "total_call_duration", "总通话时长", "BIGINT", 6),
            # ---- DWS收入汇总 (dws_revenue_daily_sum) ----
            coldef("DWS收入汇总", "stat_date", "统计日期", "DATE", 1),
            coldef("DWS收入汇总", "revenue_type", "收入类型", "VARCHAR(32)", 2),
            coldef("DWS收入汇总", "amount", "金额", "DECIMAL(14,2)", 3),
            coldef("DWS收入汇总", "user_count", "用户数", "BIGINT", 4),
            # ---- DWS营销效果汇总 (dws_mkt_effect_daily_sum) ----
            coldef("DWS营销效果汇总", "stat_date", "统计日期", "DATE", 1),
            coldef("DWS营销效果汇总", "campaign_id", "营销活动ID", "BIGINT", 2),
            coldef("DWS营销效果汇总", "total_amount", "总金额", "DECIMAL(14,2)", 3),
            coldef("DWS营销效果汇总", "order_count", "订单数", "INT", 4),
            # ---- DM经营分析看板 (dm_business_board) ----
            coldef("DM经营分析看板", "stat_date", "统计日期", "DATE", 1),
            coldef("DM经营分析看板", "total_revenue", "总收入", "DECIMAL(14,2)", 2),
            coldef("DM经营分析看板", "voice_revenue", "语音收入", "DECIMAL(12,2)", 3),
            coldef("DM经营分析看板", "broadband_revenue", "宽带收入", "DECIMAL(12,2)", 4),
            coldef("DM经营分析看板", "total_user_count", "总用户数", "BIGINT", 5),
            coldef("DM经营分析看板", "active_user_count", "活跃用户数", "BIGINT", 6),
            # ---- DM收入财务表 (dm_income_financial) ----
            coldef("DM收入财务表", "report_month", "报表月份", "VARCHAR(7)", 1),
            coldef("DM收入财务表", "total_revenue", "总收入", "DECIMAL(14,2)", 2),
            coldef("DM收入财务表", "voice_revenue", "语音收入", "DECIMAL(12,2)", 3),
            coldef("DM收入财务表", "broadband_revenue", "宽带收入", "DECIMAL(12,2)", 4),
            coldef("DM收入财务表", "value_added_revenue", "增值业务收入", "DECIMAL(12,2)", 5),
            # ---- DM用户画像表 (dm_user_portrait) ----
            coldef("DM用户画像表", "user_id", "用户ID", "BIGINT", 1, pk=1),
            coldef("DM用户画像表", "user_name", "用户姓名", "VARCHAR(64)", 2),
            coldef("DM用户画像表", "age_group", "年龄段", "VARCHAR(16)", 3),
            coldef("DM用户画像表", "package_type", "套餐类型", "VARCHAR(32)", 4),
            coldef("DM用户画像表", "arpu_level", "ARPU等级", "VARCHAR(16)", 5),
            coldef("DM用户画像表", "churn_risk", "流失风险分", "DECIMAL(3,2)", 6),
        ]

        for col in columns:
            conn.execute(
                text("""INSERT IGNORE INTO lineage_node_column
                        (column_id, node_id, column_name, column_cn_name, column_type, column_order, is_pk, is_fk, status, create_time, update_time)
                        VALUES (:cid, :nid, :col, :cn, :type, :ord, :pk, :fk, 1, :now, :now)"""),
                {"cid": col["id"], "nid": col["nid"], "col": col["col"], "cn": col["cn"], "type": col["type"], "ord": col["ord"], "pk": col["pk"], "fk": col["fk"], "now": NOW},
            )

        # ========== 5. 算子级血缘边 (OPERATOR) ==========
        operator_edges = [
            ("ODS用户表", "DWD用户账户宽表", "PROCESS", "JOIN", "JOIN(user_id)", 1.00),
            ("ODS账户表", "DWD用户账户宽表", "PROCESS", "JOIN", "JOIN(user_id)", 1.00),
            ("ODS通话详单", "DWD账单明细", "PROCESS", "UNION_ALL", "UNION ALL(通联合并)", 0.98),
            ("ODS账单表", "DWD账单明细", "PROCESS", "UNION_ALL", "UNION ALL(通联合并)", 0.98),
            ("DWD用户账户宽表", "DWS用户汇总", "PROCESS", "AGGREGATE", "GROUP BY(user_id)", 1.00),
            ("DWD账单明细", "DWS收入汇总", "PROCESS", "AGGREGATE", "SUM(amount) GROUP BY(revenue_type)", 1.00),
            ("DWD账单明细", "DWS收入汇总", "PROCESS", "AGGREGATE", "COUNT(DISTINCT user_id) GROUP BY(revenue_type)", 0.95),
            ("DWS收入汇总", "DM经营分析看板", "PROCESS", "SELECT", "INSERT OVERWRITE SELECT", 0.98),
            ("DWS收入汇总", "DM收入财务表", "PROCESS", "SELECT", "INSERT OVERWRITE SELECT", 0.98),
            ("DWS用户汇总", "DM经营分析看板", "PROCESS", "AGGREGATE", "SUM/COUNT GROUP BY(stat_date)", 0.95),
            ("DWS用户汇总", "DM用户画像表", "OUTPUT", "JOIN", "JOIN(多维度打标签)", 0.95),
        ]
        for src_name, tgt_name, stage, operator, program, conf in operator_edges:
            conn.execute(
                text("""INSERT IGNORE INTO lineage_edge
                        (edge_id, source_node_id, target_node_id, lineage_stage, lineage_type, source_program, parse_method, confidence, status, create_time, update_time)
                        VALUES (:eid, :src, :tgt, :stage, 'OPERATOR', :prog, 'AST', :conf, 1, :now, :now)"""),
                {
                    "eid": uid(),
                    "src": node_map[src_name],
                    "tgt": node_map[tgt_name],
                    "stage": stage,
                    "prog": program,
                    "conf": conf,
                    "now": NOW,
                },
            )

        # ========== 6. 字段级血缘边 (COLUMN) + lineage_column_edge 明细 ==========
        # 6a. 构建 column_id 映射: (node_id, column_name) → column_id
        col_map = {}
        for col in columns:
            col_map[(col["nid"], col["col"])] = col["id"]

        # 6b. 为每个需要字段级映射的表对创建 COLUMN 类型的 lineage_edge
        col_edge_groups = [
            # ODS用户表 → DWD用户账户宽表
            ("ODS用户表", "DWD用户账户宽表", "PROCESS",
             [("user_id", "user_id", "DIRECT"),
              ("user_name", "user_name", "DIRECT")]),
            # ODS账户表 → DWD用户账户宽表
            ("ODS账户表", "DWD用户账户宽表", "PROCESS",
             [("account_id", "account_id", "DIRECT"),
              ("balance", "balance", "DIRECT")]),
            # ODS通话详单 → DWD账单明细
            ("ODS通话详单", "DWD账单明细", "PROCESS",
             [("call_duration", "call_duration", "DIRECT"),
              ("fee", "amount", "DIRECT")]),
            # ODS账单表 → DWD账单明细
            ("ODS账单表", "DWD账单明细", "PROCESS",
             [("total_fee", "amount", "COALESCE(total_fee, 0)")]),
            # DWD账单明细 → DWS收入汇总
            ("DWD账单明细", "DWS收入汇总", "PROCESS",
             [("amount", "amount", "SUM(amount) GROUP BY revenue_type"),
              ("user_id", "user_count", "COUNT(DISTINCT user_id)")]),
            # DWD用户账户宽表 → DWS用户汇总
            ("DWD用户账户宽表", "DWS用户汇总", "PROCESS",
             [("user_id", "user_id", "DIRECT"),
              ("user_name", "user_name", "DIRECT"),
              ("balance", "total_balance", "SUM(balance) GROUP BY user_id")]),
            # DWS收入汇总 → DM收入财务表
            ("DWS收入汇总", "DM收入财务表", "PROCESS",
             [("amount", "total_revenue", "SUM(amount) GROUP BY report_month"),
              ("revenue_type", "voice_revenue", "CASE WHEN revenue_type='VOICE' THEN amount END"),
              ("revenue_type", "broadband_revenue", "CASE WHEN revenue_type='BROADBAND' THEN amount END"),
              ("revenue_type", "value_added_revenue", "CASE WHEN revenue_type='VALUE_ADDED' THEN amount END")]),
            # DWS收入汇总 → DM经营分析看板
            ("DWS收入汇总", "DM经营分析看板", "PROCESS",
             [("amount", "total_revenue", "SUM(amount)"),
              ("revenue_type", "voice_revenue", "CASE WHEN revenue_type='VOICE' THEN SUM(amount) END"),
              ("revenue_type", "broadband_revenue", "CASE WHEN revenue_type='BROADBAND' THEN SUM(amount) END"),
              ("user_count", "total_user_count", "SUM(user_count)")]),
            # DWS用户汇总 → DM用户画像表
            ("DWS用户汇总", "DM用户画像表", "PROCESS",
             [("user_id", "user_id", "DIRECT"),
              ("user_name", "user_name", "DIRECT")]),
            # DWS用户汇总 → DM经营分析看板
            ("DWS用户汇总", "DM经营分析看板", "PROCESS",
             [("total_balance", "total_revenue", "SUM(total_balance)"),
              ("order_count", "active_user_count", "SUM(order_count)")]),
        ]

        # Operator detail per mapping type
        operator_detail_map = {
            "DIRECT":         '{"operator_types":["DIRECT"], "detail":"Direct field assignment"}',
            "SUM":            '{"operator_types":["AGGREGATE"], "detail":"SUM aggregation"}',
            "COUNT":          '{"operator_types":["AGGREGATE"], "detail":"COUNT distinct aggregation"}',
            "CASE_WHEN":      '{"operator_types":["CASE_WHEN"], "detail":"CASE WHEN conditional mapping"}',
            "COALESCE":       '{"operator_types":["FUNCTION"], "detail":"COALESCE null handling"}',
        }

        def get_op_detail(expr):
            if "CASE WHEN" in expr:
                return operator_detail_map["CASE_WHEN"]
            if "SUM" in expr and "GROUP BY" in expr:
                return '{"operator_types":["AGGREGATE","GROUP_BY"], "detail":"' + expr.replace('"', "'") + '"}'
            if "SUM" in expr:
                return operator_detail_map["SUM"]
            if "COUNT" in expr:
                return operator_detail_map["COUNT"]
            if "COALESCE" in expr:
                return operator_detail_map["COALESCE"]
            if expr == "DIRECT":
                return operator_detail_map["DIRECT"]
            return '{"operator_types":["FUNCTION"], "detail":"' + expr.replace('"', "'") + '"}'

        for src_name, tgt_name, stage, mappings in col_edge_groups:
            ceid = uid()
            conn.execute(
                text("""INSERT IGNORE INTO lineage_edge
                        (edge_id, source_node_id, target_node_id, lineage_stage, lineage_type, parse_method, confidence, status, create_time, update_time)
                        VALUES (:eid, :src, :tgt, :stage, 'COLUMN', 'AST', 0.96, 1, :now, :now)"""),
                {"eid": ceid, "src": node_map[src_name], "tgt": node_map[tgt_name], "stage": stage, "now": NOW},
            )
            # Insert individual column mappings
            for src_col, tgt_col, expr in mappings:
                src_id = col_map.get((node_map[src_name], src_col))
                tgt_id = col_map.get((node_map[tgt_name], tgt_col))
                if src_id and tgt_id:
                    conn.execute(
                        text("""INSERT IGNORE INTO lineage_column_edge
                                (column_edge_id, edge_id, source_column_id, target_column_id, transform_expr, operator_detail, parse_method, confidence, status, create_time, update_time)
                                VALUES (:ceid, :eid, :src, :tgt, :expr, :od, 'AST', 0.96, 1, :now, :now)"""),
                        {"ceid": uid(), "eid": ceid, "src": src_id, "tgt": tgt_id, "expr": expr, "od": get_op_detail(expr), "now": NOW},
                    )

        # ========== 7. AI调用配置 ==========
        ai_configs = [
            {
                "config_id": "SQL_EXTRACT_DEFAULT",
                "ai_capability": "SQL_EXTRACT",
                "model_name": "claude-sonnet-4-6",
                "api_endpoint": "https://api.example.com/v1/chat/completions",
                "api_key": "",
                "max_tokens": 4096,
                "temperature": 0.1,
                "timeout_ms": 30000,
                "retry_count": 2,
                "enabled": 1,
            },
            {
                "config_id": "LINEAGE_PARSE_DEFAULT",
                "ai_capability": "LINEAGE_PARSE",
                "model_name": "claude-sonnet-4-6",
                "api_endpoint": "https://api.example.com/v1/chat/completions",
                "api_key": "",
                "max_tokens": 4096,
                "temperature": 0.1,
                "timeout_ms": 30000,
                "retry_count": 2,
                "enabled": 1,
            },
        ]
        for c in ai_configs:
            conn.execute(
                text("""INSERT IGNORE INTO ai_call_config
                        (config_id, ai_capability, model_name, api_endpoint, api_key, max_tokens, temperature, timeout_ms, retry_count, enabled, create_time, update_time)
                        VALUES (:config_id, :ai_capability, :model_name, :api_endpoint, :api_key, :max_tokens, :temperature, :timeout_ms, :retry_count, :enabled, :now, :now)"""),
                {**c, "now": NOW},
            )

        print("=" * 50)
        print("种子数据写入完成！")
        print(f"  集群: {len(clusters)} 个")
        print(f"  节点: {len(nodes)} 个")
        print(f"  血缘边(TABLE): {len(edges)} 条")
        print(f"  血缘边(OPERATOR): {len(operator_edges)} 条")
        col_edge_count = sum(len(m[3]) for m in col_edge_groups)
        print(f"  血缘边(COLUMN): {col_edge_count} 条关联")
        print(f"  节点字段: {len(columns)} 个")
        print(f"  AI配置: {len(ai_configs)} 个")
        print("=" * 50)
        print("\n分析粒度测试:")
        print("  - 表级:    lineage_type=TABLE   → 查看表间依赖")
        print("  - 字段级:  lineage_type=COLUMN  → 查看字段映射关系+转换表达式")
        print("  - 算子级:  lineage_type=OPERATOR → 查看数据经过的算子(JOIN/AGGREGATE/SELECT)")
        print("  - 全部:    lineage_type=ALL      → 查看完整血缘")
        print("\n推荐搜索表名:")
        print("  - dm_income_financial   (收入财务表，全链路)")
        print("  - dm_user_portrait       (用户画像表)")
        print("  - dm_business_board      (经营分析看板)")
        print("  - ods_crm_user           (ODS用户表)")
        print("  - dws_revenue_daily_sum  (收入日汇总)")


def uid() -> str:
    return uuid.uuid4().hex[:16]


if __name__ == "__main__":
    # 先确保 pymysql 已安装
    try:
        import pymysql  # noqa
    except ImportError:
        print("请先安装 pymysql: pip install pymysql")
        exit(1)
    run()
