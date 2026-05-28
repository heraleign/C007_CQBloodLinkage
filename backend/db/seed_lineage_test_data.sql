-- =============================================================================
-- 血缘分析测试数据（字段级 + 算子级）
-- 场景：用户订单分析管线
--   ods_orders ──┐
--                 ├─[JOIN]→ dwd_order_detail ──[AGGREGATE]→ dws_user_stats ──[SELECT]→ ads_order_report
--   ods_users  ──┘
-- =============================================================================
-- 使用方式: mysql -u root -p db_name < seed_lineage_test_data.sql

-- =============================================================================
-- 1. lineage_node: 血缘节点（表级）
-- =============================================================================
INSERT INTO lineage_node (node_id, node_type, node_name, node_unique_key, system_code, system_name, cluster_id, cluster_name, database_name, table_name, table_cn_name, table_remark, source_type, status, create_time, update_time) VALUES
-- 入湖层
('N_ODS_ORD_001', 'TABLE', 'ods_orders', 'CLICKHOUSE.analysis_cloud.ods_orders', 'CLICKHOUSE', 'ClickHouse实时数仓', 'CLUSTER_CH_001', 'ClickHouse主集群', 'analysis_cloud', 'ods_orders', '订单原始表', '订单业务原始数据，每日增量同步', 'SYNC', 1, NOW(), NOW()),
('N_ODS_USR_001', 'TABLE', 'ods_users', 'CLICKHOUSE.analysis_cloud.ods_users', 'CLICKHOUSE', 'ClickHouse实时数仓', 'CLUSTER_CH_001', 'ClickHouse主集群', 'analysis_cloud', 'ods_users', '用户原始表', '用户信息原始数据', 'SYNC', 1, NOW(), NOW()),

-- 湖内加工层
('N_DWD_OD_001', 'TABLE', 'dwd_order_detail', 'SPARK.analysis_cloud.dwd_order_detail', 'SPARK', 'Spark离线计算', 'CLUSTER_SPK_001', 'Spark计算集群', 'analysis_cloud', 'dwd_order_detail', '订单明细宽表', '订单与用户JOIN后的明细宽表', 'COMPUTE', 1, NOW(), NOW()),
('N_DWS_US_001', 'TABLE', 'dws_user_stats', 'SPARK.analysis_cloud.dws_user_stats', 'SPARK', 'Spark离线计算', 'CLUSTER_SPK_001', 'Spark计算集群', 'analysis_cloud', 'dws_user_stats', '用户统计汇总表', '按用户维度的聚合统计数据', 'COMPUTE', 1, NOW(), NOW()),

-- 出湖层
('N_ADS_OR_001', 'TABLE', 'ads_order_report', 'MYSQL.ads.ads_order_report', 'MYSQL', 'MySQL业务系统', 'CLUSTER_MYSQL_001', 'MySQL主库', 'ads', 'ads_order_report', '订单分析报表', 'BI报表数据，供可视化看板使用', 'EXPORT', 1, NOW(), NOW());

-- =============================================================================
-- 2. lineage_node_column: 字段定义
-- =============================================================================
INSERT INTO lineage_node_column (column_id, node_id, column_name, column_cn_name, column_type, column_order, status, create_time) VALUES
-- ods_orders 的字段
('COL_ODS_ORD_01', 'N_ODS_ORD_001', 'order_id', '订单ID', 'String', 1, 1, NOW()),
('COL_ODS_ORD_02', 'N_ODS_ORD_001', 'user_id', '用户ID', 'String', 2, 1, NOW()),
('COL_ODS_ORD_03', 'N_ODS_ORD_001', 'product_id', '产品ID', 'String', 3, 1, NOW()),
('COL_ODS_ORD_04', 'N_ODS_ORD_001', 'amount', '订单金额', 'Decimal(18,2)', 4, 1, NOW()),
('COL_ODS_ORD_05', 'N_ODS_ORD_001', 'order_time', '下单时间', 'DateTime', 5, 1, NOW()),
('COL_ODS_ORD_06', 'N_ODS_ORD_001', 'order_status', '订单状态', 'String', 6, 1, NOW()),

