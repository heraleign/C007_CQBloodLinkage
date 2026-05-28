<template>
  <div class="lineage-canvas-wrapper">
    <div v-if="error" class="graph-error-overlay">
      <p>⚠️ 图谱渲染异常</p>
      <pre>{{ error }}</pre>
    </div>
    <div v-if="debugInfo" class="graph-debug-info">
      {{ debugInfo }}
    </div>
    <div ref="containerRef" class="lineage-canvas"></div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, watch, nextTick } from 'vue'
import G6 from '@antv/g6'
import './customNodes.js' // side-effect registers 'table-card' node type

const props = defineProps({
  nodes: { type: Array, default: () => [] },
  edges: { type: Array, default: () => [] },
  centerNodeId: { type: String, default: null },
  lineageType: { type: String, default: 'TABLE' },
  activeField: { type: Object, default: null }, // { nodeId, fieldIndex }
})

const emit = defineEmits(['node-click', 'node-hover', 'field-click'])

const containerRef = ref(null)
let graph = null
let initRetries = 0
const MAX_RETRIES = 3

const error = ref('')
const debugInfo = ref('')

const DIM_OPACITY = 0.18
const HIGHLIGHT_OPACITY = 1.0

const nodeStyles = {
  upstream: { fill: '#E6F7FF', stroke: '#91D5FF', lineWidth: 1 },
  downstream: { fill: '#FFF7E6', stroke: '#FFD591', lineWidth: 1 },
  default: { fill: '#F5F5F5', stroke: '#D9D9D9', lineWidth: 1 },
}

function getStageColor(stage) {
  const colors = { INGEST: '#1890FF', PROCESS: '#52C41A', OUTPUT: '#FA8C16' }
  return colors[stage] || '#D9D9D9'
}

function getEdgeLabel(e) {
  if (e.lineageType === 'OPERATOR_IN' || e.lineageType === 'OPERATOR_OUT') return ''
  if (e.lineageType === 'COLUMN') {
    if (e.mappingType === 'DIRECT' || !e.mappingType) return ''
    return e.label || ''
  }
  if (e.lineageType === 'OPERATOR') return e.sourceProgram || '算子'
  return e.label || ''
}

function getEdgeStyle(e) {
  if (e.lineageType === 'OPERATOR_IN' || e.lineageType === 'OPERATOR_OUT') {
    return { stroke: '#52C41A', lineWidth: 2, lineDash: [4, 2] }
  }
  if (e.lineageType === 'OPERATOR') {
    return { stroke: '#722ED1', lineWidth: 2, lineDash: [5, 3] }
  }
  if (e.lineageType === 'COLUMN') {
    if (e.mappingType === 'CASE_WHEN') {
      return { stroke: '#FA8C16', lineWidth: 1.5, lineDash: [3, 3] }
    }
    if (e.mappingType === 'AGGREGATE') {
      return { stroke: '#52C41A', lineWidth: 2, lineDash: [5, 3] }
    }
    return { stroke: '#1890FF', lineWidth: 1.5 }
  }
  return {
    stroke: getStageColor(e.lineage_stage),
    lineWidth: (e.confidence || 1) > 0.8 ? 2 : 1,
  }
}

function initGraph() {
  if (!containerRef.value) return
  error.value = ''
  debugInfo.value = ''

  const width = containerRef.value.clientWidth
  const height = containerRef.value.clientHeight

  if (width < 10 || height < 10) {
    if (initRetries < MAX_RETRIES) {
      initRetries++
      setTimeout(() => initGraph(), 300 * initRetries)
    }
    return
  }
  initRetries = 0

  try {
    graph = new G6.Graph({
      container: containerRef.value,
      width,
      height,
      modes: {
        default: ['drag-canvas', 'zoom-canvas', 'drag-node'],
      },
      defaultNode: {
        type: 'rect',
        size: [120, 34],
        style: { radius: 4, fill: '#E6F7FF', stroke: '#91D5FF', lineWidth: 1 },
        labelCfg: {
          style: { fill: '#333', fontSize: 11, textAlign: 'center' },
          offset: 2,
        },
      },
      defaultEdge: {
        type: 'cubic-horizontal',
        style: {
          stroke: '#A3B1BF',
          lineWidth: 1,
          endArrow: { path: G6.Arrow.triangle(8, 10, 0), fill: '#A3B1BF' },
        },
      },
      layout: {
        type: 'dagre',
        rankdir: 'LR',
        align: 'UL',
        nodesep: 28,
        ranksep: 70,
        controlPoints: true,
        sortByCombo: false,
      },
      fitView: true,
      fitViewPadding: [30, 50, 30, 50],
    })

    // Node click: detect field row click vs card click
    graph.on('node:click', (evt) => {
      const node = evt.item
      const model = node.getModel()
      const targetName = evt.target?.get?.('name') || ''

      const fieldMatch = targetName.match(/^field-row-(\d+)$/)
      if (fieldMatch && model.nodeType === 'table-card') {
        const fieldIndex = parseInt(fieldMatch[1], 10)
        const field = model.fields?.[fieldIndex]
        if (field) {
          emit('field-click', {
            nodeId: model.id,
            nodeLabel: model.label,
            fieldIndex,
            field,
          })
          return
        }
      }
      emit('node-click', model)
    })

    graph.on('canvas:click', () => {
      emit('field-click', null)
    })

    graph.on('node:mouseenter', (evt) => {
      const model = evt.item.getModel()
      emit('node-hover', model)
    })
  } catch (e) {
    error.value = `Graph initialization failed: ${e.message}`
  }
}

