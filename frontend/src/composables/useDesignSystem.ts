/**
 * 设计系统组合式函数
 * 提供动画、主题和 UI 交互的统一接口
 */

import { ref, onMounted, onUnmounted, nextTick } from 'vue'

/**
 * 页面过渡动画
 */
export function usePageTransition() {
  const isTransitioning = ref(false)
  
  const startTransition = () => {
    isTransitioning.value = true
  }
  
  const endTransition = () => {
    isTransitioning.value = false
  }
  
  return {
    isTransitioning,
    startTransition,
    endTransition
  }
}

/**
 * 滚动动画观察器
 */
export function useScrollAnimation(threshold: number = 0.1) {
  const animatedElements = ref<Set<Element>>(new Set())
  let observer: IntersectionObserver | null = null
  
  const initObserver = () => {
    if (typeof window === 'undefined') return
    
    observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add('in-view')
            animatedElements.value.add(entry.target)
            observer?.unobserve(entry.target)
          }
        })
      },
      {
        threshold,
        rootMargin: '0px 0px -50px 0px'
      }
    )
    
    // 观察所有带有 animate-on-scroll 类的元素
    const elements = document.querySelectorAll('.animate-on-scroll')
    elements.forEach((el) => observer?.observe(el))
  }
  
  const observeElement = (element: Element) => {
    if (observer && element) {
      observer.observe(element)
    }
  }
  
  const unobserveElement = (element: Element) => {
    if (observer && element) {
      observer.unobserve(element)
      animatedElements.value.delete(element)
    }
  }
  
  onMounted(() => {
    nextTick(() => {
      initObserver()
    })
  })
  
  onUnmounted(() => {
    if (observer) {
      observer.disconnect()
      observer = null
    }
    animatedElements.value.clear()
  })
  
  return {
    animatedElements,
    observeElement,
    unobserveElement,
    initObserver
  }
}

/**
 * 涟漪效果
 */
export function useRippleEffect() {
  const createRipple = (event: MouseEvent, element: Element) => {
    const rect = element.getBoundingClientRect()
    const size = Math.max(rect.width, rect.height)
    const x = event.clientX - rect.left - size / 2
    const y = event.clientY - rect.top - size / 2
    
    const ripple = document.createElement('span')
    ripple.style.cssText = `
      position: absolute;
      border-radius: 50%;
      transform: scale(0);
      animation: ripple 600ms linear;
      background-color: rgba(255, 255, 255, 0.6);
      left: ${x}px;
      top: ${y}px;
      width: ${size}px;
      height: ${size}px;
      pointer-events: none;
      z-index: 1000;
    `
    
    const style = document.createElement('style')
    style.textContent = `
      @keyframes ripple {
        to {
          transform: scale(4);
          opacity: 0;
        }
      }
    `
    
    if (!document.head.querySelector('[data-ripple-style]')) {
      style.setAttribute('data-ripple-style', '')
      document.head.appendChild(style)
    }
    
    element.appendChild(ripple)
    
    ripple.addEventListener('animationend', () => {
      ripple.remove()
    })
  }
  
  const addRippleEffect = (element: Element) => {
    element.addEventListener('click', (event) => {
      createRipple(event as MouseEvent, element)
    })
  }
  
  return {
    createRipple,
    addRippleEffect
  }
}

/**
 * 主题管理
 */
