import type { TaskStatus, Task } from '@/types'

/**
 * 任务相关工具函数
 */

// 任务状态配置
export const TASK_STATUS_CONFIG = {
  pending: {
    text: '待处理',
    type: 'info' as const,
    color: '#909399',
    progress: 10
  },
  recognizing: {
    text: '识别中',
    type: 'warning' as const,
    color: '#E6A23C',
    progress: 25
  },
  tracking: {
    text: '查询物流中',
    type: 'warning' as const,
    color: '#E6A23C',
    progress: 50
  },
  delivered: {
    text: '已签收',
    type: 'success' as const,
    color: '#67C23A',
    progress: 75
  },
  generating: {
    text: '生成文档中',
    type: 'warning' as const,
    color: '#E6A23C',
    progress: 90
  },
  completed: {
    text: '已完成',
    type: 'success' as const,
    color: '#67C23A',
    progress: 100
  },
  failed: {
    text: '失败',
    type: 'danger' as const,
    color: '#F56C6C',
    progress: 0
  },
  returned: {
    text: '退签',
    type: 'warning' as const,
    color: '#E6A23C',
    progress: 100
  }
}

/**
 * 获取任务状态配置
 */
export const getTaskStatusConfig = (status: TaskStatus) => {
  return TASK_STATUS_CONFIG[status] || TASK_STATUS_CONFIG.pending
}

/**
 * 获取任务状态文本
 */
export const getTaskStatusText = (status: TaskStatus): string => {
  return getTaskStatusConfig(status).text
}

/**
 * 获取任务状态类型（用于Element Plus标签）
 */
export const getTaskStatusType = (status: TaskStatus): 'success' | 'warning' | 'danger' | 'info' => {
  return getTaskStatusConfig(status).type
}

/**
 * 获取任务进度百分比
 */
export const getTaskProgress = (status: TaskStatus): number => {
  return getTaskStatusConfig(status).progress
}

/**
 * 获取任务进度状态（用于进度条）
 */
export const getTaskProgressStatus = (status: TaskStatus): 'success' | 'exception' | undefined => {
  if (status === 'failed') return 'exception'
  if (status === 'completed') return 'success'
  return undefined
}

/**
 * 判断任务是否处理中
 */
export const isTaskProcessing = (status: TaskStatus): boolean => {
  return ['pending', 'recognizing', 'tracking', 'generating'].includes(status)
}

/**
 * 判断任务是否已完成
 */
export const isTaskCompleted = (status: TaskStatus): boolean => {
  return status === 'completed' || status === 'returned'
}

/**
 * 判断任务是否失败
 */
export const isTaskFailed = (status: TaskStatus): boolean => {
  return status === 'failed'
}

/**
 * 判断任务是否可以手动生成回证
 */
export const canGenerateReceipt = (task: Task): boolean => {
  return task.status === 'delivered' && !task.document_url
}

/**
 * 判断任务是否可以重试
 */
export const canRetryTask = (task: Task): boolean => {
  return task.status === 'failed'
}

/**
 * 判断任务是否可以下载文档
 */
export const canDownloadDocument = (task: Task): boolean => {
  return task.status === 'completed' && !!task.document_url
}

/**
 * 获取任务处理步骤
 */
export const getTaskSteps = () => [
  {
    key: 'uploaded',
    title: '图片上传',
    description: '上传包含二维码的图片'
  },
  {
    key: 'recognized',
    title: '二维码识别',
    description: '识别图片中的二维码'
  },
  {
    key: 'tracking',
    title: '物流查询',
    description: '查询快递物流信息'
  },
  {
    key: 'delivered',
    title: '等待签收',
    description: '等待快递签收'
  },
  {
    key: 'generating',
    title: '生成文档',
    description: '生成送达回证文档'
  },
  {
    key: 'completed',
    title: '任务完成',
    description: '任务处理完成'
  }
]

