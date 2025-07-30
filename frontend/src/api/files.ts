import request from '@/utils/request'
import type { 
  ApiResponse,
  FileUploadResponse
} from '@/types'

export const filesApi = {
  // 上传单个文件
  uploadFile(file: File): Promise<ApiResponse<FileUploadResponse>> {
    const formData = new FormData()
    formData.append('file', file)
    
    return request.post('/api/v1/upload/file', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },

  // 批量上传文件
  uploadFiles(files: File[]): Promise<ApiResponse<FileUploadResponse[]>> {
    const formData = new FormData()
    files.forEach(file => {
      formData.append('files', file)
    })
    
    return request.post('/api/v1/upload/files', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },

  // 获取文件列表
  getList(params?: any): Promise<ApiResponse<{ items: any[], total: number }>> {
    return request.get('/api/v1/files/', { params })
  },

  // 获取文件内容
  getContent(id: string | number): Promise<ApiResponse<string>> {
    return request.get(`/api/v1/files/${id}/content`)
  },

  // 下载文件
  download(id: string | number): Promise<any> {
    return request.get(`/api/v1/files/${id}/download`, {
      responseType: 'blob'
    })
  },

  // 重命名文件
  rename(id: string | number, data: { new_name: string }): Promise<ApiResponse> {
    return request.put(`/api/v1/files/${id}/rename`, data)
  },

  // 删除文件
  delete(id: string | number): Promise<ApiResponse> {
    return request.delete(`/api/v1/files/${id}`)
  },

  // 批量删除文件
  batchDelete(data: { ids: (string | number)[] }): Promise<ApiResponse> {
    return request.post('/api/v1/files/batch/delete', data)
  }
}