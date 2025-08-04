/**
 * useScrollAnimation - 滚动动画组合式函数
 * 监听滚动事件，当元素进入视口时触发动画
 */

import { onMounted, onUnmounted } from 'vue'

interface ScrollAnimationOptions {
  /**
   * 元素选择器，默认为 '.animate-on-scroll'
   */
  selector?: string
  /**
   * 触发动画的阈值，0.1 表示元素 10% 进入视口时触发
   */
  threshold?: number
  /**
   * 根边距，用于提前或延迟触发动画
   */
  rootMargin?: string
  /**
   * 是否只触发一次动画
   */
  once?: boolean
}

export function useScrollAnimation(options: ScrollAnimationOptions = {}) {
  const {
    selector = '.animate-on-scroll',
    threshold = 0.1,
    rootMargin = '0px 0px -50px 0px',
    once = true
  } = options

  let observer: IntersectionObserver | null = null

  const initScrollAnimation = () => {
    // 检查浏览器是否支持 IntersectionObserver
    if (!window.IntersectionObserver) {
      // 不支持的情况下，直接显示所有元素
      const elements = document.querySelectorAll(selector)
      elements.forEach(el => {
        el.classList.add('in-view')
      })
      return
    }

    // 创建 Intersection Observer
    observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            // 元素进入视口，添加 in-view 类
            entry.target.classList.add('in-view')
            
            // 如果设置了只触发一次，则停止观察该元素
            if (once) {
              observer?.unobserve(entry.target)
            }
          } else if (!once) {
            // 如果不是只触发一次，元素离开视口时移除 in-view 类
            entry.target.classList.remove('in-view')
          }
        })
      },
      {
        threshold,
        rootMargin
      }
    )

    // 查找所有需要动画的元素
    const animateElements = document.querySelectorAll(selector)
    
    // 开始观察这些元素
    animateElements.forEach((el) => {
      observer?.observe(el)
    })
  }

  const destroyScrollAnimation = () => {
    if (observer) {
      observer.disconnect()
      observer = null
    }
  }

  const refreshElements = () => {
    // 重新扫描元素，用于动态添加的内容
    if (observer) {
      const animateElements = document.querySelectorAll(selector)
      animateElements.forEach((el) => {
        if (!el.classList.contains('in-view')) {
          observer?.observe(el)
        }
      })
    }
  }

  // 立即显示所有动画元素（备用方案）
  const showAllElements = () => {
    const elements = document.querySelectorAll(selector)
    elements.forEach(el => {
      el.classList.add('in-view')
    })
  }

  // 隐藏所有动画元素
  const hideAllElements = () => {
    const elements = document.querySelectorAll(selector)
    elements.forEach(el => {
      el.classList.remove('in-view')
    })
  }

  onMounted(() => {
    // 使用 nextTick 确保 DOM 已经渲染完成
    setTimeout(() => {
      initScrollAnimation()
    }, 100)
  })

  onUnmounted(() => {
    destroyScrollAnimation()
  })

  return {
    initScrollAnimation,
    destroyScrollAnimation,
    refreshElements,
    showAllElements,
    hideAllElements
  }
}

/**
 * 检查是否偏好减少动画
 */
export function prefersReducedMotion(): boolean {
  return window.matchMedia('(prefers-reduced-motion: reduce)').matches
}

/**
 * 为单个元素添加滚动动画
 */
export function addScrollAnimation(
  element: HTMLElement,
  animationClass: string = 'animate-fade-in-up'
) {
  element.classList.add('animate-on-scroll', animationClass)
}

/**
 * 移除元素的滚动动画
 */
export function removeScrollAnimation(element: HTMLElement) {
  element.classList.remove('animate-on-scroll', 'in-view')
  // 移除所有动画类
  const animationClasses = [
    'animate-fade-in-up',
    'animate-fade-in-down', 
    'animate-fade-in-left',
    'animate-fade-in-right'
  ]
  element.classList.remove(...animationClasses)
}