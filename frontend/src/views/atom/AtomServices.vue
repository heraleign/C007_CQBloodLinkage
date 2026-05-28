<template>
  <div class="atom-services">
    <el-card shadow="never">
      <template #header>
        <span>单次血缘解析</span>
      </template>

      <!-- Parse Type Selector -->
      <el-form :model="parseForm" label-position="top">
        <el-form-item label="解析类型">
          <el-radio-group v-model="parseForm.parseType">
            <el-radio value="SQL">SQL文本</el-radio>
            <el-radio value="SCRIPT">Shell脚本</el-radio>
          </el-radio-group>
        </el-form-item>

        <el-form-item label="SQL方言">
          <el-select v-model="parseForm.sqlDialect" style="width: 200px">
            <el-option label="SparkSQL" value="SparkSQL" />
            <el-option label="HiveQL" value="HiveQL" />
            <el-option label="MySQL" value="MySQL" />
          </el-select>
        </el-form-item>

        <el-form-item label="AI补充">
          <el-switch v-model="parseForm.enableAI" />
        </el-form-item>

        <el-form-item label="输入内容">
          <el-input
            v-model="parseForm.inputContent"
            type="textarea"
            :rows="8"
            placeholder="请输入SQL或Shell脚本内容..."
          />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="doParse" :loading="parsing">
            <el-icon><Search /></el-icon> 开始解析
          </el-button>
          <el-button @click="clearResult">清除</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- Results -->
    <el-card v-if="parseResult" shadow="never" class="result-card">
      <template #header>
        <div class="result-header">
          <span>解析结果</span>
          <el-tag :type="parseResult.tableLineages?.length ? 'success' : 'info'">
            置信度：{{ parseResult.confidence }}
          </el-tag>
        </div>
      </template>

      <el-descriptions :column="3" border size="small">
        <el-descriptions-item label="解析方法">{{ parseResult.parseMethod || '-' }}</el-descriptions-item>
        <el-descriptions-item label="置信度">{{ parseResult.confidence }}</el-descriptions-item>
        <el-descriptions-item label="解析耗时">{{ parseResult.parseDurationMs }}ms</el-descriptions-item>
      </el-descriptions>

      <h4 style="margin: 16px 0 8px">表级血缘</h4>
      <el-table :data="parseResult.tableLineages || []" border size="small">
        <el-table-column prop="sourceTable" label="源表" />
        <el-table-column prop="targetTable" label="目标表" />
        <el-table-column prop="relationType" label="关系类型" width="140" />
      </el-table>

      <h4 style="margin: 16px 0 8px">字段级血缘</h4>
      <el-table :data="parseResult.columnLineages || []" border size="small">
        <el-table-column prop="sourceTable" label="源表" />
        <el-table-column prop="sourceColumn" label="源字段" />
        <el-table-column prop="targetTable" label="目标表" />
        <el-table-column prop="targetColumn" label="目标字段" />
        <el-table-column prop="transformExpr" label="转换表达式" width="120" />
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { lineageApi } from '@/api/lineage'

const parseForm = reactive({
  parseType: 'SQL',
  sqlDialect: 'SparkSQL',
  enableAI: true,
  inputContent: '',
})

const parsing = ref(false)
const parseResult = ref(null)

async function doParse() {
  if (!parseForm.inputContent.trim()) return

  parsing.value = true
  try {
    if (parseForm.parseType === 'SQL') {
      const res = await lineageApi.parseTableLineage({
        sql: parseForm.inputContent,
        sql_dialect: parseForm.sqlDialect,
        enable_ai: parseForm.enableAI,
      })
      parseResult.value = res?.data || { tableLineages: [], confidence: 0 }
    } else {
      const res = await lineageApi.parseScriptLineage({
        script_content: parseForm.inputContent,
        vendor_code: 'DIKE',
        script_type: 'SHELL_SPARK',
        enable_ai: parseForm.enableAI,
      })
      parseResult.value = res?.data || { tableLineages: [], confidence: 0 }
    }
  } finally {
    parsing.value = false
  }
}

function clearResult() {
  parseResult.value = null
  parseForm.inputContent = ''
}
</script>

<style scoped>
.result-card {
  margin-top: 16px;
}
.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
