<template>
  <div class="admin-dashboard">
    <el-tabs v-model="activeTab" type="border-card">
      <!-- ========== Tab 1: 概览 ========== -->
      <el-tab-pane label="概览" name="overview">
        <el-row :gutter="16" style="margin-bottom: 16px">
          <el-col :span="6" v-for="stat in stats" :key="stat.label">
            <el-card shadow="never">
              <div class="stat-card">
                <div class="stat-value">{{ stat.value }}</div>
                <div class="stat-label">{{ stat.label }}</div>
              </div>
            </el-card>
          </el-col>
        </el-row>

        <!-- 集群管理 -->
        <el-card shadow="never" style="margin-bottom: 16px">
          <template #header>
            <span>集群管理</span>
          </template>
          <el-empty description="集群管理功能" />
        </el-card>

        <!-- 同步控制 -->
        <el-card shadow="never">
          <template #header>
            <span>同步控制</span>
          </template>
          <el-descriptions :column="3" border>
            <el-descriptions-item label="入湖血缘同步">
              <el-tag type="success">每日 01:00</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="日志解析">
              <el-tag type="success">每日 02:30</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="Neo4j同步">
              <el-tag type="success">每日 04:00</el-tag>
            </el-descriptions-item>
          </el-descriptions>
          <div style="margin-top: 16px">
            <el-button type="primary" @click="triggerSync" :loading="syncing">
              手动触发同步
            </el-button>
          </div>
        </el-card>
      </el-tab-pane>

      <!-- ========== Tab 2: 大模型配置 ========== -->
      <el-tab-pane label="大模型配置" name="ai-config">
        <div class="section-toolbar">
          <span class="section-title">AI 调用配置管理</span>
          <el-button type="primary" @click="showAddDialog">
            <el-icon><Plus /></el-icon> 新增配置
          </el-button>
        </div>

        <el-table :data="aiConfigs" border stripe v-loading="aiLoading" style="width: 100%">
          <el-table-column prop="config_id" label="配置ID" width="180" />
          <el-table-column prop="ai_capability" label="能力类型" width="140">
            <template #default="{ row }">
              <el-tag :type="row.ai_capability === 'SQL_EXTRACT' ? 'primary' : 'success'">
                {{ row.ai_capability === 'SQL_EXTRACT' ? 'SQL提取' : '血缘解析' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="model_name" label="模型名称" width="160" />
          <el-table-column prop="api_endpoint" label="API端点" min-width="220" show-overflow-tooltip />
          <el-table-column prop="max_tokens" label="最大Token" width="100" />
          <el-table-column prop="temperature" label="温度" width="80" />
          <el-table-column prop="timeout_ms" label="超时(ms)" width="90" />
          <el-table-column prop="enabled" label="状态" width="80">
            <template #default="{ row }">
              <el-tag :type="row.enabled ? 'success' : 'info'" size="small">
                {{ row.enabled ? '启用' : '禁用' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="120" fixed="right">
            <template #default="{ row }">
              <el-button type="primary" link @click="showEditDialog(row)">编辑</el-button>
              <el-popconfirm title="确认删除该配置？" @confirm="deleteConfig(row.config_id)">
                <template #reference>
                  <el-button type="danger" link>删除</el-button>
                </template>
              </el-popconfirm>
            </template>
          </el-table-column>
        </el-table>

        <!-- 新增/编辑 AI 配置弹窗 -->
        <el-dialog v-model="configDialogVisible" :title="isEditing ? '编辑AI配置' : '新增AI配置'" width="640px">
          <el-form :model="configForm" label-position="top" v-loading="configSaving">
            <el-row :gutter="16">
              <el-col :span="12">
                <el-form-item label="配置ID" required>
                  <el-input v-model="configForm.config_id" :disabled="isEditing" placeholder="唯一标识，如 SQL_EXTRACT_DEFAULT" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="能力类型" required>
                  <el-select v-model="configForm.ai_capability" style="width: 100%" :disabled="isEditing">
                    <el-option label="SQL提取 (SQL_EXTRACT)" value="SQL_EXTRACT" />
                    <el-option label="血缘解析 (LINEAGE_PARSE)" value="LINEAGE_PARSE" />
                  </el-select>
                </el-form-item>
              </el-col>
            </el-row>
            <el-row :gutter="16">
              <el-col :span="12">
                <el-form-item label="模型名称" required>
                  <el-input v-model="configForm.model_name" placeholder="如 claude-sonnet-4-6" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="API端点" required>
                  <el-input v-model="configForm.api_endpoint" placeholder="https://api.example.com/v1/chat/completions" />
                </el-form-item>
              </el-col>
            </el-row>
            <el-form-item label="API密钥">
              <el-input v-model="configForm.api_key" type="password" placeholder="留空则不修改" show-password />
            </el-form-item>
            <el-row :gutter="16">
              <el-col :span="8">
                <el-form-item label="最大Token数">
                  <el-input-number v-model="configForm.max_tokens" :min="256" :max="32768" :step="512" style="width: 100%" />
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="温度">
                  <el-input-number v-model="configForm.temperature" :min="0" :max="2" :step="0.1" :precision="1" style="width: 100%" />
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="超时(ms)">
                  <el-input-number v-model="configForm.timeout_ms" :min="5000" :max="300000" :step="5000" style="width: 100%" />
                </el-form-item>
              </el-col>
            </el-row>
            <el-row :gutter="16">
              <el-col :span="12">
                <el-form-item label="重试次数">
                  <el-input-number v-model="configForm.retry_count" :min="0" :max="5" style="width: 100%" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="启用状态">
                  <el-switch v-model="configForm.enabled" :active-value="1" :inactive-value="0" active-text="启用" inactive-text="禁用" />
                </el-form-item>
              </el-col>
            </el-row>
          </el-form>
          <template #footer>
            <el-button @click="configDialogVisible = false">取消</el-button>
            <el-button type="primary" @click="saveConfig" :loading="configSaving">保存</el-button>
          </template>
        </el-dialog>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { lineageApi } from '@/api/lineage'

const activeTab = ref('overview')

// ---- 概览 ----
const stats = reactive([
  { label: '总节点数', value: 0 },
  { label: '总边数', value: 0 },
  { label: '已解析脚本', value: 0 },
  { label: '集群数', value: 0 },
])
const syncing = ref(false)

async function triggerSync() {
  syncing.value = true
  try {
    await lineageApi.triggerIngestSync()
    ElMessage.success('同步任务已触发')
  } finally {
    syncing.value = false
  }
}

// ---- 大模型配置 ----
const aiConfigs = ref([])
const aiLoading = ref(false)
const configDialogVisible = ref(false)
const configSaving = ref(false)
const isEditing = ref(false)

const configForm = reactive({
  config_id: '',
  ai_capability: 'SQL_EXTRACT',
  model_name: '',
  api_endpoint: '',
  api_key: '',
  max_tokens: 4096,
  temperature: 0.1,
  timeout_ms: 30000,
  retry_count: 2,
  enabled: 1,
})

function resetForm() {
  configForm.config_id = ''
  configForm.ai_capability = 'SQL_EXTRACT'
  configForm.model_name = ''
  configForm.api_endpoint = ''
  configForm.api_key = ''
  configForm.max_tokens = 4096
  configForm.temperature = 0.1
  configForm.timeout_ms = 30000
  configForm.retry_count = 2
  configForm.enabled = 1
}

async function loadAiConfigs() {
  aiLoading.value = true
  try {
    const res = await lineageApi.listAiConfigs()
    aiConfigs.value = res?.data || []
  } finally {
    aiLoading.value = false
  }
}

function showAddDialog() {
  isEditing.value = false
  resetForm()
  configDialogVisible.value = true
}

function showEditDialog(row) {
  isEditing.value = true
  configForm.config_id = row.config_id
  configForm.ai_capability = row.ai_capability
  configForm.model_name = row.model_name
  configForm.api_endpoint = row.api_endpoint
  configForm.api_key = ''  // Don't show stored key
  configForm.max_tokens = row.max_tokens
  configForm.temperature = row.temperature
  configForm.timeout_ms = row.timeout_ms
  configForm.retry_count = row.retry_count
  configForm.enabled = row.enabled
  configDialogVisible.value = true
}

async function saveConfig() {
  if (!configForm.config_id || !configForm.model_name || !configForm.api_endpoint) {
    ElMessage.warning('请填写必要字段（配置ID、模型名称、API端点）')
    return
  }
  configSaving.value = true
  try {
    if (isEditing.value) {
      const data = {}
      if (configForm.model_name) data.model_name = configForm.model_name
      if (configForm.api_endpoint) data.api_endpoint = configForm.api_endpoint
      if (configForm.api_key) data.api_key = configForm.api_key
      data.max_tokens = configForm.max_tokens
      data.temperature = configForm.temperature
      data.timeout_ms = configForm.timeout_ms
      data.retry_count = configForm.retry_count
      data.enabled = configForm.enabled
      await lineageApi.updateAiConfig(configForm.config_id, data)
      ElMessage.success('配置已更新')
    } else {
      await lineageApi.createAiConfig({ ...configForm })
      ElMessage.success('配置已创建')
    }
    configDialogVisible.value = false
    await loadAiConfigs()
  } finally {
    configSaving.value = false
  }
}

async function deleteConfig(configId) {
  try {
    await lineageApi.deleteAiConfig(configId)
    ElMessage.success('配置已删除')
    await loadAiConfigs()
  } catch {
    ElMessage.error('删除失败')
  }
}

onMounted(() => {
  loadAiConfigs()
})
</script>

<style scoped>
.stat-card {
  text-align: center;
  padding: 8px;
}
.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: #1890FF;
}
.stat-label {
  font-size: 14px;
  color: #666;
  margin-top: 4px;
}
.section-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
.section-title {
  font-size: 15px;
  font-weight: 600;
}
</style>
