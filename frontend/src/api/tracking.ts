import request from '@/utils/request'
import type { TrackingInfo, ApiResponse } from '@/types'

/**
 * 物流跟踪相关API
 */
export const trackingApi = {
  /**
   * 获取物流信息
   * @param trackingNumber 物流单号
   * @returns 物流信息
   */
  getInfo(trackingNumber: string): Promise<ApiResponse<TrackingInfo>> {
    return request({
      url: `/api/v1/tracking/${trackingNumber}`,
      method: 'GET'
    })
  },

  /**
   * 更新物流信息
   * @param trackingNumber 物流单号
   * @returns 更新后的物流信息
   */
  updateInfo(trackingNumber: string): Promise<ApiResponse<TrackingInfo>> {
    return request({
      url: `/api/v1/tracking/${trackingNumber}/update`,
      method: 'POST'
    })
  },

  /**
   * 生成物流截图
   * @param trackingNumber 物流单号
   * @returns 截图URL
   */
  generateScreenshot(trackingNumber: string): Promise<ApiResponse<{ screenshot_url: string }>> {
    return request({
      url: `/api/v1/tracking/${trackingNumber}/screenshot`,
      method: 'POST'
    })
  },

  /**
   * 批量查询物流信息
   * @param trackingNumbers 物流单号数组
   * @returns 物流信息列表
   */
  batchGetInfo(trackingNumbers: string[]): Promise<ApiResponse<TrackingInfo[]>> {
    return request({
      url: '/api/v1/tracking/batch',
      method: 'POST',
      data: { tracking_numbers: trackingNumbers }
    })
  }
}

export default trackingApi