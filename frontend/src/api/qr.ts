import request from '@/utils/request'
import type { 
  ApiResponse,
  QRCodeGenerateRequest,
  QRCodeGenerateResponse,
  QRCodeRecognizeResponse
} from '@/types'

export const qrApi = {
  // 生成二维码
  generate(data: any): Promise<ApiResponse<any>> {
    return request.post('/api/v1/qr-generation/generate', data)
  },

  // 生成完整标签
  generateLabel(data: { tracking_number: string }): Promise<ApiResponse<any>> {
    return request.post('/api/v1/qr-generation/label', data)
  },

  // 识别二维码（支持FormData）
  recognize(data: FormData): Promise<ApiResponse<QRCodeRecognizeResponse>> {
    return request.post('/api/v1/qr-recognition/recognize', data, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },

  // 识别二维码（支持File）
  recognizeFile(file: File): Promise<ApiResponse<QRCodeRecognizeResponse>> {
    const formData = new FormData()
    formData.append('file', file)
    
    return request.post('/api/v1/qr-recognition/recognize', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },

  // 批量识别二维码
  batchRecognize(files: File[]): Promise<ApiResponse<QRCodeRecognizeResponse[]>> {
    const formData = new FormData()
    files.forEach(file => {
      formData.append('files', file)
    })
    
    return request.post('/api/v1/qr-recognition/batch-recognize', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  }
}