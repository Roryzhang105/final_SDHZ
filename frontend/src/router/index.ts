import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/auth'

// 路由配置
const routes: Array<RouteRecordRaw> = [
  // 认证相关路由（不使用 MainLayout）
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/LoginView.vue'),
    meta: {
      title: '登录',
      requiresAuth: false,
      hideInMenu: true
    }
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('@/views/RegisterView.vue'),
    meta: {
      title: '注册',
      requiresAuth: false,
      hideInMenu: true
    }
  },
  
  // 主应用路由（使用 MainLayout）
  {
    path: '/app',
    component: () => import('@/components/Layout/MainLayout.vue'),
    meta: {
      requiresAuth: true
    },
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/views/DashboardView.vue'),
        meta: {
          title: '仪表盘',
          icon: 'Dashboard',
          requiresAuth: true
        }
      },
      {
        path: 'delivery',
        name: 'Delivery',
        meta: {
          title: '送达回证',
          icon: 'Document',
          requiresAuth: true
        },
        children: [
          {
            path: 'generate',
            name: 'DeliveryGenerate',
            component: () => import('@/views/delivery/GenerateView.vue'),
            meta: {
              title: '上传图片',
              requiresAuth: true
            }
          },
          {
            path: 'list',
            name: 'DeliveryList',
            component: () => import('@/views/delivery/ListView.vue'),
            meta: {
              title: '任务列表',
              requiresAuth: true
            }
          },
          {
            path: 'detail/:id',
            name: 'TaskDetail',
            component: () => import('@/views/delivery/TaskDetailView.vue'),
            meta: {
              title: '任务详情',
              requiresAuth: true,
              hideInMenu: true
            }
          }
        ]
      }
    ]
  },
  
  // 错误页面
  {
    path: '/404',
    name: 'NotFound',
    component: () => import('@/views/error/404View.vue'),
    meta: {
      title: '页面不存在',
      hideInMenu: true
    }
  },
  {
    path: '/500',
    name: 'ServerError',
    component: () => import('@/views/error/500View.vue'),
    meta: {
      title: '服务器错误',
      hideInMenu: true
    }
  },
  
  // 根路径（不设置重定向，在路由守卫中处理）
  {
    path: '/',
    name: 'Root',
    component: () => import('@/views/LoadingView.vue'), // 需要创建一个loading页面
    meta: {
      title: '加载中...',
      hideInMenu: true
    }
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/404'
  }
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
  scrollBehavior(to, from, savedPosition) {
    if (savedPosition) {
      return savedPosition
    } else {
      return { top: 0 }
    }
  }
})

// 重定向计数器，防止无限重定向
let redirectCount = 0
const MAX_REDIRECTS = 3

// 路由守卫
router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore()
  
  // 获取localStorage中的token进行详细日志记录
  const storedToken = localStorage.getItem('token')
  const storedUser = localStorage.getItem('user')
  
  console.log('=== Route Guard Start ===', {
    to: to.path,
    from: from.path,
    requiresAuth: to.meta.requiresAuth,
    storeToken: !!authStore.token,
    storeUser: !!authStore.user,
    storedToken: !!storedToken,
    storedUser: !!storedUser,
    isAuthenticated: authStore.isAuthenticated,
    redirectCount
  })
  
  // 检查重定向次数，防止无限循环
  if (redirectCount >= MAX_REDIRECTS) {
    console.error('Too many redirects, resetting and going to 404')
    redirectCount = 0
    next('/404')
    return
  }
  
  // 设置页面标题
  if (to.meta.title) {
    document.title = `${to.meta.title} - ${import.meta.env.VITE_APP_TITLE || '送达回证系统'}`
  }
  
  // 确保认证状态已初始化
  if (storedToken && !authStore.token) {
    console.log('Found stored token but auth not initialized, initializing...')
    try {
      await authStore.initializeAuth()
      console.log('Auth initialization completed in route guard')
    } catch (error) {
      console.error('Auth initialization failed in route guard:', error)
      // 如果初始化失败，清理可能损坏的状态
      localStorage.removeItem('token')
      localStorage.removeItem('user')
    }
  }
  
  // 处理根路径的智能重定向
  if (to.path === '/') {
    redirectCount++
    if (authStore.isAuthenticated) {
      console.log('Root path - authenticated, redirecting to dashboard')
      next('/app/dashboard')
      return
    } else {
      console.log('Root path - not authenticated, redirecting to login')
      next('/login')
      return
    }
  }
  
  // 如果已登录用户访问登录页，重定向到仪表盘
  if (to.path === '/login' && authStore.isAuthenticated) {
    redirectCount++
    console.log('Already authenticated, redirecting to dashboard')
    next('/app/dashboard')
    return
  }
  
  // 检查是否需要认证
  if (to.meta.requiresAuth) {
    if (!authStore.isAuthenticated) {
      redirectCount++
      console.log('Not authenticated, redirecting to login')
      ElMessage.warning('请先登录')
      next({
        path: '/login',
        query: { redirect: to.fullPath }
      })
      return
    }
    
    // 如果有token但没有用户信息，尝试获取用户信息
    if (!authStore.user) {
      try {
        console.log('Trying to get current user...')
        await authStore.getCurrentUser()
        console.log('Got current user successfully')
      } catch (error) {
        console.error('获取用户信息失败:', error)
        redirectCount++
        await authStore.logout()
        next('/login')
        return
      }
    }
  }
  
  // 成功通过守卫，重置重定向计数器
  redirectCount = 0
  console.log('Route guard passed, proceeding...')
  next()
})

// 路由错误处理
router.onError((error) => {
  console.error('路由错误:', error)
  ElMessage.error('加载页面失败')
})

export default router
