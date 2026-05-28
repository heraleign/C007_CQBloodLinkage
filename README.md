# 数据全生命周期血缘可视化管理平台

基于《数据全生命周期流转可视化管理》技术规范书实现的完整前后端分离项目。

## 技术栈

| 层次 | 技术 | 说明 |
|------|------|------|
| 后端框架 | Python FastAPI | 异步高性能 Web 框架 |
| 数据库 | MySQL + Neo4j | 关系型存储 + 图数据库 |
| ORM | SQLAlchemy 2.0 (async) | 异步 ORM + Alembic 迁移 |
| 前端 | Vue 3 + Vite | Composition API |
| 可视化 | AntV G6 | 血缘 DAG 图渲染 |
| UI 库 | Element Plus | 后台管理 UI 组件 |
| 状态管理 | Pinia | Vue 3 状态管理 |
| SQL 解析 | sqlparse | SQL 血缘提取引擎 |
| AI | LLM API | AI 辅助 SQL 提取与血缘补充 |
| 调度 | APScheduler | 定时任务（入湖同步/日志解析） |
| 导出 | openpyxl + python-docx | Excel/Word 导出 |

## 项目结构

```
C007_CQBloodLinkage/
├── backend/                     # Python 后端
│   ├── app/
│   │   ├── api/v1/              # RESTful API 端点
│   │   ├── core/                # 配置、数据库、安全
│   │   ├── models/              # SQLAlchemy ORM 模型 (12表)
│   │   ├── schemas/             # Pydantic 请求/响应模型
│   │   ├── services/            # 业务逻辑层
│   │   │   ├── parsing/         # SQL解析引擎 + AI融合
│   │   │   ├── export_service.py
│   │   │   ├── log_collector.py
│   │   │   └── neo4j_service.py
│   │   ├── tasks/               # APScheduler 定时任务
│   │   └── main.py              # FastAPI 入口
│   ├── alembic/                 # 数据库迁移
│   ├── tests/                   # 单元测试
│   ├── requirements.txt
│   └── run.py
│
├── frontend/                    # Vue 3 前端
│   ├── src/
│   │   ├── api/                 # Axios API 封装
│   │   ├── components/graph/    # AntV G6 图谱组件
│   │   ├── router/              # 路由配置
│   │   ├── stores/              # Pinia 状态管理
│   │   └── views/               # 页面视图
│   │       ├── lineage/         # 血缘分析/全景/治理/导出
│   │       ├── atom/            # 原子能力
│   │       └── admin/           # 系统管理
│   ├── package.json
│   └── vite.config.js
│
└── README.md
```

## 快速开始

### 前置条件

- Python 3.12+
- Node.js 18+
- MySQL 8.0+
- Neo4j 5.x（可选，图谱查询优化）

### 后端启动

```bash
# 1. 进入后端目录
cd backend

# 2. 创建并激活虚拟环境
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 配置数据库连接
# 编辑 .env 文件，修改 DB_HOST/DB_USER/DB_PASSWORD/DB_DATABASE

# 5. 创建数据库
mysql -u root -p -e "CREATE DATABASE IF NOT EXISTS lineage CHARACTER SET utf8mb4"

# 6. 运行数据库迁移
alembic upgrade head

# 7. 启动服务
python run.py
# 服务运行于 http://127.0.0.1:8000
```

### 前端启动

```bash
# 1. 进入前端目录
cd frontend

# 2. 安装依赖
npm install

# 3. 启动开发服务器
npm run dev
# 服务运行于 http://127.0.0.1:5173
```

### 运行测试

```bash
cd backend
source venv/Scripts/activate   # 或 venv\Scripts\activate
python -m pytest tests/ -v
```

## API 概览

所有 API 以 `/api/v1/` 为前缀。

