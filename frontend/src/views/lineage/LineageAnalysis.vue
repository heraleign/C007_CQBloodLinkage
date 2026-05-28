<template>
  <div class="lineage-analysis">
    <el-card shadow="never" class="search-card">
      <el-form :model="queryForm" inline>
        <el-form-item label="归属系统">
          <el-select
            v-model="queryForm.systemCode"
            placeholder="全部"
            clearable
            style="width: 160px"
          >
            <el-option
              v-for="s in store.systems"
              :key="s.code"
              :label="s.name"
              :value="s.code"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="归属集群">
          <el-select
            v-model="queryForm.clusterId"
            placeholder="全部"
            clearable
            style="width: 160px"
          >
            <el-option
              v-for="c in store.clusters"
              :key="c.cluster_id"
              :label="c.cluster_name"
              :value="c.cluster_id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="表名">
          <el-autocomplete
            v-model="queryForm.tableName"
            :fetch-suggestions="searchTables"
            placeholder="输入表名搜索"
            style="width: 240px"
            clearable
          />
        </el-form-item>
        <el-form-item label="分析方向">
          <el-radio-group v-model="queryForm.direction">
            <el-radio value="UPSTREAM">上游</el-radio>
            <el-radio value="DOWNSTREAM">下游</el-radio>
            <el-radio value="BOTH">全部</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="分析层数">
          <el-select v-model="queryForm.depth" style="width: 100px">
            <el-option v-for="n in 10" :key="n" :label="n" :value="n" />
          </el-select>
        </el-form-item>
        <el-form-item label="分析粒度">
          <el-radio-group v-model="queryForm.lineageType">
            <el-radio value="TABLE">表级</el-radio>
            <el-radio value="COLUMN">字段级</el-radio>
            <el-radio value="OPERATOR">算子级</el-radio>
            <el-radio value="ALL">全部</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="doQuery" :loading="store.loading">
            <el-icon><Search /></el-icon> 开始分析
          </el-button>
          <el-button @click="resetQuery">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card shadow="never" class="graph-card" v-if="store.centerNode">
      <div class="graph-toolbar">
        <span class="graph-title">
          血缘图谱：{{ store.centerNode.table_name || store.centerNode.node_name }}
          <el-tag size="small" type="info" class="node-count-tag">
            共 {{ graphNodes.length }} 个节点 / {{ graphEdges.length }} 条边
          </el-tag>
        </span>
        <div class="stage-legend">
          <template v-if="queryForm.lineageType === 'COLUMN'">
            <span class="legend-item"><span class="dot direct-edge"></span>直接映射</span>
            <span class="legend-item"><span class="dot agg-edge"></span>聚合计算</span>
            <span class="legend-item"><span class="dot case-edge"></span>条件映射</span>
          </template>
          <template v-else-if="queryForm.lineageType === 'OPERATOR'">
            <span class="legend-item"><span class="dot table-node"></span>表节点</span>
            <span class="legend-item"><span class="dot operator-node"></span>算子节点</span>
          </template>
          <template v-else>
            <span class="legend-item"><span class="dot ingest"></span>入湖</span>
            <span class="legend-item"><span class="dot process"></span>加工</span>
            <span class="legend-item"><span class="dot output"></span>出湖</span>
            <span class="legend-divider"></span>
            <span class="legend-item"><span class="dot table-edge"></span>表级</span>
            <span class="legend-item"><span class="dot column-edge"></span>字段级</span>
            <span class="legend-item"><span class="dot operator-edge"></span>算子级</span>
          </template>
        </div>
        <el-button size="small" @click="store.clearGraph()">清除</el-button>
      </div>
      <div class="graph-container">
        <LineageCanvas
          :nodes="graphNodes"
          :edges="graphEdges"
          :center-node-id="store.centerNode?.node_id"
          :lineage-type="queryForm.lineageType"
          :active-field="activeField"
          @node-click="onNodeClick"
          @field-click="onFieldClick"
        />
      </div>
      <FieldOperatorPanel
        v-if="fieldDetailData"
        :field-data="fieldDetailData"
        @close="closeFieldPanel"
      />
    </el-card>

    <el-empty v-else description="请输入表名并点击「开始分析」" />

    <!-- Node Detail Drawer -->
    <el-drawer
      v-model="drawerVisible"
      :title="detailNode?.table_name || detailNode?.node_name || '节点详情'"
      size="400px"
    >
      <template v-if="detailNode">
        <el-descriptions :column="1" border size="small">
          <el-descriptions-item label="节点名称">{{ detailNode.node_name }}</el-descriptions-item>
          <el-descriptions-item label="节点类型">{{ detailNode.node_type }}</el-descriptions-item>
          <el-descriptions-item label="中文名">{{ detailNode.table_cn_name || '-' }}</el-descriptions-item>
          <el-descriptions-item label="归属系统">{{ detailNode.system_name || '-' }}</el-descriptions-item>
          <el-descriptions-item label="集群">{{ detailNode.cluster_name || '-' }}</el-descriptions-item>
          <el-descriptions-item label="数据库">{{ detailNode.database_name || '-' }}</el-descriptions-item>
          <el-descriptions-item label="表名">{{ detailNode.table_name || '-' }}</el-descriptions-item>
          <el-descriptions-item label="备注">{{ detailNode.table_remark || '-' }}</el-descriptions-item>
        </el-descriptions>
      </template>
    </el-drawer>

    <!-- Operator SQL Dialog (OPERATOR mode) -->
    <el-dialog
      v-model="operatorDialogVisible"
      :title="operatorDialogData ? operatorDialogData.fieldName + ' 计算逻辑' : '字段计算逻辑'"
      width="560px"
      top="10vh"
      destroy-on-close
    >
      <template v-if="operatorDialogData">
        <div style="margin-bottom:12px;font-size:13px;color:#333;">
          目标字段：<strong>{{ operatorDialogData.tableName }}.{{ operatorDialogData.fieldName }}</strong>
        </div>

        <div v-if="operatorDialogData.sourceFields.length > 0" style="margin-bottom:10px;">
          <div style="font-size:11px;color:#888;font-weight:600;margin-bottom:4px;">参与字段</div>
          <el-table :data="operatorDialogData.sourceFields" size="small" stripe border>
            <el-table-column prop="nodeName" label="来源表" min-width="100" />
            <el-table-column prop="columnName" label="字段名" min-width="90" />
            <el-table-column prop="columnType" label="类型" min-width="80" />
            <el-table-column prop="role" label="角色" min-width="70" />
          </el-table>
        </div>

        <div style="margin-bottom:10px;">
          <div style="font-size:11px;color:#888;font-weight:600;margin-bottom:4px;">加工逻辑（SQL）</div>
          <pre style="background:#f6f8fa;border:1px solid #e8e8e8;border-radius:4px;padding:10px;font-family:monospace;font-size:12px;line-height:1.5;white-space:pre-wrap;color:#333;max-height:200px;overflow-y:auto;margin:0;">{{ operatorDialogData.transformExpr }}</pre>
        </div>

        <div v-if="operatorDialogData.operatorTypes.length > 0" style="margin-bottom:10px;">
          <div style="font-size:11px;color:#888;font-weight:600;margin-bottom:4px;">算子类型</div>
          <div style="display:flex;gap:6px;flex-wrap:wrap;">
            <el-tag
              v-for="op in operatorDialogData.operatorTypes"
              :key="op"
              :type="op === 'AGGREGATE' ? 'success' : op === 'CASE_WHEN' ? 'warning' : ''"
              size="small"
            >{{ op }}</el-tag>
          </div>
        </div>

        <div style="display:flex;gap:20px;font-size:11px;color:#999;padding-top:8px;border-top:1px solid #f0f0f0;">
          <span>解析方式：{{ operatorDialogData.parseMethod }}</span>
          <span>置信度：{{ operatorDialogData.confidence ? (operatorDialogData.confidence * 100).toFixed(0) + '%' : '-' }}</span>
        </div>
      </template>
      <template #footer>
        <el-button @click="closeOperatorDialog">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { reactive, computed, ref, onMounted, watch } from 'vue'
