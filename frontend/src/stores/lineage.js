import { defineStore } from 'pinia'
import { lineageApi } from '../api/lineage'

export const useLineageStore = defineStore('lineage', {
  state: () => ({
    // Analysis state
    centerNode: null,
    upstreamNodes: [],
    downstreamNodes: [],
    edges: [],
    columnEdges: [],
    nodeColumns: [],
    loading: false,

    // Search state
    searchResults: [],
    systems: [],
    clusters: [],

    // Node list
    nodes: [],
    nodeTotal: 0,

    // Selected state
    selectedNodeId: null,
    selectedFieldIds: [],
  }),

  getters: {
    allNodes: (state) => {
      const nodes = [...state.upstreamNodes, ...state.downstreamNodes]
      if (state.centerNode) {
        nodes.push(state.centerNode)
      }
      return nodes
    },
  },

  actions: {
    async queryLineage(params) {
      this.loading = true
      try {
        const res = await lineageApi.queryLineage(params)
        if (res?.data) {
          // Backend returns snake_case (center_node), normalize both forms
          const d = res.data
          this.centerNode = d.center_node || d.centerNode || null
          this.upstreamNodes = d.upstream_nodes || d.upstreamNodes || []
          this.downstreamNodes = d.downstream_nodes || d.downstreamNodes || []
          this.edges = d.edges || []
          this.columnEdges = d.column_edges || d.columnEdges || []
          this.nodeColumns = d.node_columns || d.nodeColumns || []
        }
      } finally {
        this.loading = false
      }
    },

    async searchTables(keyword) {
      const res = await lineageApi.searchTables(keyword)
      if (res?.data) {
        this.searchResults = res.data
      }
    },

    async loadSystems() {
      const res = await lineageApi.listSystems()
      if (res?.data) {
        this.systems = res.data
      }
    },

    async loadClusters() {
      const res = await lineageApi.listClusters()
      if (res?.data) {
        this.clusters = res.data
      }
    },

    setSelectedNode(nodeId) {
      this.selectedNodeId = nodeId
    },

    clearSelection() {
      this.selectedNodeId = null
      this.selectedFieldIds = []
    },

    clearGraph() {
      this.centerNode = null
      this.upstreamNodes = []
      this.downstreamNodes = []
      this.edges = []
      this.columnEdges = []
      this.nodeColumns = []
    },
  },
})