| 端点 | 说明 |
|------|------|
| `GET /health` | 健康检查 |
| `GET /api/v1/nodes/` | 血缘节点列表 |
| `POST /api/v1/nodes/` | 创建节点 |
| `PUT /api/v1/nodes/{id}` | 更新节点 |
| `DELETE /api/v1/nodes/{id}` | 删除节点 |
| `GET /api/v1/nodes/{id}/columns` | 节点字段列表 |
| `GET /api/v1/edges/` | 血缘边列表 |
| `POST /api/v1/edges/` | 创建边 |
| `DELETE /api/v1/edges/{id}` | 删除边 |
| `POST /api/v1/analysis/query` | 血缘图谱查询 |
| `GET /api/v1/analysis/search` | 表名模糊搜索 |
| `GET /api/v1/analysis/systems` | 系统列表 |
| `POST /api/v1/ingest/sync` | 手动触发入湖同步 |
| `POST /api/v1/export/preview` | 导出预览 |
| `POST /api/v1/export/execute` | 执行导出 |
| `POST /api/v1/atom/parse-table-lineage` | SQL表级血缘解析 |
| `POST /api/v1/atom/parse-column-lineage` | SQL字段级血缘解析 |
| `POST /api/v1/atom/parse-script-lineage` | Shell脚本血缘解析 |
| `POST /api/v1/atom/save-lineage` | 血缘入库 |
| `POST /api/v1/atom/query-lineage` | 血缘查询 |

## 能力清单

### 能力一：端到端全链路血缘贯通
- 对接数据汇聚系统 4 个接口（文件/数据库/Kafka/表结构）
- 自动生成入湖阶段血缘节点和边
- 统一血缘存储模型（MySQL + Neo4j）

### 能力二：持续提升数据血缘解析能力
- Shell 脚本 SQL 提取（spark-sql/beeline/hive/heredoc）
- 变量替换引擎
- AST 语法树解析 + AI 补充
- 多厂商适配器架构（天源迪科/思特奇/数派科技）

### 能力三：血缘链路完整性治理
- 表备注和字段备注管理
- 血缘链路完整性检查
- 权限管控（REMARK_VIEW/REMARK_EDIT/LINEAGE_ADMIN）

### 能力四：血缘分析查看能力
- 表名搜索、系统筛选、方向/层数控制
- AntV G6 DAG 图渲染
- 阶段着色（入湖蓝/加工绿/出湖橙）
- 节点详情抽屉

### 能力五：血缘适配 TDP 集群
- 集群注册管理
- 跨集群唯一表标识
- 跨集群血缘关联映射

### 能力六：数据血缘导出能力
- Excel 导出（表级血缘 + 节点详情多 Sheet）
- Word 导出（结构化血缘分析报告）
- 支持选择表、方向、层数、粒度

### 能力七：日志解析能力
- 文件系统日志采集器
- TDP 平台日志采集器
- SQL 提取与血缘合并
- 日志结果与静态解析结果冲突消解

### 能力八：原子能力服务
- ATOM_001: SQL 表级血缘解析
- ATOM_002: SQL 字段级血缘解析
- ATOM_003: Shell 脚本血缘解析
- ATOM_004: 血缘入库
- ATOM_005: 血缘查询
- ATOM_006: 血缘校验
- 单次解析页面（在线 SQL/脚本解析）

### 能力九：AI 赋能数据血缘
- AI 辅助 SQL 提取（从 Shell 脚本）
- AI 辅助血缘解析（从 SQL）
- AST+AI 结果融合引擎
- 置信度评分

## 环境变量

参考 `.env` 文件配置：

| 变量 | 默认值 | 说明 |
|------|--------|------|
| DB_HOST | localhost | MySQL 地址 |
| DB_PORT | 3306 | MySQL 端口 |
| DB_USER | root | MySQL 用户 |
| DB_PASSWORD | 123456 | MySQL 密码 |
| DB_DATABASE | lineage | MySQL 数据库名 |
| NEO4J_URI | bolt://127.0.0.1:7687 | Neo4j 地址 |
| NEO4J_USER | neo4j | Neo4j 用户 |
| NEO4J_PASSWORD | neo4j2026 | Neo4j 密码 |
| AI_API_ENDPOINT | https://... | AI 模型 API 地址 |
| AI_API_KEY | - | AI API 密钥 |
| AES_KEY | default...32bytes!! | 认证加密密钥 |