import { useLineageStore } from '@/stores/lineage'
import { lineageApi } from '@/api/lineage'
import LineageCanvas from '@/components/graph/LineageCanvas.vue'
import FieldOperatorPanel from '@/components/graph/FieldOperatorPanel.vue'

const store = useLineageStore()

const queryForm = reactive({
  systemCode: null,
  clusterId: null,
  tableName: '',
  direction: 'BOTH',
  depth: 3,
  lineageType: 'TABLE',
})

const drawerVisible = ref(false)
const detailNode = ref(null)
const activeField = ref(null)        // { nodeId, fieldIndex } for highlight
const fieldDetailData = ref(null)     // data for FieldOperatorPanel

// ---- Lookups ----
const columnMap = computed(() => {
  const m = {}
  store.nodeColumns.forEach((c) => { m[c.column_id] = c })
  return m
})

const fieldsByNode = computed(() => {
  const m = {}
  store.nodeColumns.forEach((c) => {
    if (!m[c.node_id]) m[c.node_id] = []
    m[c.node_id].push(c)
  })
  // Sort each node's fields by column_order
  Object.values(m).forEach((arr) => arr.sort((a, b) => (a.column_order || 0) - (b.column_order || 0)))
  return m
})

const tableNameMap = computed(() => {
  const m = {}
  store.allNodes.forEach((n) => { m[n.node_id] = n.table_name || n.node_name || n.node_id })
  return m
})

