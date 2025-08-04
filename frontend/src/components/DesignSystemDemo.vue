<template>
  <div class="design-system-demo">
    <div class="demo-container">
      <!-- 页面标题 -->
      <div class="demo-header">
        <h1 class="demo-title animate-on-scroll animate-fade-in-up">
          🎨 设计系统演示
        </h1>
        <p class="demo-subtitle animate-on-scroll animate-fade-in-up">
          现代化的 UI 组件和动画效果展示
        </p>
      </div>

      <!-- 色彩系统 -->
      <section class="demo-section animate-on-scroll animate-fade-in-up">
        <h2 class="section-title">色彩系统</h2>
        <div class="color-grid">
          <div class="color-item">
            <div class="color-swatch color-primary"></div>
            <span>主色调</span>
          </div>
          <div class="color-item">
            <div class="color-swatch color-success"></div>
            <span>成功色</span>
          </div>
          <div class="color-item">
            <div class="color-swatch color-warning"></div>
            <span>警告色</span>
          </div>
          <div class="color-item">
            <div class="color-swatch color-danger"></div>
            <span>危险色</span>
          </div>
          <div class="color-item">
            <div class="color-swatch color-info"></div>
            <span>信息色</span>
          </div>
        </div>
      </section>

      <!-- 按钮组件 -->
      <section class="demo-section animate-on-scroll animate-fade-in-up">
        <h2 class="section-title">按钮组件</h2>
        <div class="button-grid">
          <button class="btn btn-primary">主要按钮</button>
          <button class="btn btn-secondary">次要按钮</button>
          <button class="btn btn-success">成功按钮</button>
          <button class="btn btn-warning">警告按钮</button>
          <button class="btn btn-danger">危险按钮</button>
          <button class="btn btn-ghost">幽灵按钮</button>
          <button class="btn btn-primary btn-sm">小按钮</button>
          <button class="btn btn-primary btn-lg">大按钮</button>
        </div>
      </section>

      <!-- 卡片组件 -->
      <section class="demo-section animate-on-scroll animate-fade-in-up">
        <h2 class="section-title">卡片组件</h2>
        <div class="card-grid">
          <div class="card hover-lift">
            <h3>基础卡片</h3>
            <p>这是一个基础的毛玻璃卡片，具有悬浮效果。</p>
            <button class="btn btn-primary btn-sm">了解更多</button>
          </div>
          <div class="card card-glass hover-lift">
            <h3>玻璃卡片</h3>
            <p>透明的毛玻璃效果，更加轻盈。</p>
            <button class="btn btn-secondary btn-sm">查看详情</button>
          </div>
          <div class="card card-primary hover-lift">
            <h3>主色调卡片</h3>
            <p>使用主色调的卡片变体。</p>
            <button class="btn btn-primary btn-sm">立即行动</button>
          </div>
        </div>
      </section>

      <!-- 表单组件 -->
      <section class="demo-section animate-on-scroll animate-fade-in-up">
        <h2 class="section-title">表单组件</h2>
        <div class="form-demo">
          <div class="input-group">
            <label class="input-label">用户名</label>
            <input class="input" type="text" placeholder="请输入用户名" v-model="formData.username">
          </div>
          <div class="input-group">
            <label class="input-label">邮箱</label>
            <input class="input" type="email" placeholder="请输入邮箱" v-model="formData.email">
          </div>
          <div class="input-group">
            <label class="input-label">状态</label>
            <select class="select" v-model="formData.status">
              <option value="">请选择状态</option>
              <option value="active">激活</option>
              <option value="inactive">未激活</option>
              <option value="pending">待处理</option>
            </select>
          </div>
          <div class="input-group">
            <label class="input-label">错误状态演示</label>
            <input class="input input-error" type="text" placeholder="这是一个错误状态的输入框">
          </div>
        </div>
      </section>

      <!-- 标签组件 -->
      <section class="demo-section animate-on-scroll animate-fade-in-up">
        <h2 class="section-title">标签组件</h2>
        <div class="tag-demo">
          <span class="tag tag-primary">主要标签</span>
          <span class="tag tag-success">成功标签</span>
          <span class="tag tag-warning">警告标签</span>
          <span class="tag tag-danger">危险标签</span>
          <span class="tag tag-info">信息标签</span>
          <span class="tag tag-gray">灰色标签</span>
        </div>
      </section>

      <!-- 进度条组件 -->
      <section class="demo-section animate-on-scroll animate-fade-in-up">
        <h2 class="section-title">进度条组件</h2>
        <div class="progress-demo">
          <div class="progress-item">
            <span class="progress-label">默认进度 (75%)</span>
            <div class="progress">
              <div class="progress-bar" :style="{ width: '75%' }"></div>
            </div>
          </div>
          <div class="progress-item">
            <span class="progress-label">成功进度 (60%)</span>
            <div class="progress progress-success">
              <div class="progress-bar" :style="{ width: '60%' }"></div>
            </div>
          </div>
          <div class="progress-item">
            <span class="progress-label">警告进度 (90%)</span>
            <div class="progress progress-warning">
              <div class="progress-bar" :style="{ width: '90%' }"></div>
            </div>
          </div>
        </div>
      </section>

      <!-- 加载动画 -->
      <section class="demo-section animate-on-scroll animate-fade-in-up">
        <h2 class="section-title">加载动画</h2>
        <div class="loading-demo">
          <div class="loading-item">
            <div class="loading-spinner"></div>
            <span>旋转加载</span>
          </div>
          <div class="loading-item">
            <div class="loading-dots">
              <span></span>
              <span></span>
              <span></span>
            </div>
            <span>点状加载</span>
          </div>
          <div class="loading-item">
            <div class="loading-wave">
              <span></span>
              <span></span>
              <span></span>
              <span></span>
              <span></span>
            </div>
            <span>波浪加载</span>
          </div>
          <div class="loading-item">
            <div class="loading-orbit"></div>
            <span>轨道加载</span>
          </div>
        </div>
      </section>

      <!-- 特殊效果 -->
      <section class="demo-section animate-on-scroll animate-fade-in-up">
        <h2 class="section-title">特殊效果</h2>
        <div class="effects-demo">
          <div class="effect-item glow">
            <h4>发光效果</h4>
            <p>边框发光动画</p>
          </div>
          <div class="effect-item neon">
            <h4>霓虹效果</h4>
            <p>文字霓虹闪烁</p>
          </div>
          <div class="effect-item pulse-scale">
            <h4>脉冲效果</h4>
            <p>缩放脉冲动画</p>
          </div>
          <div class="effect-item float">
            <h4>浮动效果</h4>
            <p>上下浮动动画</p>
          </div>
        </div>
      </section>

      <!-- 响应式网格 -->
      <section class="demo-section animate-on-scroll animate-fade-in-up">
        <h2 class="section-title">响应式网格</h2>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div class="card" v-for="i in 8" :key="i">
            <h4>网格项 {{ i }}</h4>
            <p>响应式网格布局演示</p>
          </div>
        </div>
      </section>

      <!-- 交互演示 -->
      <section class="demo-section animate-on-scroll animate-fade-in-up">
        <h2 class="section-title">交互演示</h2>
        <div class="interaction-demo">
          <button class="btn btn-primary" @click="showNotification('success')">
            显示成功通知
          </button>
          <button class="btn btn-warning" @click="showNotification('warning')">
            显示警告通知
          </button>
          <button class="btn btn-danger" @click="showNotification('error')">
            显示错误通知
          </button>
          <button class="btn btn-secondary" @click="toggleTheme">
            切换主题
          </button>
          <button class="btn btn-ghost" @click="toggleLoading">
            {{ isLoading ? '停止加载' : '开始加载' }}
          </button>
        </div>
      </section>

      <!-- 当前状态显示 -->
      <section class="demo-section animate-on-scroll animate-fade-in-up">
        <h2 class="section-title">当前状态</h2>
        <div class="status-demo">
          <div class="status-item">
            <span class="status-label">当前主题:</span>
            <span class="tag tag-primary">{{ currentTheme }}</span>
          </div>
          <div class="status-item">
            <span class="status-label">屏幕断点:</span>
            <span class="tag tag-info">{{ currentBreakpoint }}</span>
          </div>
          <div class="status-item">
            <span class="status-label">屏幕宽度:</span>
            <span class="tag tag-gray">{{ screenWidth }}px</span>
          </div>
          <div class="status-item">
            <span class="status-label">加载状态:</span>
            <span class="tag" :class="isLoading ? 'tag-warning' : 'tag-success'">
              {{ isLoading ? '加载中' : '空闲' }}
            </span>
          </div>
        </div>
      </section>
    </div>

    <!-- 通知容器 -->
    <div class="notification-container">
      <transition-group name="list">
        <div
          v-for="notification in notifications"
          :key="notification.id"
          :class="['notification', `notification-${notification.type}`]"
        >
          <h4>{{ notification.title }}</h4>
          <p v-if="notification.message">{{ notification.message }}</p>
          <button 
            class="notification-close" 
            @click="removeNotification(notification.id)"
          >
            ×
          </button>
        </div>
      </transition-group>
    </div>

    <!-- 加载遮罩 -->
    <div v-if="isLoading" class="loading-overlay">
      <div class="loading-content">
        <div class="loading-spinner"></div>
        <p>{{ loadingText }}</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useDesignSystem } from '@/composables/useDesignSystem'

