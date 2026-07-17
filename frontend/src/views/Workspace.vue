<template>
  <div class="workspace">
    <!-- 侧边栏 -->
    <aside class="sidebar" :style="{ width: sidebarW + 'px' }">
      <div class="sidebar-head">
        <span class="logo">SmartCS</span>
        <span class="agent-name" v-if="auth.user">{{ auth.user.display_name }}</span>
      </div>
      <nav class="sidebar-nav">
        <router-link to="/" class="nav-item" :class="{ active: $route.path === '/' || $route.path.startsWith('/chat') }">
          <el-icon><ChatLineSquare /></el-icon> 会话
        </router-link>
        <router-link to="/knowledge" class="nav-item" :class="{ active: $route.path === '/knowledge' }">
          <el-icon><Document /></el-icon> 知识库
        </router-link>
        <router-link to="/tickets" class="nav-item" :class="{ active: $route.path === '/tickets' }">
          <el-icon><Tickets /></el-icon> 工单
        </router-link>
        <router-link to="/dashboard" class="nav-item" :class="{ active: $route.path === '/dashboard' }">
          <el-icon><DataAnalysis /></el-icon> 看板
        </router-link>
      </nav>
      <div class="sidebar-foot">
        <el-button text size="small" @click="handleLogout">退出</el-button>
      </div>
    </aside>

    <!-- 左边会话列表 -->
    <aside class="conv-panel" :style="{ width: '320px' }" v-show="$route.path === '/' || $route.path.startsWith('/chat')">
      <ConversationList />
    </aside>

    <!-- 主区域 -->
    <main class="main-panel">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import ConversationList from './ConversationList.vue'

const auth = useAuthStore()
const router = useRouter()
const sidebarW = 60

function handleLogout() {
  auth.logout()
  router.push('/login')
}
</script>

<style scoped>
.workspace { display: flex; height: 100vh; background: #f5f5f5; }
.sidebar { background: #fff; border-right: 1px solid #e8e8e8; display: flex; flex-direction: column; align-items: center; padding: 12px 0; flex-shrink: 0; }
.sidebar-head { text-align: center; margin-bottom: 16px; }
.logo { font-size: 12px; font-weight: 700; color: #409EFF; display: block; }
.agent-name { font-size: 10px; color: #999; margin-top: 2px; display: block; }
.sidebar-nav { flex: 1; display: flex; flex-direction: column; gap: 2px; }
.nav-item { display: flex; flex-direction: column; align-items: center; padding: 10px 4px; font-size: 10px; color: #888; text-decoration: none; border-radius: 6px; width: 48px; transition: all .15s; }
.nav-item:hover { color: #409EFF; background: #ecf5ff; }
.nav-item.active { color: #409EFF; background: #ecf5ff; }
.nav-item .el-icon { font-size: 18px; margin-bottom: 2px; }
.sidebar-foot { margin-top: auto; }
.conv-panel { flex-shrink: 0; border-right: 1px solid #e8e8e8; background: #fafafa; }
.main-panel { flex: 1; overflow: hidden; display: flex; flex-direction: column; }
</style>
