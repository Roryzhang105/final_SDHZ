// 导入设计系统样式 - 必须在 Element Plus 之前
import './styles/design-system/index.css'
import './assets/main.css'

import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'

import App from './App.vue'
import router from './router'
import { useAuthStore } from '@/stores/auth'

const app = createApp(App)

// 注册Element Plus图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

app.use(createPinia())
app.use(ElementPlus)
app.use(router)

// 初始化认证状态
const authStore = useAuthStore()
// 由于initializeAuth现在是异步的，我们不等待它完成
// 而是让路由守卫在需要时处理初始化
authStore.initializeAuth().catch(error => {
  console.error('Auth initialization failed:', error)
})

app.mount('#app')
