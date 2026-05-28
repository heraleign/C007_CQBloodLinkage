<template>
  <div class="lineage-graph">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span>血缘全景视图</span>
          <div>
            <el-radio-group v-model="viewLevel" size="small">
              <el-radio-button value="INGEST">入湖层</el-radio-button>
              <el-radio-button value="PROCESS">湖内加工层</el-radio-button>
              <el-radio-button value="OUTPUT">出湖层</el-radio-button>
              <el-radio-button value="ALL">全链路</el-radio-button>
            </el-radio-group>
          </div>
        </div>
      </template>
      <div class="legend">
        <span class="legend-item"><span class="dot ingest"></span> 入湖（蓝色）</span>
        <span class="legend-item"><span class="dot process"></span> 湖内加工（绿色）</span>
        <span class="legend-item"><span class="dot output"></span> 出湖（橙色）</span>
      </div>
      <div class="graph-container">
        <LineageCanvas
          :nodes="graphNodes"
          :edges="graphEdges"
          lineage-type="TABLE"
          @node-click="onNodeClick"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { lineageApi } from '@/api/lineage'
import LineageCanvas from '@/components/graph/LineageCanvas.vue'

const viewLevel = ref('ALL')
const rawNodes = ref([])
const rawEdges = ref([])
const loading = ref(false)

// Infer node stage from edges.
// Priority: INGEST > PROCESS > OUTPUT.
function computeNodeStages(nodes, edges) {
  const map = {}
  edges.forEach((e) => {
    const stage = e.lineage_stage
    const src = e.source_node_id
    const tgt = e.target_node_id
    if (stage === 'INGEST') {
      map[src] = 'INGEST'
      map[tgt] = 'INGEST'
    } else if (stage === 'PROCESS') {
      if (!map[src]) map[src] = 'PROCESS'
      if (!map[tgt]) map[tgt] = 'PROCESS'
    } else if (stage === 'OUTPUT') {
      if (!map[src]) map[src] = 'OUTPUT'
      if (!map[tgt]) map[tgt] = 'OUTPUT'
    }
  })
  return map
}

const graphNodes = computed(() => {
  const stageMap = computeNodeStages(rawNodes.value, rawEdges.value)
  const nodes = rawNodes.value.map((n) => ({
    id: n.node_id,
    node_id: n.node_id,
    label: n.table_name || n.node_name || n.node_id,
    node_name: n.node_name,
    table_name: n.table_name,
    node_type: n.node_type,
    stage: stageMap[n.node_id] || 'UNKNOWN',
  }))
  if (viewLevel.value === 'ALL') return nodes
  return nodes.filter((n) => n.stage === viewLevel.value)
})

const graphEdges = computed(() => {
  const edges = rawEdges.value.map((e) => ({
    source: e.source_node_id,
    target: e.target_node_id,
    lineageType: e.lineage_type,
    lineage_stage: e.lineage_stage,
    label: e.lineage_stage || '',
    confidence: e.confidence,
    sourceProgram: e.source_program,
  }))
  if (viewLevel.value === 'ALL') return edges
  return edges.filter((e) => e.lineage_stage === viewLevel.value)
})

async function loadOverviewData() {
  loading.value = true
  try {
    // Load all edges (no pagination)
    const edgeRes = await lineageApi.getEdges()
    rawEdges.value = edgeRes?.data || []

    // Load all nodes (paginated, max 100 per page)
    const allNodes = []
    let page = 1
    const pageSize = 100
    while (true) {
      const nodeRes = await lineageApi.getNodes({ page, page_size: pageSize })
      const items = nodeRes?.data?.items || []
      if (items.length === 0) break
      allNodes.push(...items)
      if (items.length < pageSize) break
      page++
    }
    rawNodes.value = allNodes
  } finally {
    loading.value = false
  }
}

function onNodeClick(node) {
  // Navigate to analysis page for this node
}

onMounted(() => {
  loadOverviewData()
})
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.legend {
  margin-bottom: 12px;
  display: flex;
  gap: 20px;
}
.legend-item {
  display: flex;
  align-items: center;
  font-size: 13px;
  color: #666;
}
.dot {
  width: 12px;
  height: 12px;
  border-radius: 2px;
  display: inline-block;
  margin-right: 6px;
}
.dot.ingest { background: #1890FF; }
.dot.process { background: #52C41A; }
.dot.output { background: #FA8C16; }
.graph-container {
  height: calc(100vh - 280px);
  min-height: 500px;
  border: 1px solid #f0f0f0;
  border-radius: 4px;
}
</style>
