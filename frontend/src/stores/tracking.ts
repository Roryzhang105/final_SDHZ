import { defineStore } from 'pinia'
import { ref } from 'vue'
import { trackingApi } from '@/api'
import type { TrackingInfo } from '@/types'

export const useTrackingStore = defineStore('tracking', () => {
  // 状态
  const trackingInfo = ref<TrackingInfo | null>(null)
  const loading = ref(false)
  const updating = ref(false)
  const screenshotLoading = ref(false)

  // 获取物流信息
  const getTrackingInfo = async (trackingNumber: string) => {
    loading.value = true
    try {
      const response = await trackingApi.getInfo(trackingNumber)
      if (response.success && response.data) {
        trackingInfo.value = response.data
      }
      return response
    } catch (error) {
      console.error('Get tracking info error:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  // 更新物流信息
  const updateTrackingInfo = async (trackingNumber: string) => {
    updating.value = true
    try {
      const response = await trackingApi.updateInfo(trackingNumber)
      if (response.success && response.data) {
        trackingInfo.value = response.data
      }
      return response
    } catch (error) {
      console.error('Update tracking info error:', error)
      throw error
    } finally {
      updating.value = false
    }
  }

  // 生成物流截图
  const generateScreenshot = async (trackingNumber: string) => {
    screenshotLoading.value = true
    try {
      const response = await trackingApi.generateScreenshot(trackingNumber)
      return response
    } catch (error) {
      console.error('Generate screenshot error:', error)
      throw error
    } finally {
      screenshotLoading.value = false
    }
  }

  // 清除当前物流信息
  const clearTrackingInfo = () => {
    trackingInfo.value = null
  }

  return {
    // 状态
    trackingInfo,
    loading,
    updating,
    screenshotLoading,
    
    // 方法
    getTrackingInfo,
    updateTrackingInfo,
    generateScreenshot,
    clearTrackingInfo
  }
})