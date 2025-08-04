<template>
  <el-container class="main-layout">
    <!-- 侧边栏 -->
    <el-aside :width="sidebarCollapsed ? '64px' : '250px'" class="sidebar">
      <div class="logo-container">
        <div v-if="!sidebarCollapsed" class="logo-icon">
          <el-icon size="28"><Van /></el-icon>
        </div>
        <div v-else class="logo-icon-collapsed">
          <el-icon size="24"><Van /></el-icon>
        </div>
        <h1 v-if="!sidebarCollapsed" class="app-title">送达回证系统</h1>
      </div>
      
      <el-menu
        :default-active="activeMenu"
        :collapse="sidebarCollapsed"
        :unique-opened="true"
        router
        class="sidebar-menu"
        background-color="transparent"
        text-color="#4a5568"
        active-text-color="#5e72e4"
      >
        <template v-for="route in menuRoutes" :key="route.path">
          <!-- 有子菜单的路由 -->
          <el-sub-menu v-if="route.children && route.children.length > 0" :index="route.path">
            <template #title>
              <el-icon v-if="route.meta?.icon">
                <component :is="route.meta.icon" />
              </el-icon>
              <span>{{ route.meta?.title }}</span>
            </template>
            
            <el-menu-item
              v-for="child in route.children"
              :key="child.path"
              :index="child.path"
            >
              <el-icon v-if="child.meta?.icon">
                <component :is="child.meta.icon" />
              </el-icon>
              <span>{{ child.meta?.title }}</span>
            </el-menu-item>
          </el-sub-menu>
          
          <!-- 无子菜单的路由 -->
          <el-menu-item v-else :index="route.path">
            <el-icon v-if="route.meta?.icon">
              <component :is="route.meta.icon" />
            </el-icon>
            <span>{{ route.meta?.title }}</span>
          </el-menu-item>
        </template>
      </el-menu>
    </el-aside>
    
    <el-container class="right-container">
      <!-- 顶部导航栏 -->
      <el-header class="header">
        <div class="header-left">
          <el-button
            type="text"
            @click="toggleSidebar"
            class="sidebar-toggle"
          >
            <el-icon size="20">
              <Fold v-if="!sidebarCollapsed" />
              <Expand v-else />
            </el-icon>
          </el-button>
          
          <!-- 面包屑导航 -->
          <el-breadcrumb separator="/" class="breadcrumb">
            <el-breadcrumb-item
              v-for="item in breadcrumbList"
              :key="item.path"
              :to="item.path === $route.path ? undefined : item.path"
            >
              {{ item.title }}
            </el-breadcrumb-item>
          </el-breadcrumb>
        </div>
        
        <div class="header-right">
          <!-- 用户信息 -->
          <el-dropdown @command="handleUserCommand">
            <span class="user-dropdown">
              <el-avatar :size="32" :src="userAvatar">
                <el-icon><User /></el-icon>
              </el-avatar>
              <span class="username">{{ authStore.userInfo?.username || '用户' }}</span>
              <el-icon class="el-icon--right"><ArrowDown /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="profile">
                  <el-icon><User /></el-icon>
                  个人中心
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
        </div>
      </el-header>
      
      <!-- 主内容区域 -->
      <el-main class="main-content">
        <router-view v-slot="{ Component, route }">
          <transition name="fade-transform" mode="out-in">
            <keep-alive>
              <component :is="Component" :key="route.path" />
            </keep-alive>
          </transition>
        </router-view>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Fold,
  Expand,
  User,
  Setting,
  SwitchButton,
  ArrowDown,
  Odometer,
  Camera,
  List,
  Document,
  Van,
  Files
} from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

// 侧边栏状态
const sidebarCollapsed = ref(false)

// 用户头像
const userAvatar = ref('')

// 当前激活的菜单
const activeMenu = computed(() => route.path)

