import request from '@/utils/request'
import type { 
  ApiResponse,
  TrackingInfo
} from '@/types'

export const trackingApi = {
  // 获取物流信息
  getInfo(trackingNumber: string): Promise<ApiResponse<TrackingInfo>> {
    return request.get(`/api/v1/tracking/${trackingNumber}`)
  },

  // 更新物流信息
  updateInfo(trackingNumber: string): Promise<ApiResponse<TrackingInfo>> {
    return request.post(`/api/v1/tracking/${trackingNumber}/update`)
  },

  // 生成物流截图
  generateScreenshot(trackingNumber: string): Promise<ApiResponse<{ screenshot_path: string, screenshot_filename: string }>> {
    return request.post(`/api/v1/tracking/${trackingNumber}/screenshot`)
  }
}