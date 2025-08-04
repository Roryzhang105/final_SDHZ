# SDHZ 设计系统

现代化的设计系统，采用毛玻璃效果、微动画和响应式设计。

## 🎨 设计理念

- **现代简约**: 使用毛玻璃效果和微妙的渐变
- **响应式**: 适配所有设备尺寸
- **可访问性**: 支持键盘导航和屏幕阅读器
- **性能优化**: 尊重用户的动画偏好设置
- **一致性**: 统一的设计语言和交互模式

## 🚀 快速开始

### 导入设计系统

```typescript
// main.ts
import './styles/design-system/index.css'
```

### 使用组合式函数

```vue
<script setup>
import { useDesignSystem } from '@/composables/useDesignSystem'

const { theme, loadingState, notification } = useDesignSystem()
</script>
```

## 🎯 核心概念

### 设计令牌 (Design Tokens)

所有设计值都定义为 CSS 变量，确保一致性和可维护性。

```css
:root {
  /* 色彩系统 */
  --color-primary: #5e72e4;
  --color-success: #2dce89;
  --color-warning: #fb6340;
  
  /* 间距系统 */
  --spacing-4: 1rem;
  --spacing-6: 1.5rem;
  
  /* 动画系统 */
  --duration-200: 200ms;
  --ease-out: cubic-bezier(0, 0, 0.2, 1);
}
```

### 色彩系统

#### 主色调
- `--color-primary`: #5E72E4 (现代蓝紫色)
- `--color-primary-light`: #7C8CE6
- `--color-primary-dark`: #4C5AC7

#### 语义色彩
- `--color-success`: #2DCE89 (成功)
- `--color-warning`: #FB6340 (警告)
- `--color-danger`: #F5365C (危险)
- `--color-info`: #11CDEF (信息)

#### 中性色彩
完整的灰度色板，从 `--color-gray-50` 到 `--color-gray-900`

### 间距系统

基于 `0.25rem` (4px) 的倍数系统：

```css
--spacing-1: 0.25rem;  /* 4px */
--spacing-2: 0.5rem;   /* 8px */
--spacing-4: 1rem;     /* 16px */
--spacing-6: 1.5rem;   /* 24px */
--spacing-8: 2rem;     /* 32px */
```

### 字体系统

#### 字体族
```css
--font-family-sans: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
--font-family-mono: 'SF Mono', Monaco, 'Cascadia Code', monospace;
```

#### 字体大小
```css
--font-size-xs: 0.75rem;   /* 12px */
--font-size-sm: 0.875rem;  /* 14px */
--font-size-base: 1rem;    /* 16px */
--font-size-lg: 1.125rem;  /* 18px */
```

## 🧩 组件系统

### 卡片组件

基础卡片具有毛玻璃效果和悬浮动画：

```html
<div class="card">
  <h3>卡片标题</h3>
  <p>卡片内容</p>
</div>
```

变体：
- `card-glass`: 透明毛玻璃效果
- `card-primary`: 主色调卡片
- `card-success`: 成功色调卡片

### 按钮组件

带有涟漪效果和微动画的按钮：

```html
<button class="btn btn-primary">
  主要按钮
</button>

<button class="btn btn-secondary">
  次要按钮
</button>
```

尺寸变体：
- `btn-sm`: 小按钮
- `btn-lg`: 大按钮
- `btn-xl`: 超大按钮

### 输入框组件

带有焦点动画的输入框：

```html
<input class="input" type="text" placeholder="请输入内容">

<input class="input input-error" type="text" placeholder="错误状态">
```

### 标签组件

带有光泽扫描效果的标签：

```html
<span class="tag tag-primary">主要标签</span>
<span class="tag tag-success">成功标签</span>
```

### 进度条组件

带有闪光动画的进度条：

```html
<div class="progress">
  <div class="progress-bar" style="width: 60%"></div>
</div>
```

## 🎭 动画系统

### 页面过渡

```vue
<template>
  <transition name="page">
    <div>页面内容</div>
  </transition>
</template>
```

### 列表动画

```vue
<template>
  <transition-group name="list">
    <div v-for="item in items" :key="item.id">
      {{ item.name }}
    </div>
  </transition-group>
</template>
```

### 滚动动画

```html
<div class="animate-on-scroll animate-fade-in-up">
  滚动时出现的内容
</div>
```

### 悬浮效果

```html
<div class="hover-lift">悬浮上升</div>
<div class="hover-scale">悬浮缩放</div>
<div class="hover-glow">悬浮发光</div>
```

## 📱 响应式系统

### 断点系统