// ---- Field index map for anchor computation ----
function buildFieldIndexMap() {
  const m = {}
  for (const [nodeId, fields] of Object.entries(fieldsByNode.value)) {
    m[nodeId] = {}
    fields.forEach((f, i) => { m[nodeId][f.column_name] = i })
  }
  return m
}

// ---- Graph data builders per lineage type ----
const graphNodes = computed(() => {
  if (queryForm.lineageType === 'COLUMN' || queryForm.lineageType === 'OPERATOR') return buildColumnNodes()
  return buildTableNodes()
})

const graphEdges = computed(() => {
  if (queryForm.lineageType === 'COLUMN') return buildColumnEdges()
  if (queryForm.lineageType === 'OPERATOR') return buildOperatorEdges()
  return buildTableEdges()
})

// ----- TABLE mode -----
function buildTableNodes() {
  const nodes = []
  if (store.centerNode) {
    nodes.push({ ...store.centerNode, id: store.centerNode.node_id, stage: 'CENTER', nodeType: 'table' })
  }
  store.upstreamNodes.forEach((n) => nodes.push({ ...n, id: n.node_id, stage: 'UPSTREAM', nodeType: 'table' }))
  store.downstreamNodes.forEach((n) => nodes.push({ ...n, id: n.node_id, stage: 'DOWNSTREAM', nodeType: 'table' }))
  return nodes
}

function buildTableEdges() {
  return store.edges.map((e) => ({
    source: e.source_node_id,
    target: e.target_node_id,
    label: e.lineage_stage || '',
    lineageType: e.lineage_type,
    confidence: e.confidence,
    sourceProgram: e.source_program,
  }))
}

// ----- COLUMN mode: table-card nodes with field rows -----
function buildColumnNodes() {
  return store.allNodes.map((n) => {
    const nodeId = n.node_id
    const fields = (fieldsByNode.value[nodeId] || []).map((c) => {
      // Check if this field is computed (is target of a column edge)
      const targetEdge = store.columnEdges.find((ce) => ce.target_column_id === c.column_id)
      return {
        columnId: c.column_id,
        name: c.column_name,
        type: c.column_type || '',
        isPk: c.is_pk === 1,
        isFk: c.is_fk === 1,
        mappingType: targetEdge ? getMappingType(targetEdge.transform_expr) : null,
        transformExpr: targetEdge ? targetEdge.transform_expr : null,
      }
    })

    return {
      id: nodeId,
      label: n.table_name || n.node_name || nodeId,
      nodeType: 'table-card',
      stage: nodeId === store.centerNode?.node_id ? 'CENTER'
        : store.upstreamNodes.some((u) => u.node_id === nodeId) ? 'UPSTREAM' : 'DOWNSTREAM',
      fields,
    }
  })
}

function buildColumnEdges() {
  const fieldIdxMap = buildFieldIndexMap()
  const edges = []

  store.columnEdges.forEach((ce) => {
    const srcCol = columnMap.value[ce.source_column_id]
    const tgtCol = columnMap.value[ce.target_column_id]
    if (!srcCol || !tgtCol) return

    const srcNodeId = srcCol.node_id
    const tgtNodeId = tgtCol.node_id
    const srcFields = fieldsByNode.value[srcNodeId] || []
    const tgtFields = fieldsByNode.value[tgtNodeId] || []
    const srcIdx = fieldIdxMap[srcNodeId]?.[srcCol.column_name]
    const tgtIdx = fieldIdxMap[tgtNodeId]?.[tgtCol.column_name]
    if (srcIdx === undefined || tgtIdx === undefined) return

    // Anchor: source uses right side (offset by field count), target uses left side
    edges.push({
      source: srcNodeId,
      target: tgtNodeId,
      sourceAnchor: srcFields.length + srcIdx,
      targetAnchor: tgtIdx,
      label: shortMappingLabel(getMappingType(ce.transform_expr)),
      lineageType: 'COLUMN',
      mappingType: getMappingType(ce.transform_expr),
      transformExpr: ce.transform_expr,
      operatorDetail: ce.operator_detail,
      confidence: ce.confidence,
      sourceColumnId: ce.source_column_id,
      targetColumnId: ce.target_column_id,
    })
  })

  return edges
}

