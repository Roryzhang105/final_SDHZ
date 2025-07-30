import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { tasksApi } from '@/api/tasks'
import type { 
  Task, 
  TaskStatus, 
  TaskListParams, 
  TaskUpdateData 
} from '@/types'

export const useTasksStore = defineStore('tasks', () => {
  // 状态
  const taskList = ref<Task[]>([])
  const currentTask = ref<Task | null>(null)
  const loading = ref(false)
  const uploading = ref(false)
  
  // 分页信息
  const pagination = ref({
    page: 1,
    size: 20,
    total: 0
  })

  // 筛选条件
  const filters = ref<TaskListParams>({
    page: 1,
    size: 20,
    task_id: '',
    tracking_number: '',
    status: '',
    sort_by: 'created_desc'
  })

  // 统计信息
  const stats = ref({
    total: 0,
    completed: 0,
    pending: 0,
    failed: 0
  })

  // 最近活动
  const recentActivities = ref<Array<{
    id: string
    taskId: string
    description: string
    time: string
    type: 'success' | 'info' | 'warning' | 'error'
  }>>([])

  // Getters
  const processingTasks = computed(() => 
    taskList.value.filter(task => 
      ['pending', 'recognizing', 'tracking', 'generating'].includes(task.status)
    )
  )

  const completedTasks = computed(() => 
    taskList.value.filter(task => task.status === 'completed')
  )

  const failedTasks = computed(() => 
    taskList.value.filter(task => task.status === 'failed')
  )

  const hasProcessingTasks = computed(() => 
    processingTasks.value.length > 0
  )

  // Actions
  
  /**
   * 上传图片
   */
  const uploadImage = async (file: File) => {
    try {
      uploading.value = true
      const response = await tasksApi.uploadImage(file)
      
      if (response.success) {
        ElMessage.success('图片上传成功，任务已创建')
        // 刷新任务列表
        await getTaskList()
        return response.data
      } else {
        throw new Error(response.message || '上传失败')
      }
    } catch (error) {
      console.error('Upload image failed:', error)
      ElMessage.error(error instanceof Error ? error.message : '上传失败')
      throw error
    } finally {
      uploading.value = false
    }
  }

  /**
   * 批量上传图片
   */
  const uploadImages = async (files: File[]) => {
    try {
      uploading.value = true
      const responses = await tasksApi.uploadImages(files)
      
      const successCount = responses.filter(r => r.success).length
      const failedCount = responses.length - successCount
      
      if (successCount > 0) {
        ElMessage.success(`成功上传 ${successCount} 张图片`)
        // 刷新任务列表
        await getTaskList()
      }
      
      if (failedCount > 0) {
        ElMessage.warning(`有 ${failedCount} 张图片上传失败`)
      }
      
      return responses
    } catch (error) {
      console.error('Batch upload failed:', error)
      ElMessage.error('批量上传失败')
      throw error
    } finally {
      uploading.value = false
    }
  }

  /**
   * 获取任务列表
   */
  const getTaskList = async (params?: Partial<TaskListParams>) => {
    try {
      loading.value = true
      
      const queryParams = {
        ...filters.value,
        ...params
      }
      
      const response = await tasksApi.getTaskList(queryParams)
      
      if (response.success) {
        taskList.value = response.data.items
        pagination.value = {
          page: response.data.page,
          size: response.data.size,
          total: response.data.total
        }
      } else {
        throw new Error(response.message || '获取任务列表失败')
      }
    } catch (error) {
      console.error('Get task list failed:', error)
      ElMessage.error('获取任务列表失败')
      throw error
    } finally {
      loading.value = false
    }
  }

  /**
   * 获取任务详情
   */
  const getTaskDetail = async (taskId: string) => {
    try {
      loading.value = true
      const response = await tasksApi.getTaskDetail(taskId)
      
      if (response.success) {
        currentTask.value = response.data
        return response.data
      } else {
        throw new Error(response.message || '获取任务详情失败')
      }
    } catch (error) {
      console.error('Get task detail failed:', error)
      ElMessage.error('获取任务详情失败')
      throw error
    } finally {
      loading.value = false
    }
  }

  /**
   * 更新任务信息
   */
  const updateTaskInfo = async (taskId: string, data: TaskUpdateData) => {
    try {
      loading.value = true
      const response = await tasksApi.updateTaskInfo(taskId, data)
      
      // 更新当前任务信息
      if (currentTask.value && currentTask.value.task_id === taskId) {
        currentTask.value = response
      }
      
      // 更新任务列表中的对应项
      const index = taskList.value.findIndex(task => task.task_id === taskId)
      if (index !== -1) {
        taskList.value[index] = response
      }
      
      ElMessage.success('任务信息更新成功')
      return response
    } catch (error) {
      console.error('Update task info failed:', error)
      ElMessage.error('更新任务信息失败')
      throw error
    } finally {
      loading.value = false
    }
  }

  /**
   * 手动生成回证
   */
  const generateReceipt = async (taskId: string) => {
    try {
      loading.value = true
      const response = await tasksApi.generateReceipt(taskId)
      
      if (response.success) {
        ElMessage.success('回证生成成功')
        // 刷新任务详情
        await getTaskDetail(taskId)
        return response.data
      } else {
        throw new Error(response.message || '生成回证失败')
      }
    } catch (error) {
      console.error('Generate receipt failed:', error)
      ElMessage.error('生成回证失败')
      throw error
    } finally {
      loading.value = false
    }
  }

  /**
   * 下载文件
   */
  const downloadFile = async (
    taskId: string, 
    fileType: 'document' | 'screenshot' | 'image',
    filename?: string
  ) => {
    try {
      loading.value = true
      const blob = await tasksApi.downloadFile(taskId, fileType)
      
      // 创建下载链接
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = filename || `${taskId}_${fileType}`
      link.click()
      window.URL.revokeObjectURL(url)
      
      ElMessage.success('下载成功')
    } catch (error) {
      console.error('Download file failed:', error)
      ElMessage.error('下载失败')
      throw error
    } finally {
      loading.value = false
    }
  }

  /**
   * 批量下载任务文件
   */
  const downloadTaskFiles = async (taskId: string) => {
    try {
      loading.value = true
      const blob = await tasksApi.downloadTaskFiles(taskId)
      
      // 创建下载链接
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `task_${taskId}_files.zip`
      link.click()
      window.URL.revokeObjectURL(url)
      
      ElMessage.success('打包下载成功')
    } catch (error) {
      console.error('Download task files failed:', error)
      ElMessage.error('打包下载失败')
      throw error
    } finally {
      loading.value = false
    }
  }

  /**
   * 删除任务
   */
  const deleteTask = async (taskId: string) => {
    try {
      loading.value = true
      await tasksApi.deleteTask(taskId)
      
      // 从列表中移除
      taskList.value = taskList.value.filter(task => task.task_id !== taskId)
      
      // 如果是当前任务，清空
      if (currentTask.value && currentTask.value.task_id === taskId) {
        currentTask.value = null
      }
      
      ElMessage.success('任务删除成功')
    } catch (error) {
      console.error('Delete task failed:', error)
      ElMessage.error('删除任务失败')
      throw error
    } finally {
      loading.value = false
    }
  }

  /**
   * 重试任务
   */
  const retryTask = async (taskId: string) => {
    try {
      loading.value = true
      const response = await tasksApi.retryTask(taskId)
      
      // 更新任务状态
      const index = taskList.value.findIndex(task => task.task_id === taskId)
      if (index !== -1) {
        taskList.value[index] = response
      }
      
      if (currentTask.value && currentTask.value.task_id === taskId) {
        currentTask.value = response
      }
      
      ElMessage.success('任务重试成功')
      return response
    } catch (error) {
      console.error('Retry task failed:', error)
      ElMessage.error('重试任务失败')
      throw error
    } finally {
      loading.value = false
    }
  }

  /**
   * 获取统计信息
   */
  const getStats = async () => {
    try {
      const response = await tasksApi.getTaskStats()
      stats.value = response
      return response
    } catch (error) {
      console.error('Get stats failed:', error)
      throw error
    }
  }

  /**
   * 获取最近活动
   */
  const getRecentActivities = async (limit: number = 10) => {
    try {
      const response = await tasksApi.getRecentActivities(limit)
      recentActivities.value = response
      return response
    } catch (error) {
      console.error('Get recent activities failed:', error)
      throw error
    }
  }

  /**
   * 设置筛选条件
   */
  const setFilters = (newFilters: Partial<TaskListParams>) => {
    filters.value = {
      ...filters.value,
      ...newFilters
    }
  }

  /**
   * 重置筛选条件
   */
  const resetFilters = () => {
    filters.value = {
      page: 1,
      size: 20,
      task_id: '',
      tracking_number: '',
      status: '',
      sort_by: 'created_desc'
    }
  }

  /**
   * 清空当前任务
   */
  const clearCurrentTask = () => {
    currentTask.value = null
  }

  /**
   * 根据状态筛选任务
   */
  const getTasksByStatus = (status: TaskStatus) => {
    return taskList.value.filter(task => task.status === status)
  }

  return {
    // 状态
    taskList,
    currentTask,
    loading,
    uploading,
    pagination,
    filters,
    stats,
    recentActivities,
    
    // Getters
    processingTasks,
    completedTasks,
    failedTasks,
    hasProcessingTasks,
    
    // Actions
    uploadImage,
    uploadImages,
    getTaskList,
    getTaskDetail,
    updateTaskInfo,
    generateReceipt,
    downloadFile,
    downloadTaskFiles,
    deleteTask,
    retryTask,
    getStats,
    getRecentActivities,
    setFilters,
    resetFilters,
    clearCurrentTask,
    getTasksByStatus
  }
})

export default useTasksStore