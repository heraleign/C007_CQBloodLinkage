<template>
  <div class="lineage-governance">
    <!-- 主卡片 -->
    <el-card shadow="never">
      <template #header>
        <span>血缘链路备注管理</span>
      </template>

      <!-- 搜索条件 -->
      <el-form :model="searchForm" inline style="margin-bottom: 16px">
        <el-form-item label="表名">
          <el-input v-model="searchForm.tableName" placeholder="输入表名" style="width: 200px" clearable />
        </el-form-item>
        <el-form-item label="系统">
          <el-select v-model="searchForm.systemCode" placeholder="全部" clearable style="width: 160px">
            <el-option v-for="s in store.systems" :key="s.code" :label="s.name" :value="s.code" />
          </el-select>
        </el-form-item>
        <el-form-item label="集群">
          <el-select v-model="searchForm.clusterId" placeholder="全部" clearable style="width: 160px">
            <el-option v-for="c in store.clusters" :key="c.cluster_id" :label="c.cluster_name" :value="c.cluster_id" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="search">
            <el-icon><Search /></el-icon> 搜索
          </el-button>
        </el-form-item>
      </el-form>

      <!-- 节点列表 -->
      <el-table
        :data="tableData"
        border
        stripe
        v-loading="loading"
        highlight-current-row
        @row-click="onRowClick"
      >
        <el-table-column type="index" label="序号" width="60" />
        <el-table-column prop="table_name" label="表名" min-width="180" />
        <el-table-column prop="table_cn_name" label="中文名" min-width="150" />
        <el-table-column prop="system_name" label="归属系统" width="120" />
        <el-table-column prop="cluster_name" label="集群" width="120">
          <template #default="{ row }">
            {{ row.cluster_name || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="table_remark" label="当前备注" min-width="200">
          <template #default="{ row }">
            <span :class="{ 'remark-empty': !row.table_remark }">
              {{ row.table_remark || '(空)' }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click.stop="editRemark(row)">编辑备注</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-if="total > 20"
        v-model:current-page="page"
        :page-size="20"
        :total="total"
        layout="prev, pager, next"
        class="pagination"
      />
    </el-card>

    <!-- 血缘链路视图（点击表名后展示） -->
    <el-card v-if="lineageNodes.length > 0" shadow="never" class="lineage-card">
      <template #header>
        <span>血缘链路视图 — {{ selectedTableName }}</span>
      </template>

      <!-- 链路链式展示 -->
      <div class="lineage-chain">
        <template v-for="(node, idx) in lineageNodes" :key="node.node_id">
          <div class="chain-node" :class="remarkClass(node)">
            <div class="chain-node-name">{{ node.table_name || node.node_name }}</div>
            <div class="chain-node-type">{{ node.node_type }}</div>
            <div class="chain-node-remark">
              <template v-if="node.table_remark">
                <el-icon style="color:#52c41a"><Check /></el-icon> {{ node.table_remark }}
              </template>
              <template v-else>
                <el-icon style="color:#faad14"><WarningFilled /></el-icon> 备注为空
              </template>
            </div>
          </div>
          <div v-if="idx < lineageNodes.length - 1" class="chain-arrow">
            <el-icon><ArrowRight /></el-icon>
          </div>
        </template>
      </div>

      <!-- 链路完整性 -->
      <div class="lineage-completeness">
        <el-icon><WarningFilled /></el-icon>
        链路完整性：{{ completenessPercent }}% ({{ remarkedCount }}/{{ lineageNodes.length }}节点有备注)
        <el-progress
          :percentage="completenessPercent"
          :color="completenessColor"
          style="width: 300px; margin-top: 6px"
        />
      </div>
    </el-card>

    <!-- 编辑备注弹窗 -->
    <el-dialog v-model="editVisible" title="编辑表备注" width="600px">
      <template v-if="editForm">
        <el-form label-position="top">
          <el-form-item label="表名">
            <el-tag>{{ editForm.table_name }}</el-tag>
          </el-form-item>
          <el-form-item label="当前备注">
            <span>{{ editForm.table_remark || '(空)' }}</span>
          </el-form-item>
          <el-form-item label="新备注">
            <el-input
              v-model="editForm.table_remark"
              type="textarea"
              :rows="3"
              placeholder="请输入备注信息"
            />
          </el-form-item>

          <!-- 字段备注补充 -->
          <el-divider>字段备注补充</el-divider>
          <el-table :data="editForm.columns || []" border size="small" max-height="300">
            <el-table-column prop="column_name" label="字段名" width="150" />
            <el-table-column label="当前备注" width="150">
              <template #default="{ row }">
                <span :class="{ 'remark-empty': !row.column_remark }">
                  {{ row.column_remark || '(空)' }}
                </span>
              </template>
            </el-table-column>
            <el-table-column label="新备注">
              <template #default="{ row }">
                <el-input
                  v-model="row.column_remark_new"
                  size="small"
                  placeholder="输入字段备注"
                  @click.stop
                />
              </template>
            </el-table-column>
          </el-table>
          <div v-if="!editForm.columns || editForm.columns.length === 0" style="color:#999;font-size:13px;text-align:center;padding:16px">
            暂无字段信息
          </div>
        </el-form>
      </template>
      <template #footer>
        <el-button @click="editVisible = false">取消</el-button>
        <el-button type="primary" @click="saveRemark">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useLineageStore } from '@/stores/lineage'
import { lineageApi } from '@/api/lineage'

const store = useLineageStore()

// ---- 搜索 ----
const searchForm = ref({ tableName: '', systemCode: null, clusterId: null })
const tableData = ref([])
const loading = ref(false)
const total = ref(0)
const page = ref(1)

async function search() {
  loading.value = true
  try {
    const res = await lineageApi.getNodes({
      table_name: searchForm.value.tableName || undefined,
      system_code: searchForm.value.systemCode || undefined,
      cluster_id: searchForm.value.clusterId || undefined,
      page: page.value,
      page_size: 20,
    })
    if (res?.data) {
      tableData.value = res.data.items || []
      total.value = res.data.total || 0
    }
  } finally {
    loading.value = false
  }
}

// ---- 行点击 → 加载血缘链路 ----
const selectedTableName = ref('')
const lineageNodes = ref([])

async function onRowClick(row) {
  selectedTableName.value = row.table_name || row.node_name
  try {
    const res = await lineageApi.queryLineage({
      table_name: row.table_name,
      cluster_id: row.cluster_id || undefined,
      direction: 'BOTH',
      depth: 5,
      lineage_type: 'TABLE',
    })
    if (res?.data) {
      const d = res.data
      // Build ordered lineage chain: center + upstream + downstream
      const chain = []
      const center = d.center_node || d.centerNode
      const ups = d.upstream_nodes || d.upstreamNodes || []
      const downs = d.downstream_nodes || d.downstreamNodes || []

      // Upstream first (reverse order so source → center)
      const reversedUps = [...ups].reverse()
      for (const n of reversedUps) {
        if (!chain.find((x) => x.node_id === n.node_id)) {
          chain.push(n)
        }
      }
      // Center
      if (center && !chain.find((x) => x.node_id === center.node_id)) {
        chain.push(center)
      }
      // Downstream
      for (const n of downs) {
        if (!chain.find((x) => x.node_id === n.node_id)) {
          chain.push(n)
        }
      }
      lineageNodes.value = chain
    }
  } catch {
    lineageNodes.value = []
  }
}

// ---- 链路完整性计算 ----
const remarkedCount = computed(() =>
  lineageNodes.value.filter((n) => n.table_remark).length
)
const completenessPercent = computed(() =>
  lineageNodes.value.length === 0 ? 0 : Math.round((remarkedCount.value / lineageNodes.value.length) * 100)
)
const completenessColor = computed(() => {
  if (completenessPercent.value >= 80) return '#52c41a'
  if (completenessPercent.value >= 50) return '#faad14'
  return '#f5222d'
})
function remarkClass(node) {
  return node.table_remark ? 'chain-node-ok' : 'chain-node-miss'
}

// ---- 编辑备注 ----
const editVisible = ref(false)
const editForm = ref(null)

async function editRemark(row) {
  // Load columns for this node
  let columns = []
  try {
    const res = await lineageApi.getNodeColumns(row.node_id)
    columns = (res?.data || []).map((c) => ({
      ...c,
      column_remark_new: c.column_remark || '',
    }))
  } catch {
    columns = []
  }

  editForm.value = {
    ...row,
    columns,
  }
  editVisible.value = true
}

async function saveRemark() {
  if (!editForm.value) return
  // Update table remark
  await lineageApi.updateNode(editForm.value.node_id, {
    table_remark: editForm.value.table_remark,
  })
  ElMessage.success('备注已更新')
  editVisible.value = false
  search()
}

onMounted(() => {
  store.loadSystems()
  store.loadClusters()
  search()
})
</script>

<style scoped>
.remark-empty {
  color: #faad14;
  font-style: italic;
}
.pagination {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}

/* ---- 血缘链路视图 ---- */
.lineage-card {
  margin-top: 16px;
}
.lineage-chain {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 4px;
  padding: 16px 0;
}
.chain-node {
  border: 1px solid #d9d9d9;
  border-radius: 6px;
  padding: 10px 16px;
  min-width: 140px;
  text-align: center;
  font-size: 13px;
  background: #fafafa;
}
.chain-node-ok {
  border-color: #b7eb8f;
  background: #f6ffed;
}
.chain-node-miss {
  border-color: #ffd591;
  background: #fff7e6;
}
.chain-node-name {
  font-weight: 600;
  margin-bottom: 2px;
}
.chain-node-type {
  font-size: 11px;
  color: #999;
  margin-bottom: 4px;
}
.chain-node-remark {
  font-size: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
}
.chain-arrow {
  color: #bfbfbf;
  font-size: 18px;
  flex-shrink: 0;
}
.lineage-completeness {
  border-top: 1px solid #f0f0f0;
  padding-top: 12px;
  margin-top: 8px;
  font-size: 14px;
  color: #faad14;
  display: flex;
  flex-direction: column;
  gap: 4px;
}
</style>