const {
  theme: { currentTheme, toggleTheme },
  loadingState: { isLoading, loadingText, startLoading, stopLoading },
  notification: { notifications, success, warning, error, removeNotification },
  breakpoints: { currentBreakpoint, screenWidth },
  scrollAnimation: { initObserver }
} = useDesignSystem()

// 表单数据
const formData = ref({
  username: '',
  email: '',
  status: ''
})

// 显示通知
const showNotification = (type: 'success' | 'warning' | 'error') => {
  const messages = {
    success: { title: '操作成功', message: '您的操作已经成功完成！' },
    warning: { title: '注意警告', message: '请检查您的输入信息。' },
    error: { title: '操作失败', message: '发生了错误，请稍后重试。' }
  }
  
  const { title, message } = messages[type]
  
  if (type === 'success') {
    success(title, message)
  } else if (type === 'warning') {
    warning(title, message)
  } else {
    error(title, message)
  }
}

// 切换加载状态
const toggleLoading = () => {
  if (isLoading.value) {
    stopLoading()
  } else {
    startLoading('正在处理请求...')
    setTimeout(() => {
      stopLoading()
    }, 3000)
  }
}

onMounted(() => {
  // 初始化滚动动画观察器
  setTimeout(() => {
    initObserver()
  }, 100)
})
</script>