/**
 * 获取当前步骤索引
 */
export const getCurrentStepIndex = (status: TaskStatus): number => {
  const stepMap = {
    pending: 0,
    recognizing: 1,
    tracking: 2,
    delivered: 3,
    generating: 4,
    completed: 5,
    failed: -1,
    returned: 3  // 退签在物流查询后就结束了
  }
  return stepMap[status] || 0
}

/**
 * 判断步骤是否完成
 */
export const isStepCompleted = (status: TaskStatus, stepKey: string): boolean => {
  const steps = ['uploaded', 'recognized', 'tracking', 'delivered', 'generating', 'completed']
  const currentIndex = getCurrentStepIndex(status)
  const stepIndex = steps.indexOf(stepKey)
  
  if (status === 'failed') {
    return stepKey === 'uploaded' // 失败状态下只有上传是完成的
  }
  
  return stepIndex <= currentIndex
}

/**
 * 获取时间线类型
 */
export const getTimelineType = (status: TaskStatus, stepKey: string): 'success' | 'primary' | 'warning' | 'danger' | 'info' => {
  if (status === 'failed' && stepKey !== 'uploaded') {
    return 'danger'
  }
  return isStepCompleted(status, stepKey) ? 'success' : 'info'
}

/**
 * 格式化文件大小
 */
export const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

/**
 * 格式化日期时间
 */
export const formatDateTime = (dateString: string): string => {
  if (!dateString) return '-'
  return new Date(dateString.replace(/-/g, '/')).toLocaleString('zh-CN')
}

/**
 * 格式化相对时间
 */
export const formatRelativeTime = (dateString: string): string => {
  if (!dateString) return '-'
  
  const now = new Date()
  const date = new Date(dateString.replace(/-/g, '/'))
  const diff = now.getTime() - date.getTime()
  
  const minute = 60 * 1000
  const hour = 60 * minute
  const day = 24 * hour
  const week = 7 * day
  const month = 30 * day
  
  if (diff < minute) {
    return '刚刚'
  } else if (diff < hour) {
    return `${Math.floor(diff / minute)}分钟前`
  } else if (diff < day) {
    return `${Math.floor(diff / hour)}小时前`
  } else if (diff < week) {
    return `${Math.floor(diff / day)}天前`
  } else if (diff < month) {
    return `${Math.floor(diff / week)}周前`
  } else {
    return formatDateTime(dateString)
  }
}

/**
 * 生成任务ID
 */
export const generateTaskId = (): string => {
  const timestamp = Date.now()
  const random = Math.floor(Math.random() * 10000)
  return `task_${timestamp}_${random}`
}

/**
 * 验证文件类型
 */
export const validateImageFile = (file: File): { valid: boolean; message?: string } => {
  const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png']
  const maxSize = 10 * 1024 * 1024 // 10MB
  
  if (!allowedTypes.includes(file.type)) {
    return {
      valid: false,
      message: '只支持 JPG、PNG 格式的图片'
    }
  }
  
  if (file.size > maxSize) {
    return {
      valid: false,
      message: '图片大小不能超过 10MB'
    }
  }
  
  return { valid: true }
}

/**
 * 创建下载链接
 */
export const downloadBlob = (blob: Blob, filename: string): void => {
  const url = window.URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  link.click()
  window.URL.revokeObjectURL(url)
}

/**
 * 任务状态统计
 */
export const calculateTaskStats = (tasks: Task[]) => {
  const stats = {
    total: tasks.length,
    completed: 0,
    pending: 0,
    failed: 0,
    processing: 0
  }
  
  tasks.forEach(task => {
    switch (task.status) {
      case 'completed':
        stats.completed++
        break
      case 'failed':
        stats.failed++
        break
      case 'pending':
        stats.pending++
        break
      default:
        if (isTaskProcessing(task.status)) {
          stats.processing++
        }
        break
    }
  })
  
  return stats
}