function renderGraph() {
  if (!graph) return
  error.value = ''

  try {
    const isFieldMode = props.lineageType === 'COLUMN'
    const showTableCard = props.lineageType === 'COLUMN' || props.lineageType === 'OPERATOR'

    debugInfo.value = `N=${props.nodes.length} E=${props.edges.length} type=${props.lineageType}`

    // Build nodes
    const g6Nodes = props.nodes.map((n) => {
      const base = {
        id: n.node_id || n.id,
        label: n.table_name || n.node_name || n.label || n.id,
        original: n,
      }

      if (n.nodeType === 'operator') {
        return {
          ...base,
          type: 'diamond',
          size: [80, 40],
          style: { fill: '#F6FFED', stroke: '#52C41A', lineWidth: 2 },
          labelCfg: { style: { fill: '#333', fontSize: 9, textAlign: 'center' } },
        }
      }

      if (showTableCard) {
        const numFields = Math.min((n.fields || []).length, 8)
        const h = 32 + numFields * 24 + 8
        return {
          ...base,
          type: 'table-card',
          nodeType: 'table-card',
          size: [210, h],
          stage: n.stage,
          fields: n.fields || [],
          centerNode: n.stage === 'CENTER',
          style: {},
        }
      }

      // Default table node
      const isCenter = n.stage === 'CENTER'
      let style
      if (n.stage === 'UPSTREAM') style = { ...nodeStyles.upstream }
      else if (n.stage === 'DOWNSTREAM') style = { ...nodeStyles.downstream }
      else if (n.stage === 'INGEST') style = { fill: '#E6F7FF', stroke: '#1890FF', lineWidth: 1 }
      else if (n.stage === 'PROCESS') style = { fill: '#F6FFED', stroke: '#52C41A', lineWidth: 1 }
      else if (n.stage === 'OUTPUT') style = { fill: '#FFF7E6', stroke: '#FA8C16', lineWidth: 1 }
      else style = { ...nodeStyles.default }
      if (isCenter) { style.stroke = '#333'; style.lineWidth = 3 }

      return {
        ...base,
        type: 'rect',
        size: [120, 34],
        style,
        labelCfg: { style: { fill: '#333', fontSize: 11, textAlign: 'center' }, offset: 2 },
        stage: n.stage,
      }
    })

    // Build edges
    const g6Edges = props.edges.map((e) => {
      const style = getEdgeStyle(e)
      const edge = {
        source: e.source,
        target: e.target,
        label: getEdgeLabel(e),
        style: { ...style, endArrow: { path: G6.Arrow.triangle(8, 10, 0), fill: style.stroke } },
        labelCfg: {
          autoRotate: true,
          style: {
            fill: '#555',
            fontSize: 10,
            textAlign: 'center',
            fontWeight: 'bold',
            stroke: '#fff',
            lineWidth: 3,
          },
        },
      }

      if (e.sourceAnchor !== undefined) edge.sourceAnchor = e.sourceAnchor
      if (e.targetAnchor !== undefined) edge.targetAnchor = e.targetAnchor

      return edge
    })

    // Defensive: filter out invalid nodes/edges
    const validNodes = g6Nodes.filter((n) => n.id)
    const validEdges = g6Edges.filter((e) => e.source && e.target)

    if (validNodes.length === 0) {
      graph.clear()
      return
    }

    // Clear existing items to avoid stale shapes when node types change
    graph.clear()
    graph.changeData({ nodes: validNodes, edges: validEdges })
    graph.layout()

    // Ensure fitView after data change
    const doFitView = () => {
      if (graph && !graph.destroyed) {
        graph.fitView([30, 50, 30, 50])
      }
    }
    setTimeout(doFitView, 100)
    setTimeout(doFitView, 500)
  } catch (e) {
    error.value = `Render error: ${e.message}`
  }
}

