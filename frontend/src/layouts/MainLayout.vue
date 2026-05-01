<template>
  <el-container class="main-container">
    <el-header class="header">
      <div class="logo">
        <el-icon size="24"><TrendCharts /></el-icon>
        <span class="title">空气质量数据分析平台</span>
      </div>
      <el-menu
        :default-active="activeMenu"
        mode="horizontal"
        router
        class="nav-menu"
      >
        <el-menu-item index="/">
          <el-icon><House /></el-icon>
          仪表盘
        </el-menu-item>
        <el-menu-item index="/upload">
          <el-icon><Upload /></el-icon>
          数据上传
        </el-menu-item>
        <el-menu-item index="/analysis">
          <el-icon><DataAnalysis /></el-icon>
          数据分析
        </el-menu-item>
        <el-menu-item index="/history">
          <el-icon><Document /></el-icon>
          历史记录
        </el-menu-item>
        <el-menu-item index="/settings">
          <el-icon><Setting /></el-icon>
          设置
        </el-menu-item>
      </el-menu>
      <el-dropdown @command="handleCommand" trigger="click">
        <div class="user-info" style="cursor: pointer;">
          <el-avatar :size="32" style="background-color: #667eea; margin-right: 8px;">
            {{ authStore.username?.charAt(0)?.toUpperCase() || 'U' }}
          </el-avatar>
          <span class="username">{{ authStore.username }}</span>
          <el-tag v-if="authStore.isAdmin" type="danger" size="small" style="margin-left: 8px;">
            管理员
          </el-tag>
          <el-icon class="el-icon--right" style="margin-left: 8px;"><ArrowDown /></el-icon>
        </div>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item command="profile">
              <el-icon><User /></el-icon>
              个人信息
            </el-dropdown-item>
            <el-dropdown-item command="settings">
              <el-icon><Setting /></el-icon>
              设置
            </el-dropdown-item>
            <el-dropdown-item divided command="logout">
              <el-icon><SwitchButton /></el-icon>
              退出登录
            </el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </el-header>
    <el-main class="main-content">
      <router-view />
    </el-main>
  </el-container>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { 
  House, 
  Upload, 
  DataAnalysis, 
  Document, 
  SwitchButton,
  TrendCharts
} from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const activeMenu = computed(() => route.path)

const handleLogout = () => {
  authStore.logout()
  router.push('/login')
}
</script>

<style scoped>
.main-container {
  min-height: 100vh;
}

.header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  padding: 0 20px;
  color: white;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.logo {
  display: flex;
  align-items: center;
  margin-right: 30px;
}

.title {
  font-size: 20px;
  font-weight: bold;
  margin-left: 10px;
}

.nav-menu {
  flex: 1;
  background: transparent;
  border: none;
}

.nav-menu .el-menu-item {
  color: rgba(255, 255, 255, 0.8);
  border-bottom: none;
}

.nav-menu .el-menu-item:hover,
.nav-menu .el-menu-item.is-active {
  color: white;
  background: rgba(255, 255, 255, 0.1);
  border-bottom: none;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 15px;
}

.username {
  font-size: 14px;
}

.main-content {
  background: #f5f7fa;
  padding: 20px;
}
</style>
