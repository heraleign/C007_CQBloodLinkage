import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    redirect: '/lineage/analysis',
  },
  {
    path: '/lineage/analysis',
    name: 'LineageAnalysis',
    component: () => import('../views/lineage/LineageAnalysis.vue'),
    meta: { title: '血缘分析' },
  },
  {
    path: '/lineage/graph',
    name: 'LineageGraph',
    component: () => import('../views/lineage/LineageGraph.vue'),
    meta: { title: '血缘全景视图' },
  },
  {
    path: '/lineage/governance',
    name: 'LineageGovernance',
    component: () => import('../views/lineage/LineageGovernance.vue'),
    meta: { title: '血缘治理' },
  },
  {
    path: '/lineage/export',
    name: 'LineageExport',
    component: () => import('../views/lineage/LineageExport.vue'),
    meta: { title: '血缘导出' },
  },
  {
    path: '/atom',
    name: 'AtomServices',
    component: () => import('../views/atom/AtomServices.vue'),
    meta: { title: '原子能力' },
  },
  {
    path: '/admin',
    name: 'Admin',
    component: () => import('../views/admin/AdminDashboard.vue'),
    meta: { title: '系统管理' },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