```css
--breakpoint-sm: 576px;
--breakpoint-md: 768px;
--breakpoint-lg: 992px;
--breakpoint-xl: 1200px;
--breakpoint-2xl: 1400px;
```

### 栅格系统

基于 CSS Grid 的 12 列栅格：

```html
<div class="grid grid-cols-12 gap-4">
  <div class="col-span-6 md:col-span-4">内容</div>
  <div class="col-span-6 md:col-span-8">内容</div>
</div>
```

### Flexbox 布局

```html
<div class="flex justify-between items-center gap-4">
  <div>左侧内容</div>
  <div>右侧内容</div>
</div>
```

## 🎨 特殊效果

### 毛玻璃效果

```css
.glass-card {
  background: var(--gradient-glass);
  backdrop-filter: var(--backdrop-blur);
  border: 1px solid rgba(255, 255, 255, 0.2);
}
```

### 渐变背景

```css
.gradient-primary {
  background: var(--gradient-primary);
}

.gradient-card {
  background: var(--gradient-card);
}
```

### 发光效果

```html
<div class="glow">发光边框</div>
<div class="neon">霓虹文字</div>
```

## 🔧 组合式函数

### 主题管理

```typescript
const { currentTheme, toggleTheme } = useTheme()

// 切换主题
toggleTheme()
```

### 加载状态

```typescript
const { isLoading, withLoading } = useLoadingState()

// 包装异步操作
await withLoading(async () => {
  await fetchData()
}, '正在加载数据...')
```

### 通知系统

```typescript
const { success, error, warning } = useNotification()

success('操作成功', '数据已保存')
error('操作失败', '请检查网络连接')
```

### 滚动动画

```typescript
const { observeElement } = useScrollAnimation()

// 观察新元素
observeElement(element)
```

### 响应式断点

```typescript
const { currentBreakpoint, isBreakpointOrAbove } = useBreakpoints()

// 检查断点
if (isBreakpointOrAbove('md')) {
  // 中等屏幕及以上
}
```

## 🎯 最佳实践

### 1. 使用设计令牌

❌ 避免硬编码值：
```css
.my-component {
  color: #5e72e4;
  padding: 16px;
}
```

✅ 使用设计令牌：
```css
.my-component {
  color: var(--color-primary);
  padding: var(--spacing-4);
}
```

### 2. 遵循组件命名

❌ 不规范的命名：
```css
.my-blue-button { }
.card-container { }
```

✅ 规范的命名：
```css
.btn-primary { }
.card { }
```

### 3. 响应式优先

❌ 固定尺寸：
```css
.sidebar {
  width: 250px;
}
```

✅ 响应式设计：
```css
.sidebar {
  width: 250px;
}

@media (max-width: 768px) {
  .sidebar {
    width: 100%;
  }
}
```

### 4. 性能考虑

- 使用 `will-change` 属性优化动画性能
- 尊重 `prefers-reduced-motion` 设置
- 避免过度使用阴影和滤镜

### 5. 可访问性

- 确保足够的颜色对比度
- 提供键盘导航支持
- 使用语义化的 HTML 结构
- 为动态内容提供替代文本

## 🌙 深色模式

系统自动支持深色模式，会根据用户系统偏好或手动设置切换：

```css
@media (prefers-color-scheme: dark) {
  :root {
    --color-bg-primary: var(--color-gray-900);
    --color-bg-secondary: var(--color-gray-800);
  }
}
```

## 🖨️ 打印样式

系统包含优化的打印样式：

```css
@media print {
  .no-print { display: none !important; }
  * {
    background: white !important;
    color: black !important;
  }
}
```

## 🔍 调试工具

### 布局调试

临时添加此类来可视化布局：

```css
.debug * {
  outline: 1px solid red !important;
}
```

### 动画调试

减慢所有动画以便调试：

```css
.debug-animations * {
  animation-duration: 5s !important;
  transition-duration: 5s !important;
}
```

## 📚 扩展系统

### 添加新的设计令牌

在 `tokens.css` 中添加：

```css
:root {
  --color-brand-new: #123456;
  --spacing-custom: 2.5rem;
}
```

### 创建新组件

遵循现有的模式和命名约定：

```css
.new-component {
  background: var(--gradient-card);
  border-radius: var(--radius-lg);
  padding: var(--spacing-4);
  transition: all var(--duration-200) var(--ease-out);
}

.new-component:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-lg);
}
```

## 🤝 贡献指南

1. 遵循现有的命名约定
2. 保持设计一致性
3. 考虑性能影响
4. 测试响应式行为
5. 确保可访问性
6. 更新文档

## 📄 许可证

此设计系统遵循项目整体许可证。