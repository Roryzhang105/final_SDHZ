import request from '@/utils/request'
import type { 
  ApiResponse,
  FileUploadResponse
} from '@/types'

export const fileApi = {
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
  getFileList(params?: any): Promise<ApiResponse<any[]>> {
    return request.get('/api/v1/files/', { params })
  },

  // 删除文件
  deleteFile(fileId: string): Promise<ApiResponse> {
    return request.delete(`/api/v1/files/${fileId}`)
  }
}