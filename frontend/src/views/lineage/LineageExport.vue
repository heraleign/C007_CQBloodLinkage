<template>
  <div class="lineage-export">
    <el-card shadow="never">
      <template #header>
        <span>血缘导出</span>
      </template>

      <el-form :model="exportForm" label-position="top">
        <el-form-item label="选择表">
          <el-select
            v-model="exportForm.tableNames"
            multiple
            filterable
            allow-create
            default-first-option
            placeholder="输入表名后回车添加"
            style="width: 100%"
          />
        </el-form-item>

        <el-form-item label="导出方向">
          <el-radio-group v-model="exportForm.direction">
            <el-radio value="UPSTREAM">上游</el-radio>
            <el-radio value="DOWNSTREAM">下游</el-radio>
            <el-radio value="BOTH">全部</el-radio>
          </el-radio-group>
        </el-form-item>

        <el-form-item label="导出层数">
          <el-select v-model="exportForm.depth" style="width: 120px">
            <el-option label="1层" :value="1" />
            <el-option label="2层" :value="2" />
            <el-option label="3层" :value="3" />
            <el-option label="全部" :value="10" />
          </el-select>
        </el-form-item>

        <el-form-item label="导出粒度">
          <el-radio-group v-model="exportForm.lineageType">
            <el-radio value="TABLE">表级血缘</el-radio>
            <el-radio value="COLUMN">字段级血缘</el-radio>
            <el-radio value="OPERATOR">算子级血缘</el-radio>
            <el-radio value="ALL">全部</el-radio>
          </el-radio-group>
        </el-form-item>

        <el-form-item label="导出格式">
          <el-radio-group v-model="exportForm.exportFormat">
            <el-radio value="EXCEL">Excel</el-radio>
            <el-radio value="WORD">Word</el-radio>
          </el-radio-group>
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="doExport" :loading="exporting">
            <el-icon><Download /></el-icon> 导出
          </el-button>
          <el-button @click="doPreview">预览</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { lineageApi } from '@/api/lineage'

const exportForm = reactive({
  tableNames: [],
  direction: 'BOTH',
  depth: 3,
  lineageType: 'ALL',
  exportFormat: 'EXCEL',
})

const exporting = ref(false)

async function doExport() {
  if (!exportForm.tableNames.length) {
    ElMessage.warning('请至少选择一个表')
    return
  }

  exporting.value = true
  try {
    const res = await lineageApi.executeExport(exportForm)
    // Handle blob download
    const blob = new Blob([res], {
      type: exportForm.exportFormat === 'EXCEL'
        ? 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        : 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `lineage_export_${Date.now()}.${exportForm.exportFormat === 'EXCEL' ? 'xlsx' : 'docx'}`
    a.click()
    URL.revokeObjectURL(url)
    ElMessage.success('导出成功')
  } finally {
    exporting.value = false
  }
}

async function doPreview() {
  if (!exportForm.tableNames.length) {
    ElMessage.warning('请至少选择一个表')
    return
  }
  const res = await lineageApi.previewExport(exportForm)
  if (res?.data) {
    ElMessage.info(`预计导出 ${res.data.estimated_nodes} 个节点`)
  }
}
</script>