-- ods_users 的字段
('COL_ODS_USR_01', 'N_ODS_USR_001', 'user_id', '用户ID', 'String', 1, 1, NOW()),
('COL_ODS_USR_02', 'N_ODS_USR_001', 'user_name', '用户名称', 'String', 2, 1, NOW()),
('COL_ODS_USR_03', 'N_ODS_USR_001', 'user_email', '用户邮箱', 'String', 3, 1, NOW()),
('COL_ODS_USR_04', 'N_ODS_USR_001', 'register_time', '注册时间', 'DateTime', 4, 1, NOW()),
('COL_ODS_USR_05', 'N_ODS_USR_001', 'user_level', '用户等级', 'String', 5, 1, NOW()),

-- dwd_order_detail 的字段
('COL_DWD_OD_01', 'N_DWD_OD_001', 'order_id', '订单ID', 'String', 1, 1, NOW()),
('COL_DWD_OD_02', 'N_DWD_OD_001', 'user_id', '用户ID', 'String', 2, 1, NOW()),
('COL_DWD_OD_03', 'N_DWD_OD_001', 'product_id', '产品ID', 'String', 3, 1, NOW()),
('COL_DWD_OD_04', 'N_DWD_OD_001', 'amount', '订单金额', 'Decimal(18,2)', 4, 1, NOW()),
('COL_DWD_OD_05', 'N_DWD_OD_001', 'order_time', '下单时间', 'DateTime', 5, 1, NOW()),
('COL_DWD_OD_06', 'N_DWD_OD_001', 'user_name', '用户名称', 'String', 6, 1, NOW()),
('COL_DWD_OD_07', 'N_DWD_OD_001', 'user_email', '用户邮箱', 'String', 7, 1, NOW()),
('COL_DWD_OD_08', 'N_DWD_OD_001', 'order_status', '订单状态', 'String', 8, 1, NOW()),

-- dws_user_stats 的字段
('COL_DWS_US_01', 'N_DWS_US_001', 'user_id', '用户ID', 'String', 1, 1, NOW()),
('COL_DWS_US_02', 'N_DWS_US_001', 'user_name', '用户名称', 'String', 2, 1, NOW()),
('COL_DWS_US_03', 'N_DWS_US_001', 'total_amount', '总消费金额', 'Decimal(18,2)', 3, 1, NOW()),
('COL_DWS_US_04', 'N_DWS_US_001', 'order_count', '订单总数', 'Int', 4, 1, NOW()),
('COL_DWS_US_05', 'N_DWS_US_001', 'avg_amount', '平均订单金额', 'Decimal(18,2)', 5, 1, NOW()),
('COL_DWS_US_06', 'N_DWS_US_001', 'last_order_time', '最后下单时间', 'DateTime', 6, 1, NOW()),

-- ads_order_report 的字段
('COL_ADS_OR_01', 'N_ADS_OR_001', 'user_id', '用户ID', 'String', 1, 1, NOW()),
('COL_ADS_OR_02', 'N_ADS_OR_001', 'user_name', '用户名称', 'String', 2, 1, NOW()),
('COL_ADS_OR_03', 'N_ADS_OR_001', 'total_amount', '总消费金额', 'Decimal(18,2)', 3, 1, NOW()),
('COL_ADS_OR_04', 'N_ADS_OR_001', 'order_count', '订单总数', 'Int', 4, 1, NOW()),
('COL_ADS_OR_05', 'N_ADS_OR_001', 'report_date', '报表日期', 'Date', 5, 1, NOW());