export function useTheme() {
  const currentTheme = ref<'light' | 'dark'>('light')
  const systemPrefersDark = ref(false)
  
  const updateSystemPreference = () => {
    if (typeof window !== 'undefined') {
      systemPrefersDark.value = window.matchMedia('(prefers-color-scheme: dark)').matches
    }
  }
  
  const toggleTheme = () => {
    currentTheme.value = currentTheme.value === 'light' ? 'dark' : 'light'
    applyTheme()
  }
  
  const setTheme = (theme: 'light' | 'dark') => {
    currentTheme.value = theme
    applyTheme()
  }
  
  const applyTheme = () => {
    if (typeof document !== 'undefined') {
      document.documentElement.setAttribute('data-theme', currentTheme.value)
      localStorage.setItem('theme', currentTheme.value)
    }
  }
  
  const initTheme = () => {
    if (typeof window !== 'undefined') {
      // 从 localStorage 获取保存的主题
      const savedTheme = localStorage.getItem('theme') as 'light' | 'dark' | null
      
      if (savedTheme) {
        currentTheme.value = savedTheme
      } else {
        // 使用系统偏好
        updateSystemPreference()
        currentTheme.value = systemPrefersDark.value ? 'dark' : 'light'
      }
      
      applyTheme()
      
      // 监听系统主题变化
      const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
      mediaQuery.addEventListener('change', updateSystemPreference)
      
      return () => {
        mediaQuery.removeEventListener('change', updateSystemPreference)
      }
    }
  }
  
  onMounted(() => {
    const cleanup = initTheme()
    
    onUnmounted(() => {
      cleanup?.()
    })
  })
  
  return {
    currentTheme,
    systemPrefersDark,
    toggleTheme,
    setTheme,
    initTheme
  }
}

/**
 * 毛玻璃效果
 */
export function useGlassEffect() {
  const createGlassCard = (element: Element, intensity: 'light' | 'medium' | 'heavy' = 'medium') => {
    const intensityClasses = {
      light: 'glass-light',
      medium: 'glass-medium',
      heavy: 'glass-heavy'
    }
    
    element.classList.add('glass-effect', intensityClasses[intensity])
  }
  
  const removeGlassEffect = (element: Element) => {
    element.classList.remove('glass-effect', 'glass-light', 'glass-medium', 'glass-heavy')
  }
  
  return {
    createGlassCard,
    removeGlassEffect
  }
}

/**
 * 悬浮效果
 */
export function useHoverEffects() {
  const addHoverLift = (element: Element, intensity: 'light' | 'medium' | 'heavy' = 'medium') => {
    const intensityClasses = {
      light: 'hover-lift-light',
      medium: 'hover-lift',
      heavy: 'hover-lift-heavy'
    }
    
    element.classList.add(intensityClasses[intensity])
  }
  
  const addHoverGlow = (element: Element, color: 'primary' | 'success' | 'warning' | 'danger' = 'primary') => {
    element.classList.add('hover-glow', `hover-glow-${color}`)
  }
  
  const addHoverScale = (element: Element) => {
    element.classList.add('hover-scale')
  }
  
  return {
    addHoverLift,
    addHoverGlow,
    addHoverScale
  }
}

/**
 * 加载状态管理
 */
export function useLoadingState() {
  const isLoading = ref(false)
  const loadingText = ref('加载中...')
  
  const startLoading = (text?: string) => {
    isLoading.value = true
    if (text) loadingText.value = text
  }
  
  const stopLoading = () => {
    isLoading.value = false
  }
  
  const withLoading = async <T>(
    asyncFn: () => Promise<T>,
    text?: string
  ): Promise<T> => {
    startLoading(text)
    try {
      const result = await asyncFn()
      return result
    } finally {
      stopLoading()
    }
  }
  
  return {
    isLoading,
    loadingText,
    startLoading,
    stopLoading,
    withLoading
  }
}

/**
 * 通知系统
 */
export function useNotification() {
  const notifications = ref<Array<{
    id: string
    type: 'success' | 'warning' | 'error' | 'info'
    title: string
    message?: string
    duration?: number
    action?: () => void
    actionText?: string
  }>>([])
  
  const addNotification = (notification: Omit<typeof notifications.value[0], 'id'>) => {
    const id = Math.random().toString(36).substr(2, 9)
    const newNotification = {
      ...notification,
      id,
      duration: notification.duration ?? 5000
    }
    
    notifications.value.push(newNotification)
    
    if (newNotification.duration > 0) {
      setTimeout(() => {
        removeNotification(id)
      }, newNotification.duration)
    }
    
    return id
  }
  
  const removeNotification = (id: string) => {
    const index = notifications.value.findIndex(n => n.id === id)
    if (index > -1) {
      notifications.value.splice(index, 1)
    }
  }
  
  const clearAllNotifications = () => {
    notifications.value = []
  }
  
  const success = (title: string, message?: string, duration?: number) => {
    return addNotification({ type: 'success', title, message, duration })
  }
  
  const warning = (title: string, message?: string, duration?: number) => {
    return addNotification({ type: 'warning', title, message, duration })
  }
  
  const error = (title: string, message?: string, duration?: number) => {
    return addNotification({ type: 'error', title, message, duration: duration ?? 0 })
  }
  
  const info = (title: string, message?: string, duration?: number) => {
    return addNotification({ type: 'info', title, message, duration })
  }
  
  return {
    notifications,
    addNotification,
    removeNotification,
    clearAllNotifications,
    success,
    warning,
    error,
    info
  }
}