function getMappingType(expr) {
  if (!expr) return 'DIRECT'
  if (/CASE WHEN/i.test(expr)) return 'CASE_WHEN'
  if (/SUM|COUNT|AVG|MIN|MAX|GROUP BY/i.test(expr)) return 'AGGREGATE'
  if (/COALESCE|CONCAT|SUBSTR|TRIM|NVL/i.test(expr)) return 'FUNCTION'
  if (expr === 'DIRECT') return 'DIRECT'
  return 'DIRECT'
}

function shortMappingLabel(type) {
  const labels = { AGGREGATE: '∑聚合', CASE_WHEN: '⇉条件', FUNCTION: 'ƒ函数' }
  return labels[type] || ''
}

// ----- OPERATOR mode: table-level edges + field operator popup -----
// OPERATOR mode shows table-card nodes with fields (same as COLUMN),
// but uses TABLE-level edges (not field-to-field) to show data flow direction.
// Field rows are clickable → pops up SQL expression dialog.

function buildOperatorEdges() {
  return store.edges.map((e) => ({
    source: e.source_node_id,
    target: e.target_node_id,
    label: e.lineage_type === 'OPERATOR' ? (e.source_program || '算子') : (e.lineage_stage || ''),
    lineageType: e.lineage_type,
    lineage_stage: e.lineage_stage,
    confidence: e.confidence,
    sourceProgram: e.source_program,
  }))
}

// Operator SQL dialog state
const operatorDialogVisible = ref(false)
const operatorDialogData = ref(null)

function openOperatorDialog(field, nodeId) {
  const tgtColId = field.columnId
  const matchingEdge = store.columnEdges.find((ce) => ce.target_column_id === tgtColId)
  if (!matchingEdge) {
    operatorDialogData.value = {
      fieldName: field.name,
      tableName: tableNameMap.value[nodeId] || nodeId,
      transformExpr: '-',
      parseMethod: '-',
      confidence: null,
      operatorTypes: [],
      sourceFields: [],
    }
    operatorDialogVisible.value = true
    return
  }

  // Parse operator detail
  let operatorTypes = []
  let detail = ''
  if (matchingEdge.operator_detail) {
    try {
      const od = typeof matchingEdge.operator_detail === 'string'
        ? JSON.parse(matchingEdge.operator_detail)
        : matchingEdge.operator_detail
      operatorTypes = od.operator_types || []
      detail = od.detail || ''
    } catch { /* ignore */ }
  }

  // Gather source fields
  const srcCol = columnMap.value[matchingEdge.source_column_id]
  const sourceFields = []
  if (srcCol) {
    sourceFields.push({
      nodeName: tableNameMap.value[srcCol.node_id] || srcCol.node_id,
      columnName: srcCol.column_name,
      columnType: srcCol.column_type || '',
      role: getFieldRole(matchingEdge.transform_expr),
    })
  }

  operatorDialogData.value = {
    fieldName: field.name,
    tableName: tableNameMap.value[nodeId] || nodeId,
    transformExpr: matchingEdge.transform_expr || '-',
    parseMethod: matchingEdge.parse_method || 'AST',
    confidence: matchingEdge.confidence || null,
    operatorTypes,
    detail,
    sourceFields,
  }
  operatorDialogVisible.value = true
}

function closeOperatorDialog() {
  operatorDialogVisible.value = false
  operatorDialogData.value = null
}

// ---- Field click -> operator detail panel ----
function onFieldClick(event) {
  if (!event) {
    closeFieldPanel()
    return
  }

  const { nodeId, fieldIndex, field } = event
  activeField.value = { nodeId, fieldIndex }

  // OPERATOR mode: show popup dialog with SQL expression
  if (queryForm.lineageType === 'OPERATOR') {
    openOperatorDialog(field, nodeId)
    return
  }

  // COLUMN mode: show inline FieldOperatorPanel
  // Find the column_edge where this field is the target
  const tgtColId = field.columnId
  const matchingEdge = store.columnEdges.find((ce) => ce.target_column_id === tgtColId)
  if (!matchingEdge) {
    // Still show basic field info even without edge detail
    fieldDetailData.value = {
      targetNode: tableNameMap.value[nodeId] || nodeId,
      fieldName: field.name,
      transformExpr: '-',
      parseMethod: '-',
      confidence: null,
      operatorDetail: null,
      sourceFields: [],
      filterCondition: null,
    }
    return
  }

  // Gather source fields
  const srcCol = columnMap.value[matchingEdge.source_column_id]
  const sourceFields = []
  if (srcCol) {
    const srcNodeName = tableNameMap.value[srcCol.node_id] || srcCol.node_id
    sourceFields.push({
      nodeId: srcCol.node_id,
      nodeName: srcNodeName,
      columnName: srcCol.column_name,
      columnType: srcCol.column_type || '',
      role: getFieldRole(matchingEdge.transform_expr),
    })
  }

  // Parse operator detail
  let operatorDetail = null
  let filterCondition = null
  if (matchingEdge.operator_detail) {
    try {
      const od = typeof matchingEdge.operator_detail === 'string'
        ? JSON.parse(matchingEdge.operator_detail)
        : matchingEdge.operator_detail
      operatorDetail = od
      filterCondition = od.filter_condition || null
    } catch { /* ignore parse errors */ }
  }

  fieldDetailData.value = {
    targetNode: tableNameMap.value[nodeId] || nodeId,
    fieldName: field.name,
    transformExpr: matchingEdge.transform_expr || '-',
    parseMethod: matchingEdge.parse_method || 'AST',
    confidence: matchingEdge.confidence || null,
    operatorDetail,
    sourceFields,
    filterCondition,
  }
}