<style scoped>
.design-system-demo {
  min-height: 100vh;
  padding: var(--spacing-8);
}

.demo-container {
  max-width: 1200px;
  margin: 0 auto;
}

.demo-header {
  text-align: center;
  margin-bottom: var(--spacing-16);
}

.demo-title {
  font-size: var(--font-size-5xl);
  font-weight: var(--font-weight-bold);
  color: white;
  margin-bottom: var(--spacing-4);
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.demo-subtitle {
  font-size: var(--font-size-xl);
  color: rgba(255, 255, 255, 0.8);
  margin-bottom: 0;
}

.demo-section {
  margin-bottom: var(--spacing-16);
}

.section-title {
  font-size: var(--font-size-2xl);
  font-weight: var(--font-weight-semibold);
  color: white;
  margin-bottom: var(--spacing-8);
  text-align: center;
}

/* 色彩网格 */
.color-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: var(--spacing-4);
}

.color-item {
  text-align: center;
}

.color-swatch {
  width: 80px;
  height: 80px;
  border-radius: var(--radius-xl);
  margin: 0 auto var(--spacing-2);
  box-shadow: var(--shadow-lg);
  transition: transform var(--duration-200) var(--ease-out);
}

.color-swatch:hover {
  transform: scale(1.1);
}

.color-primary { background: var(--color-primary); }
.color-success { background: var(--color-success); }
.color-warning { background: var(--color-warning); }
.color-danger { background: var(--color-danger); }
.color-info { background: var(--color-info); }