-- =============================================================================
-- 3. lineage_edge: 血缘边（含表级、字段级、算子级）
-- =============================================================================
INSERT INTO lineage_edge (edge_id, source_node_id, target_node_id, lineage_stage, lineage_type, source_program, source_system, parse_method, collect_method, confidence, status, create_time, update_time) VALUES
-- 3a. 表级血缘 (TABLE): 表间依赖关系
('E_TBL_ODS2DWD', 'N_ODS_ORD_001', 'N_DWD_OD_001', 'PROCESS', 'TABLE', 'spark_etl_order_detail.scala', 'SPARK', 'AST', 'FILE', 1.00, 1, NOW(), NOW()),
('E_TBL_USR2DWD', 'N_ODS_USR_001', 'N_DWD_OD_001', 'PROCESS', 'TABLE', 'spark_etl_order_detail.scala', 'SPARK', 'AST', 'FILE', 1.00, 1, NOW(), NOW()),
('E_TBL_DWD2DWS', 'N_DWD_OD_001', 'N_DWS_US_001', 'PROCESS', 'TABLE', 'spark_etl_user_stats.scala', 'SPARK', 'AST', 'FILE', 1.00, 1, NOW(), NOW()),
('E_TBL_DWS2ADS', 'N_DWS_US_001', 'N_ADS_OR_001', 'OUTPUT', 'TABLE', 'sync_ads_order_report.sh', 'SPARK', 'API', 'FILE', 1.00, 1, NOW(), NOW()),

-- 3b. 字段级血缘 (COLUMN): 字段间映射关系
('E_COL_ORDID',    'N_ODS_ORD_001', 'N_DWD_OD_001', 'PROCESS', 'COLUMN', 'spark_etl_order_detail.scala', 'SPARK', 'AST', 'FILE', 1.00, 1, NOW(), NOW()),
('E_COL_USRID',    'N_ODS_ORD_001', 'N_DWD_OD_001', 'PROCESS', 'COLUMN', 'spark_etl_order_detail.scala', 'SPARK', 'AST', 'FILE', 1.00, 1, NOW(), NOW()),
('E_COL_PRODID',   'N_ODS_ORD_001', 'N_DWD_OD_001', 'PROCESS', 'COLUMN', 'spark_etl_order_detail.scala', 'SPARK', 'AST', 'FILE', 1.00, 1, NOW(), NOW()),
('E_COL_AMT',      'N_ODS_ORD_001', 'N_DWD_OD_001', 'PROCESS', 'COLUMN', 'spark_etl_order_detail.scala', 'SPARK', 'AST', 'FILE', 1.00, 1, NOW(), NOW()),
('E_COL_UNAME',    'N_ODS_USR_001', 'N_DWD_OD_001', 'PROCESS', 'COLUMN', 'spark_etl_order_detail.scala', 'SPARK', 'AST', 'FILE', 1.00, 1, NOW(), NOW()),
('E_COL_UEMAIL',   'N_ODS_USR_001', 'N_DWD_OD_001', 'PROCESS', 'COLUMN', 'spark_etl_order_detail.scala', 'SPARK', 'AST', 'FILE', 1.00, 1, NOW(), NOW()),
('E_COL_DWS_UID',  'N_DWD_OD_001', 'N_DWS_US_001', 'PROCESS', 'COLUMN', 'spark_etl_user_stats.scala', 'SPARK', 'AST', 'FILE', 1.00, 1, NOW(), NOW()),
('E_COL_DWS_AMT',  'N_DWD_OD_001', 'N_DWS_US_001', 'PROCESS', 'COLUMN', 'spark_etl_user_stats.scala', 'SPARK', 'AST', 'FILE', 1.00, 1, NOW(), NOW()),
('E_COL_ADS_UID',  'N_DWS_US_001', 'N_ADS_OR_001', 'OUTPUT', 'COLUMN', 'sync_ads_order_report.sh', 'SPARK', 'API', 'FILE', 1.00, 1, NOW(), NOW()),
('E_COL_ADS_AMT',  'N_DWS_US_001', 'N_ADS_OR_001', 'OUTPUT', 'COLUMN', 'sync_ads_order_report.sh', 'SPARK', 'API', 'FILE', 1.00, 1, NOW(), NOW()),
('E_COL_ADS_CNT',  'N_DWS_US_001', 'N_ADS_OR_001', 'OUTPUT', 'COLUMN', 'sync_ads_order_report.sh', 'SPARK', 'API', 'FILE', 1.00, 1, NOW(), NOW()),