function getFieldRole(expr) {
  if (!expr) return '计算字段'
  if (expr === 'DIRECT') return '直接赋值'
  if (/GROUP BY/.test(expr)) return '分组字段'
  if (/CASE WHEN|IF\b/.test(expr)) return '条件判断'
  if (/SUM|COUNT|AVG|MIN|MAX/.test(expr)) return '聚合字段'
  if (/WHERE|FILTER|>|<|=/.test(expr)) return '过滤条件'
  return '计算字段'
}

function closeFieldPanel() {
  activeField.value = null
  fieldDetailData.value = null
}

// ---- Other handlers ----
async function doQuery() {
  if (!queryForm.tableName) return
  closeFieldPanel()
  const params = {
    table_name: queryForm.tableName,
    system_code: queryForm.systemCode || undefined,
    cluster_id: queryForm.clusterId || undefined,
    direction: queryForm.direction,
    depth: queryForm.depth,
    lineage_type: queryForm.lineageType,
  }
  await store.queryLineage(params)
}

function resetQuery() {
  queryForm.systemCode = null
  queryForm.clusterId = null
  queryForm.tableName = ''
  queryForm.direction = 'BOTH'
  queryForm.depth = 3
  queryForm.lineageType = 'TABLE'
  closeFieldPanel()
  store.clearGraph()
}

async function searchTables(query, cb) {
  if (!query) return cb([])
  try {
    const res = await lineageApi.searchTables(query)
    const items = res?.data || []
    cb(items.map((n) => ({ value: n.table_name || n.node_name, ...n })))
  } catch {
    cb([])
  }
}

function onNodeClick(node) {
  if (node.nodeType === 'operator') {
    detailNode.value = { node_name: `算子: ${node.label}`, node_type: 'OPERATOR' }
    drawerVisible.value = true
    return
  }
  // Table / table-card node
  const all = store.allNodes
  detailNode.value = all.find((n) => n.node_id === node.id) || null
  drawerVisible.value = true
}

watch(() => queryForm.lineageType, () => {
  if (store.centerNode && queryForm.tableName) {
    doQuery()
  }
})

onMounted(() => {
  store.loadSystems()
  store.loadClusters()
})
</script>

<style scoped>
.search-card {
  margin-bottom: 16px;
}
.graph-card {
  min-height: 400px;
}
.graph-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  flex-wrap: wrap;
  gap: 8px;
}
.graph-title {
  font-size: 16px;
  font-weight: 600;
}
.node-count-tag {
  margin-left: 8px;
}
.stage-legend {
  display: flex;
  gap: 12px;
  font-size: 12px;
  color: #666;
}
.legend-item {
  display: flex;
  align-items: center;
  gap: 4px;
}
.dot {
  width: 10px;
  height: 10px;
  border-radius: 2px;
  display: inline-block;
}
.dot.ingest { background: #1890FF; }
.dot.process { background: #52C41A; }
.dot.output { background: #FA8C16; }
.dot.table-edge { background: #1890FF; }
.dot.column-edge { background: #13C2C2; }
.dot.operator-edge { background: #722ED1; }
.dot.direct-edge { background: #1890FF; }
.dot.agg-edge { background: #52C41A; }
.dot.case-edge { background: #FA8C16; }
.dot.table-node { background: #D9D9D9; }
.dot.operator-node { background: #52C41A; }
.legend-divider {
  width: 1px;
  height: 14px;
  background: #e8e8e8;
  display: inline-block;
  align-self: center;
}
.graph-container {
  height: calc(100vh - 320px);
  min-height: 500px;
  border: 1px solid #f0f0f0;
  border-radius: 4px;
}
</style>