.color-item span {
  font-size: var(--font-size-sm);
  color: rgba(255, 255, 255, 0.8);
}

/* 按钮网格 */
.button-grid {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-4);
  justify-content: center;
}

/* 卡片网格 */
.card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: var(--spacing-6);
}

/* 表单演示 */
.form-demo {
  max-width: 500px;
  margin: 0 auto;
}

.input-group {
  margin-bottom: var(--spacing-4);
}

.input-label {
  display: block;
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: rgba(255, 255, 255, 0.9);
  margin-bottom: var(--spacing-2);
}

/* 标签演示 */
.tag-demo {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-2);
  justify-content: center;
}

/* 进度条演示 */
.progress-demo {
  max-width: 400px;
  margin: 0 auto;
}

.progress-item {
  margin-bottom: var(--spacing-4);
}

.progress-label {
  display: block;
  font-size: var(--font-size-sm);
  color: rgba(255, 255, 255, 0.8);
  margin-bottom: var(--spacing-2);
}

/* 加载演示 */
.loading-demo {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: var(--spacing-6);
}

.loading-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--spacing-2);
  color: rgba(255, 255, 255, 0.8);
  font-size: var(--font-size-sm);
}

/* 特效演示 */
.effects-demo {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: var(--spacing-4);
}

.effect-item {
  background: var(--gradient-card);
  backdrop-filter: var(--backdrop-blur);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: var(--radius-xl);
  padding: var(--spacing-6);
  text-align: center;
}

.effect-item h4 {
  color: white;
  margin-bottom: var(--spacing-2);
}

.effect-item p {
  color: rgba(255, 255, 255, 0.7);
  font-size: var(--font-size-sm);
}

/* 交互演示 */
.interaction-demo {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-4);
  justify-content: center;
}

/* 状态演示 */
.status-demo {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: var(--spacing-4);
}

.status-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  padding: var(--spacing-3);
  background: rgba(255, 255, 255, 0.1);
  border-radius: var(--radius-lg);
}

.status-label {
  font-size: var(--font-size-sm);
  color: rgba(255, 255, 255, 0.8);
}

/* 通知容器 */
.notification-container {
  position: fixed;
  top: var(--spacing-4);
  right: var(--spacing-4);
  z-index: var(--z-index-toast);
  max-width: 300px;
}

.notification-close {
  position: absolute;
  top: var(--spacing-2);
  right: var(--spacing-2);
  width: 24px;
  height: 24px;
  border: none;
  background: rgba(255, 255, 255, 0.2);
  color: white;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: var(--font-size-lg);
  line-height: 1;
  transition: background-color var(--duration-200) var(--ease-out);
}

.notification-close:hover {
  background: rgba(255, 255, 255, 0.3);
}

/* 加载遮罩 */
.loading-overlay {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.8);
  backdrop-filter: var(--backdrop-blur);
  z-index: var(--z-index-modal);
  display: flex;
  align-items: center;
  justify-content: center;
}

.loading-content {
  text-align: center;
  color: white;
}

.loading-content .loading-spinner {
  width: 60px;
  height: 60px;
  border-width: 4px;
  margin-bottom: var(--spacing-4);
}

.loading-content p {
  font-size: var(--font-size-lg);
  margin: 0;
}

/* 响应式调整 */
@media (max-width: 768px) {
  .design-system-demo {
    padding: var(--spacing-4);
  }
  
  .demo-title {
    font-size: var(--font-size-3xl);
  }
  
  .demo-subtitle {
    font-size: var(--font-size-lg);
  }
  
  .card-grid {
    grid-template-columns: 1fr;
  }
  
  .button-grid,
  .interaction-demo {
    justify-content: stretch;
  }
  
  .button-grid .btn,
  .interaction-demo .btn {
    flex: 1;
    min-width: 0;
  }
}
</style>