-- 3c. 算子级血缘 (OPERATOR): 数据经过的算子处理
('E_OP_JOIN',      'N_ODS_ORD_001', 'N_DWD_OD_001', 'PROCESS', 'OPERATOR', 'JOIN', 'SPARK', 'AST', 'FILE', 1.00, 1, NOW(), NOW()),
('E_OP_JOIN_USR',  'N_ODS_USR_001', 'N_DWD_OD_001', 'PROCESS', 'OPERATOR', 'JOIN', 'SPARK', 'AST', 'FILE', 1.00, 1, NOW(), NOW()),
('E_OP_AGG',       'N_DWD_OD_001', 'N_DWS_US_001', 'PROCESS', 'OPERATOR', 'AGGREGATE', 'SPARK', 'AST', 'FILE', 1.00, 1, NOW(), NOW()),
('E_OP_SELECT',    'N_DWS_US_001', 'N_ADS_OR_001', 'OUTPUT', 'OPERATOR', 'SELECT', 'SPARK', 'API', 'FILE', 1.00, 1, NOW(), NOW());

-- =============================================================================
-- 4. lineage_column_edge: 字段级血缘明细（字段→字段映射 + 转换表达式）
-- =============================================================================
INSERT INTO lineage_column_edge (column_edge_id, edge_id, source_column_id, target_column_id, transform_expr, parse_method, confidence, status, create_time, update_time) VALUES
-- ods_orders → dwd_order_detail 字段映射
('CE_ORDID',   'E_COL_ORDID',  'COL_ODS_ORD_01', 'COL_DWD_OD_01', 'order_id', 'AST', 1.00, 1, NOW(), NOW()),
('CE_USRID',   'E_COL_USRID',  'COL_ODS_ORD_02', 'COL_DWD_OD_02', 'user_id', 'AST', 1.00, 1, NOW(), NOW()),
('CE_PRODID',  'E_COL_PRODID', 'COL_ODS_ORD_03', 'COL_DWD_OD_03', 'product_id', 'AST', 1.00, 1, NOW(), NOW()),
('CE_AMT',     'E_COL_AMT',    'COL_ODS_ORD_04', 'COL_DWD_OD_04', 'amount', 'AST', 1.00, 1, NOW(), NOW()),

-- ods_users → dwd_order_detail 字段映射
('CE_UNAME',   'E_COL_UNAME',  'COL_ODS_USR_02', 'COL_DWD_OD_06', 'user_name', 'AST', 1.00, 1, NOW(), NOW()),
('CE_UEMAIL',  'E_COL_UEMAIL', 'COL_ODS_USR_03', 'COL_DWD_OD_07', 'user_email', 'AST', 1.00, 1, NOW(), NOW()),

-- dwd_order_detail → dws_user_stats 字段映射（含聚合表达式）
('CE_DWS_UID', 'E_COL_DWS_UID', 'COL_DWD_OD_02', 'COL_DWS_US_01', 'user_id', 'AST', 1.00, 1, NOW(), NOW()),
('CE_DWS_AMT', 'E_COL_DWS_AMT', 'COL_DWD_OD_04', 'COL_DWS_US_03', 'SUM(amount) AS total_amount', 'AST', 1.00, 1, NOW(), NOW()),

-- dws_user_stats → ads_order_report 字段映射
('CE_ADS_UID', 'E_COL_ADS_UID', 'COL_DWS_US_01', 'COL_ADS_OR_01', 'user_id', 'AST', 1.00, 1, NOW(), NOW()),
('CE_ADS_AMT', 'E_COL_ADS_AMT', 'COL_DWS_US_03', 'COL_ADS_OR_03', 'total_amount', 'AST', 1.00, 1, NOW(), NOW()),
('CE_ADS_CNT', 'E_COL_ADS_CNT', 'COL_DWS_US_04', 'COL_ADS_OR_04', 'order_count', 'AST', 1.00, 1, NOW(), NOW());
