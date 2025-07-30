import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/auth'

// 路由配置
const routes: Array<RouteRecordRaw> = [
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
  {
    path: '/',
    redirect: '/login',
    component: () => import('@/components/Layout/MainLayout.vue'),
    meta: {
      requiresAuth: true
    },
    children: [
      {
        path: '/dashboard',
        name: 'Dashboard',
        component: () => import('@/views/DashboardView.vue'),
        meta: {
          title: '仪表盘',
          icon: 'Dashboard',
          requiresAuth: true
        }
      },
      {
        path: '/delivery',
        name: 'Delivery',
        meta: {
          title: '送达回证',
          icon: 'Document',
          requiresAuth: true
        },
        children: [
          {
            path: '/delivery/generate',
            name: 'DeliveryGenerate',
            component: () => import('@/views/delivery/GenerateView.vue'),
            meta: {
              title: '上传图片',
              requiresAuth: true
            }
          },
          {
            path: '/delivery/list',
            name: 'DeliveryList',
            component: () => import('@/views/delivery/ListView.vue'),
            meta: {
              title: '任务列表',
              requiresAuth: true
            }
          },
          {
            path: '/delivery/detail/:id',
            name: 'TaskDetail',
            component: () => import('@/views/delivery/TaskDetailView.vue'),
            meta: {
              title: '任务详情',
              requiresAuth: true,
              hideInMenu: true
            }
          }
        ]
      },
    ]
  },
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

// 路由守卫
router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore()
  
  console.log('Route guard:', { 
    to: to.path, 
    requiresAuth: to.meta.requiresAuth, 
    isAuthenticated: authStore.isAuthenticated,
    hasUser: !!authStore.user 
  })
  
  // 设置页面标题
  if (to.meta.title) {
    document.title = `${to.meta.title} - ${import.meta.env.VITE_APP_TITLE || '送达回证系统'}`
  }
  
  // 检查是否需要认证
  if (to.meta.requiresAuth) {
    if (!authStore.isAuthenticated) {
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
        authStore.logout()
        next('/login')
        return
      }
    }
  }
  
  // 如果已登录用户访问登录页，重定向到仪表盘
  if (to.path === '/login' && authStore.isAuthenticated) {
    console.log('Already authenticated, redirecting to dashboard')
    next('/dashboard')
    return
  }
  
  console.log('Route guard passed, proceeding...')
  next()
})

// 路由错误处理
router.onError((error) => {
  console.error('路由错误:', error)
  ElMessage.error('加载页面失败')
})

export default router
