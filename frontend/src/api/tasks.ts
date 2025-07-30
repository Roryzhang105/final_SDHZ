import request from '@/utils/request'
import type { 
  Task, 
  TaskListParams, 
  TaskListResponse, 
  TaskDetailResponse,
  TaskUpdateData,
  GenerateReceiptResponse,
  UploadImageResponse
} from '@/types'

/**
 * 任务相关API
 */
export const tasksApi = {
  /**
   * 上传图片
   * @param file 图片文件
   * @returns 上传结果
   */
  uploadImage(file: File): Promise<UploadImageResponse> {
    const formData = new FormData()
    formData.append('image', file)
    
    return request({
      url: '/api/v1/tasks/upload',
      method: 'POST',
      data: formData,
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },

  /**
   * 批量上传图片
   * @param files 图片文件数组
   * @returns 上传结果
   */
  uploadImages(files: File[]): Promise<UploadImageResponse[]> {
    const formData = new FormData()
    files.forEach((file, index) => {
      formData.append(`images[${index}]`, file)
    })
    
    return request({
      url: '/api/v1/tasks/upload/batch',
      method: 'POST',
      data: formData,
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },

  /**
   * 获取任务列表
   * @param params 查询参数
   * @returns 任务列表
   */
  getTaskList(params: TaskListParams): Promise<TaskListResponse> {
    return request({
      url: '/api/v1/tasks',
      method: 'GET',
      params
    })
  },

  /**
   * 获取任务详情
   * @param taskId 任务ID
   * @returns 任务详情
   */
  getTaskDetail(taskId: string): Promise<TaskDetailResponse> {
    return request({
      url: `/api/v1/tasks/${taskId}`,
      method: 'GET'
    })
  },

  /**
   * 更新任务信息
   * @param taskId 任务ID
   * @param data 更新数据
   * @returns 更新结果
   */
  updateTaskInfo(taskId: string, data: TaskUpdateData): Promise<Task> {
    return request({
      url: `/api/v1/tasks/${taskId}`,
      method: 'PUT',
      data
    })
  },

  /**
   * 手动生成回证
   * @param taskId 任务ID
   * @returns 生成结果
   */
  generateReceipt(taskId: string): Promise<GenerateReceiptResponse> {
    return request({
      url: `/api/v1/tasks/${taskId}/generate`,
      method: 'POST'
    })
  },

  /**
   * 下载文件
   * @param taskId 任务ID
   * @param fileType 文件类型 (document|screenshot|image)
   * @returns 文件流
   */
  downloadFile(taskId: string, fileType: 'document' | 'screenshot' | 'image'): Promise<Blob> {
    return request({
      url: `/api/v1/tasks/${taskId}/download/${fileType}`,
      method: 'GET',
      responseType: 'blob'
    })
  },

  /**
   * 批量下载任务文件
   * @param taskId 任务ID
   * @returns 压缩包文件流
   */
  downloadTaskFiles(taskId: string): Promise<Blob> {
    return request({
      url: `/api/v1/tasks/${taskId}/download/all`,
      method: 'GET',
      responseType: 'blob'
    })
  },

  /**
   * 删除任务
   * @param taskId 任务ID
   * @returns 删除结果
   */
  deleteTask(taskId: string): Promise<void> {
    return request({
      url: `/api/v1/tasks/${taskId}`,
      method: 'DELETE'
    })
  },

  /**
   * 重试任务
   * @param taskId 任务ID
   * @returns 重试结果
   */
  retryTask(taskId: string): Promise<Task> {
    return request({
      url: `/api/v1/tasks/${taskId}/retry`,
      method: 'POST'
    })
  },

  /**
   * 获取任务统计信息
   * @returns 统计数据
   */
  getTaskStats(): Promise<{
    total: number
    completed: number
    pending: number
    failed: number
  }> {
    return request({
      url: '/api/v1/tasks/stats',
      method: 'GET'
    })
  },

  /**
   * 获取最近活动
   * @param limit 限制数量
   * @returns 活动列表
   */
  getRecentActivities(limit: number = 10): Promise<{
    id: string
    taskId: string
    description: string
    time: string
    type: 'success' | 'info' | 'warning' | 'error'
  }[]> {
    return request({
      url: '/api/v1/tasks/activities',
      method: 'GET',
      params: { limit }
    })
  }
}

export default tasksApi