/**
 * 响应式断点
 */
export function useBreakpoints() {
  const breakpoints = {
    xs: 0,
    sm: 576,
    md: 768,
    lg: 992,
    xl: 1200,
    '2xl': 1400
  }
  
  const currentBreakpoint = ref<keyof typeof breakpoints>('lg')
  const screenWidth = ref(0)
  
  const updateBreakpoint = () => {
    if (typeof window !== 'undefined') {
      screenWidth.value = window.innerWidth
      
      if (screenWidth.value >= breakpoints['2xl']) {
        currentBreakpoint.value = '2xl'
      } else if (screenWidth.value >= breakpoints.xl) {
        currentBreakpoint.value = 'xl'
      } else if (screenWidth.value >= breakpoints.lg) {
        currentBreakpoint.value = 'lg'
      } else if (screenWidth.value >= breakpoints.md) {
        currentBreakpoint.value = 'md'
      } else if (screenWidth.value >= breakpoints.sm) {
        currentBreakpoint.value = 'sm'
      } else {
        currentBreakpoint.value = 'xs'
      }
    }
  }
  
  onMounted(() => {
    updateBreakpoint()
    window.addEventListener('resize', updateBreakpoint)
  })
  
  onUnmounted(() => {
    if (typeof window !== 'undefined') {
      window.removeEventListener('resize', updateBreakpoint)
    }
  })
  
  const isBreakpoint = (breakpoint: keyof typeof breakpoints) => {
    return currentBreakpoint.value === breakpoint
  }
  
  const isBreakpointOrAbove = (breakpoint: keyof typeof breakpoints) => {
    return screenWidth.value >= breakpoints[breakpoint]
  }
  
  const isBreakpointOrBelow = (breakpoint: keyof typeof breakpoints) => {
    return screenWidth.value <= breakpoints[breakpoint]
  }
  
  return {
    breakpoints,
    currentBreakpoint,
    screenWidth,
    isBreakpoint,
    isBreakpointOrAbove,
    isBreakpointOrBelow
  }
}

/**
 * 性能优化
 */
export function usePerformance() {
  const prefersReducedMotion = ref(false)
  
  const checkReducedMotion = () => {
    if (typeof window !== 'undefined') {
      prefersReducedMotion.value = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    }
  }
  
  const optimizeForPerformance = () => {
    if (prefersReducedMotion.value) {
      document.documentElement.classList.add('reduce-motion')
    } else {
      document.documentElement.classList.remove('reduce-motion')
    }
  }
  
  onMounted(() => {
    checkReducedMotion()
    optimizeForPerformance()
    
    if (typeof window !== 'undefined') {
      const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)')
      mediaQuery.addEventListener('change', () => {
        checkReducedMotion()
        optimizeForPerformance()
      })
      
      onUnmounted(() => {
        mediaQuery.removeEventListener('change', checkReducedMotion)
      })
    }
  })
  
  return {
    prefersReducedMotion,
    optimizeForPerformance
  }
}

/**
 * 完整的设计系统钩子
 * 整合所有功能
 */
export function useDesignSystem() {
  const pageTransition = usePageTransition()
  const scrollAnimation = useScrollAnimation()
  const rippleEffect = useRippleEffect()
  const theme = useTheme()
  const glassEffect = useGlassEffect()
  const hoverEffects = useHoverEffects()
  const loadingState = useLoadingState()
  const notification = useNotification()
  const breakpoints = useBreakpoints()
  const performance = usePerformance()
  
  return {
    pageTransition,
    scrollAnimation,
    rippleEffect,
    theme,
    glassEffect,
    hoverEffects,
    loadingState,
    notification,
    breakpoints,
    performance
  }
}