// 菜单路由（从路由配置中过滤）
const menuRoutes = computed(() => {
  const routes = router.getRoutes()
  // 找到主应用路由
  const appRoute = routes.find(route => route.path === '/app')
  if (!appRoute || !appRoute.children) return []
  
  return appRoute.children.filter(route => {
    // 过滤出需要在菜单中显示的路由
    if (!route.meta?.requiresAuth || route.meta?.hideInMenu || !route.meta?.title) {
      return false
    }
    
    // 检查管理员权限
    if (route.meta?.requiresAdmin && !authStore.user?.is_superuser) {
      return false
    }
    
    return true
  }).map(route => ({
    ...route,
    // 将相对路径转换为绝对路径
    path: `/app/${route.path}`,
    children: route.children?.filter(child => 
      !child.meta?.hideInMenu && child.meta?.title
    ).map(child => ({
      ...child,
      path: `/app/${route.path}/${child.path}`
    }))
  }))
})

// 面包屑导航
const breadcrumbList = computed(() => {
  const matched = route.matched.filter(item => item.meta?.title)
  const breadcrumbs = matched.map(item => ({
    title: item.meta?.title as string,
    path: item.path
  }))
  
  // 如果不是仪表盘页面，添加仪表盘作为首页
  if (route.path !== '/app/dashboard' && breadcrumbs[0]?.path !== '/app/dashboard') {
    breadcrumbs.unshift({
      title: '仪表盘',
      path: '/app/dashboard'
    })
  }
  
  return breadcrumbs
})

// 切换侧边栏
const toggleSidebar = () => {
  sidebarCollapsed.value = !sidebarCollapsed.value
}

// 处理用户下拉菜单命令
const handleUserCommand = async (command: string) => {
  switch (command) {
    case 'profile':
      ElMessage.info('个人中心功能开发中')
      break
    case 'settings':
      ElMessage.info('设置功能开发中')
      break
    case 'logout':
      try {
        await ElMessageBox.confirm(
          '确定要退出登录吗？',
          '提示',
          {
            confirmButtonText: '确定',
            cancelButtonText: '取消',
            type: 'warning'
          }
        )
        
        await authStore.logout()
        ElMessage.success('退出登录成功')
        router.push('/login')
      } catch (error) {
        // 用户取消或其他错误
      }
      break
  }
}

// 监听路由变化，移动端自动收起侧边栏
watch(
  () => route.path,
  () => {
    if (window.innerWidth < 768) {
      sidebarCollapsed.value = true
    }
  }
)
</script>

<style scoped>
.main-layout {
  height: 100vh;
  display: flex !important;
  flex-direction: row !important;
}

.sidebar {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-right: 1px solid rgba(0, 0, 0, 0.08);
  transition: width 0.3s ease;
  overflow: hidden;
  flex-shrink: 0;
  position: relative;
  z-index: 100;
  box-shadow: 2px 0 8px rgba(0, 0, 0, 0.04);
}

.logo-container {
  display: flex;
  align-items: center;
  padding: 20px;
  color: #2c3e50;
  border-bottom: 1px solid rgba(0, 0, 0, 0.08);
  background: rgba(94, 114, 228, 0.05);
}

.logo-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  margin-right: 12px;
  background: linear-gradient(135deg, #5e72e4, #825ee4);
  border-radius: 10px;
  color: white;
  box-shadow: 0 2px 8px rgba(94, 114, 228, 0.3);
  transition: all 0.3s ease;
}

.logo-icon:hover {
  transform: scale(1.05);
  box-shadow: 0 4px 12px rgba(94, 114, 228, 0.4);
}

