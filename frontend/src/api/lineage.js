import request from './request'

export const lineageApi = {
  // Nodes
  getNodes(params) {
    return request.get('/api/v1/nodes/', { params })
  },
  getNode(id) {
    return request.get(`/api/v1/nodes/${id}`)
  },
  createNode(data) {
    return request.post('/api/v1/nodes/', data)
  },
  updateNode(id, data) {
    return request.put(`/api/v1/nodes/${id}`, data)
  },
  deleteNode(id) {
    return request.delete(`/api/v1/nodes/${id}`)
  },
  getNodeColumns(nodeId) {
    return request.get(`/api/v1/nodes/${nodeId}/columns`)
  },

  // Edges
  getEdges(params) {
    return request.get('/api/v1/edges/', { params })
  },
  createEdge(data) {
    return request.post('/api/v1/edges/', data)
  },
  deleteEdge(id) {
    return request.delete(`/api/v1/edges/${id}`)
  },

  // Analysis
  queryLineage(data) {
    return request.post('/api/v1/analysis/query', data)
  },
  searchTables(keyword) {
    return request.get('/api/v1/analysis/search', { params: { keyword } })
  },
  listSystems() {
    return request.get('/api/v1/analysis/systems')
  },
  listClusters() {
    return request.get('/api/v1/analysis/clusters')
  },

  // Ingest
  triggerIngestSync() {
    return request.post('/api/v1/ingest/sync')
  },
  getIngestStatus() {
    return request.get('/api/v1/ingest/status')
  },

  // Export
  previewExport(data) {
    return request.post('/api/v1/export/preview', data)
  },
  executeExport(data) {
    return request.post('/api/v1/export/execute', data, { responseType: 'blob' })
  },

  // Atom APIs
  parseTableLineage(data) {
    return request.post('/api/v1/atom/parse-table-lineage', data)
  },
  parseColumnLineage(data) {
    return request.post('/api/v1/atom/parse-column-lineage', data)
  },
  parseScriptLineage(data) {
    return request.post('/api/v1/atom/parse-script-lineage', data)
  },
  saveLineage(data) {
    return request.post('/api/v1/atom/save-lineage', data)
  },
  queryLineageAtom(data) {
    return request.post('/api/v1/atom/query-lineage', data)
  },

  // Health
  health() {
    return request.get('/health')
  },

  // System Config
  listAiConfigs() {
    return request.get('/api/v1/system/ai-config')
  },
  getAiConfig(configId) {
    return request.get(`/api/v1/system/ai-config/${configId}`)
  },
  createAiConfig(data) {
    return request.post('/api/v1/system/ai-config', data)
  },
  updateAiConfig(configId, data) {
    return request.put(`/api/v1/system/ai-config/${configId}`, data)
  },
  deleteAiConfig(configId) {
    return request.delete(`/api/v1/system/ai-config/${configId}`)
  },
}