// Field highlight/dim
function applyHighlight() {
  if (!graph) return

  const af = props.activeField
  if (!af) {
    graph.getNodes().forEach((n) => {
      graph.clearItemStates(n)
      const g = n.getContainer()
      if (g) g.getChildren().forEach((s) => s.attr('opacity', 1))
    })
    graph.getEdges().forEach((e) => {
      graph.clearItemStates(e)
      const g = e.getContainer()
      if (g) g.getChildren().forEach((s) => s.attr('opacity', 1))
    })
    return
  }

  const targetNodeId = af.nodeId
  const targetFieldIdx = af.fieldIndex

  const relatedEdgeIds = new Set()
  const relatedNodeIds = new Set([targetNodeId])

  props.edges.forEach((e, i) => {
    const matchesTarget = e.target === targetNodeId && e.targetAnchor === targetFieldIdx
    const matchesSource = e.source === targetNodeId && e.sourceAnchor === targetFieldIdx
    if (matchesTarget || matchesSource) {
      relatedEdgeIds.add(i)
      if (matchesTarget) relatedNodeIds.add(e.source)
      if (matchesSource) relatedNodeIds.add(e.target)
    }
  })

  graph.getNodes().forEach((node) => {
    const model = node.getModel()
    const isRelated = relatedNodeIds.has(model.id)
    const opacity = isRelated ? 1.0 : DIM_OPACITY
    const group = node.getContainer()
    if (group) {
      group.getChildren().forEach((s) => s.attr('opacity', opacity))
    }
  })

  graph.getEdges().forEach((edge, i) => {
    const isRelated = relatedEdgeIds.has(i)
    const opacity = isRelated ? 1.0 : DIM_OPACITY
    const group = edge.getContainer()
    if (group) {
      group.getChildren().forEach((s) => s.attr('opacity', opacity))
    }
  })
}

watch(
  () => [props.nodes, props.edges, props.lineageType],
  () => {
    nextTick(() => {
      if (!graph || graph.destroyed) {
        initGraph()
      }
      renderGraph()
    })
  },
  { deep: true }
)

watch(
  () => props.activeField,
  () => { applyHighlight() },
  { deep: true }
)

onMounted(() => {
  nextTick(() => {
    initGraph()
    renderGraph()
  })

  if (containerRef.value) {
    const ro = new ResizeObserver(() => {
      if (graph && !graph.destroyed) {
        const w = containerRef.value.clientWidth
        const h = containerRef.value.clientHeight
        if (w > 0 && h > 0) {
          graph.changeSize(w, h)
          graph.fitView([30, 50, 30, 50])
        }
      }
    })
    ro.observe(containerRef.value)
    containerRef.value._resizeObserver = ro
  }
})

onBeforeUnmount(() => {
  if (containerRef.value?._resizeObserver) {
    containerRef.value._resizeObserver.disconnect()
  }
  if (graph) {
    graph.destroy()
    graph = null
  }
})
</script>

<style scoped>
.lineage-canvas-wrapper {
  position: relative;
  width: 100%;
  height: 100%;
  min-height: 500px;
}
.lineage-canvas {
  width: 100%;
  height: 100%;
  min-height: 500px;
  background: #fff;
}
.graph-error-overlay {
  position: absolute;
  top: 8px;
  left: 8px;
  right: 8px;
  z-index: 10;
  background: #fff1f0;
  border: 1px solid #ff4d4f;
  border-radius: 4px;
  padding: 12px 16px;
  color: #cf1322;
  font-size: 13px;
}
.graph-error-overlay pre {
  margin: 4px 0 0;
  font-size: 11px;
  white-space: pre-wrap;
  color: #666;
}
.graph-debug-info {
  position: absolute;
  bottom: 8px;
  left: 8px;
  z-index: 10;
  background: rgba(0,0,0,0.6);
  color: #fff;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-family: monospace;
}
</style>