.logo-icon-collapsed {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  margin: 0 auto;
  background: linear-gradient(135deg, #5e72e4, #825ee4);
  border-radius: 8px;
  color: white;
  box-shadow: 0 2px 8px rgba(94, 114, 228, 0.3);
  transition: all 0.3s ease;
}

.logo-icon-collapsed:hover {
  transform: scale(1.05);
  box-shadow: 0 4px 12px rgba(94, 114, 228, 0.4);
}

.app-title {
  font-size: 16px;
  font-weight: 600;
  margin: 0;
  white-space: nowrap;
  background: linear-gradient(135deg, #5e72e4, #825ee4);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.sidebar-menu {
  border: none;
  height: calc(100vh - 80px);
  overflow-y: auto;
  background: transparent;
}

.sidebar-menu:not(.el-menu--collapse) {
  width: 250px;
}

.header {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid rgba(0, 0, 0, 0.08);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
}

.header-left {
  display: flex;
  align-items: center;
}

.sidebar-toggle {
  margin-right: 20px;
  color: #5a5e66;
  padding: 8px;
  border-radius: 6px;
  border: 1px solid transparent;
  transition: all 0.3s ease;
}

.sidebar-toggle:hover {
  color: #5e72e4;
  background: rgba(94, 114, 228, 0.1);
  border-color: rgba(94, 114, 228, 0.2);
  transform: scale(1.05);
}

.breadcrumb {
  font-size: 14px;
}

.header-right {
  display: flex;
  align-items: center;
}

.user-dropdown {
  display: flex;
  align-items: center;
  cursor: pointer;
  padding: 8px 12px;
  border-radius: 8px;
  border: 1px solid transparent;
  transition: all 0.3s ease;
}

.user-dropdown:hover {
  background: rgba(94, 114, 228, 0.1);
  border-color: rgba(94, 114, 228, 0.2);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(94, 114, 228, 0.15);
}

.username {
  margin: 0 8px;
  font-size: 14px;
  color: #606266;
}

.right-container {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  width: 0; /* 确保flex能正确工作 */
}

.main-content {
  background-color: #f0f2f5;
  overflow-y: auto;
  padding: 0;
  flex: 1;
  min-width: 0;
  width: 100%;
}

/* 页面切换动画 */
.fade-transform-enter-active,
.fade-transform-leave-active {
  transition: all 0.3s;
}

.fade-transform-enter-from {
  opacity: 0;
  transform: translateX(-30px);
}

.fade-transform-leave-to {
  opacity: 0;
  transform: translateX(30px);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .header {
    padding: 0 15px;
  }
  
  .main-content {
    padding: 15px;
  }
  
  .breadcrumb {
    display: none;
  }
  
  .username {
    display: none;
  }
}

/* Element Plus 容器修复 */
.main-layout :deep(.el-container) {
  height: 100%;
}

.main-layout :deep(.el-aside) {
  flex-shrink: 0;
}

.main-layout :deep(.el-header) {
  height: 60px;
  line-height: 60px;
  padding: 0;
}

.main-layout :deep(.el-main) {
  padding: 0;
}

/* 滚动条样式 */
.sidebar-menu::-webkit-scrollbar {
  width: 6px;
}

.sidebar-menu::-webkit-scrollbar-thumb {
  background-color: rgba(94, 114, 228, 0.3);
  border-radius: 3px;
}

.sidebar-menu::-webkit-scrollbar-thumb:hover {
  background-color: rgba(94, 114, 228, 0.5);
}

/* 菜单项现代化样式 */
.sidebar-menu :deep(.el-menu-item),
.sidebar-menu :deep(.el-sub-menu .el-sub-menu__title) {
  margin: 4px 12px;
  border-radius: 8px;
  transition: all 0.3s ease;
  border: 1px solid transparent;
}

.sidebar-menu :deep(.el-menu-item:hover),
.sidebar-menu :deep(.el-sub-menu .el-sub-menu__title:hover) {
  background: rgba(94, 114, 228, 0.1) !important;
  border-color: rgba(94, 114, 228, 0.2);
  transform: translateX(2px);
}

.sidebar-menu :deep(.el-menu-item.is-active) {
  background: linear-gradient(135deg, rgba(94, 114, 228, 0.15), rgba(130, 94, 228, 0.15)) !important;
  border-color: rgba(94, 114, 228, 0.3);
  color: #5e72e4 !important;
  box-shadow: 0 2px 8px rgba(94, 114, 228, 0.2);
}

.sidebar-menu :deep(.el-sub-menu .el-menu-item) {
  margin: 2px 20px;
  border-radius: 6px;
}

.sidebar-menu :deep(.el-sub-menu .el-menu-item:hover) {
  background: rgba(94, 114, 228, 0.08) !important;
}
</style>