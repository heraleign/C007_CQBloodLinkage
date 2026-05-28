<template>
  <div class="app-container">
    <!-- Sidebar -->
    <div class="app-sidebar">
      <div class="logo">数据血缘管理平台</div>
      <el-menu
        :default-active="route.path"
        background-color="#001529"
        text-color="rgba(255,255,255,0.7)"
        active-text-color="#fff"
        router
      >
        <el-menu-item index="/lineage/analysis">
          <el-icon><Search /></el-icon>
          <span>血缘分析</span>
        </el-menu-item>
        <el-menu-item index="/lineage/graph">
          <el-icon><Share /></el-icon>
          <span>血缘全景视图</span>
        </el-menu-item>
        <el-menu-item index="/lineage/governance">
          <el-icon><Edit /></el-icon>
          <span>血缘治理</span>
        </el-menu-item>
        <el-menu-item index="/lineage/export">
          <el-icon><Download /></el-icon>
          <span>血缘导出</span>
        </el-menu-item>
        <el-menu-item index="/atom">
          <el-icon><Connection /></el-icon>
          <span>原子能力</span>
        </el-menu-item>
        <el-menu-item index="/admin">
          <el-icon><Setting /></el-icon>
          <span>系统管理</span>
        </el-menu-item>
      </el-menu>
    </div>

    <!-- Main Content -->
    <div class="app-main">
      <div class="app-header">
        <el-breadcrumb>
          <el-breadcrumb-item :to="{ path: '/' }">首页</el-breadcrumb-item>
          <el-breadcrumb-item v-if="route.meta?.title">{{ route.meta.title }}</el-breadcrumb-item>
        </el-breadcrumb>
      </div>
      <div class="app-content">
        <router-view />
      </div>
    </div>
  </div>
</template>

<script setup>
import { useRoute } from 'vue-router'

const route = useRoute()
</script>
