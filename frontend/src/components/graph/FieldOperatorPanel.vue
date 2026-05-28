<template>
  <div v-if="fieldData" class="operator-panel">
    <div class="panel-header">
      <span class="panel-title">📐 字段口径解析</span>
      <div class="panel-actions">
        <el-button size="small" text @click="copyContent">复制</el-button>
        <el-button size="small" text @click="$emit('close')">✕</el-button>
      </div>
    </div>
    <div class="panel-body">
      <!-- Target field info -->
      <div class="target-field">
        目标字段：<strong>{{ fieldData.targetNode }}.{{ fieldData.fieldName }}</strong>
      </div>

      <!-- Participating fields table -->
      <div class="section">
        <div class="section-title">参与字段</div>
        <el-table :data="participatingFields" size="small" stripe border max-height="160">
          <el-table-column prop="sourceTable" label="来源表" min-width="100" />
          <el-table-column prop="columnName" label="字段名" min-width="90" />
          <el-table-column label="类型" width="40">
            <template #default="{ row }">{{ typeIcon(row.columnType) }}</template>
          </el-table-column>
          <el-table-column prop="role" label="角色" width="70">
            <template #default="{ row }">
              <el-tag :type="roleTagType(row.role)" size="small">{{ row.role }}</el-tag>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <!-- Transform expression -->
      <div class="section">
        <div class="section-title">加工逻辑</div>
        <div class="sql-block">{{ fieldData.transformExpr || '-' }}</div>
      </div>

      <!-- Filter condition -->
      <div class="section" v-if="fieldData.filterCondition">
        <div class="section-title">过滤条件</div>
        <div class="sql-block">{{ fieldData.filterCondition }}</div>
      </div>

      <!-- Operator types -->
      <div class="section">
        <div class="section-title">算子类型</div>
        <div class="operator-tags">
          <el-tag
            v-for="op in operatorTypes"
            :key="op"
            :type="operatorTagType(op)"
            size="small"
            class="op-tag"
          >
            {{ operatorLabel(op) }}
          </el-tag>
        </div>
      </div>

      <!-- Metadata -->
      <div class="meta-row">
        <span>解析方式：{{ fieldData.parseMethod || 'AST' }}</span>
        <span>置信度：{{ fieldData.confidence ? (fieldData.confidence * 100).toFixed(0) + '%' : '-' }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  fieldData: { type: Object, default: null },
})

defineEmits(['close'])

const participatingFields = computed(() => {
  if (!props.fieldData?.sourceFields) return []
  return props.fieldData.sourceFields.map((f) => ({
    sourceTable: f.nodeName || f.nodeId || '-',
    columnName: f.columnName || '-',
    columnType: f.columnType || '',
    role: f.role || '计算字段',
  }))
})

const operatorTypes = computed(() => {
  if (!props.fieldData?.operatorDetail) return []
  try {
    const detail = typeof props.fieldData.operatorDetail === 'string'
      ? JSON.parse(props.fieldData.operatorDetail)
      : props.fieldData.operatorDetail
    return detail.operator_types || []
  } catch {
    return []
  }
})

function roleTagType(role) {
  const map = { '计算字段': '', '分组字段': 'warning', '过滤条件': 'info', '关联键': 'danger' }
  return map[role] || ''
}

function operatorTagType(op) {
  const map = { DIRECT: '', AGGREGATE: 'success', CASE_WHEN: 'warning', JOIN: 'primary', FUNCTION: 'info' }
  return map[op] || ''
}

function operatorLabel(op) {
  const labels = {
    DIRECT: '→ 直接赋值',
    AGGREGATE: '∑ 聚合计算',
    CASE_WHEN: '🔀 条件映射',
    JOIN: '🔗 关联键',
    FUNCTION: '⚙️ 函数转换',
    GROUP_BY: '📊 分组',
    WHERE: '🔍 过滤条件',
  }
  return labels[op] || op
}

function typeIcon(type) {
  const t = (type || '').toUpperCase()
  if (/INT|DECIMAL|DOUBLE|FLOAT|BIGINT/.test(t)) return '#'
  if (/VARCHAR|CHAR|STRING|TEXT/.test(t)) return 'Aa'
  if (/DATE|TIME|TIMESTAMP/.test(t)) return 'D'
  return 'Aa'
}

function copyContent() {
  const text = `目标字段: ${props.fieldData?.targetNode || ''}.${props.fieldData?.fieldName || ''}\n` +
    `加工逻辑: ${props.fieldData?.transformExpr || '-'}\n` +
    `算子类型: ${operatorTypes.value.map(operatorLabel).join(', ')}`
  navigator.clipboard?.writeText(text)
}
</script>

<style scoped>
.operator-panel {
  border: 1px solid #e8e8e8;
  border-radius: 6px;
  background: #fff;
  font-size: 13px;
  margin-top: 12px;
  overflow: hidden;
}
.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 14px;
  background: #fafafa;
  border-bottom: 1px solid #e8e8e8;
}
.panel-title {
  font-weight: 600;
  font-size: 14px;
}
.panel-actions {
  display: flex;
  gap: 4px;
}
.panel-body {
  padding: 12px 14px;
}
.target-field {
  font-size: 13px;
  color: #333;
  margin-bottom: 10px;
  padding: 6px 10px;
  background: #f0f5ff;
  border-radius: 4px;
}
.section {
  margin-bottom: 10px;
}
.section-title {
  font-size: 11px;
  color: #888;
  margin-bottom: 4px;
  font-weight: 600;
}
.sql-block {
  background: #f6f8fa;
  border: 1px solid #e8e8e8;
  border-radius: 4px;
  padding: 8px 10px;
  font-family: monospace;
  font-size: 11px;
  line-height: 1.5;
  white-space: pre-wrap;
  color: #333;
  max-height: 120px;
  overflow-y: auto;
}
.operator-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
.op-tag {
  font-size: 11px;
}
.meta-row {
  display: flex;
  gap: 20px;
  font-size: 11px;
  color: #999;
  padding-top: 8px;
  border-top: 1px solid #f0f0f0;
}
</style>
