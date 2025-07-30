import request from '@/utils/request'
import type { 
  ApiResponse,
  DeliveryReceipt,
  DeliveryReceiptGenerateRequest,
  DeliveryReceiptGenerateResponse,
  PaginatedResponse
} from '@/types'

export const deliveryApi = {
  // 生成送达回证
  generate(data: DeliveryReceiptGenerateRequest): Promise<ApiResponse<DeliveryReceiptGenerateResponse>> {
    return request.post('/api/v1/delivery-receipts/generate', data)
  },

  // 获取送达回证列表
  getList(params?: any): Promise<ApiResponse<{ items: DeliveryReceipt[], total: number }>> {
    return request.get('/api/v1/delivery-receipts/', { params })
  },

  // 根据快递单号获取送达回证
  getByTrackingNumber(trackingNumber: string): Promise<ApiResponse<any>> {
    return request.get(`/api/v1/delivery-receipts/tracking/${trackingNumber}`)
  },

  // 获取送达回证详情
  getById(id: number): Promise<ApiResponse<DeliveryReceipt>> {
    return request.get(`/api/v1/delivery-receipts/${id}`)
  },

  // 下载送达回证文档（通过ID）
  download(id: string | number): Promise<any> {
    return request.get(`/api/v1/delivery-receipts/${id}/download`, {
      responseType: 'blob'
    })
  },

  // 下载送达回证文档（通过快递单号）
  downloadByTrackingNumber(trackingNumber: string): Promise<Blob> {
    return request.get(`/api/v1/delivery-receipts/${trackingNumber}/download`, {
      responseType: 'blob'
    })
  },

  // 删除送达回证
  delete(id: string | number): Promise<ApiResponse> {
    return request.delete(`/api/v1/delivery-receipts/${id}`)
  },

  // 批量删除送达回证
  batchDelete(data: { ids: (string | number)[] }): Promise<ApiResponse> {
    return request.post('/api/v1/delivery-receipts/batch/delete', data)
  },

  // 更新送达回证状态
  updateStatus(id: number, status: string): Promise<ApiResponse> {
    return request.put(`/api/v1/delivery-receipts/${id}/status`, { status })
  },

  // 创建送达回证（兼容旧版API）
  create(data: FormData): Promise<ApiResponse<{ message: string, receipt_id: number }>> {
    return request.post('/api/v1/delivery-receipts/', data, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  }
}