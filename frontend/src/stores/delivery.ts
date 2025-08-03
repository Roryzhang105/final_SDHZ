import { defineStore } from 'pinia'
import { ref } from 'vue'
import { deliveryApi } from '@/api'
import type { DeliveryReceipt, DeliveryReceiptGenerateRequest } from '@/types'

export const useDeliveryStore = defineStore('delivery', () => {
  // 状态
  const receipts = ref<DeliveryReceipt[]>([])
  const currentReceipt = ref<DeliveryReceipt | null>(null)
  const loading = ref(false)
  const generating = ref(false)

  // 获取送达回证列表
  const getReceiptList = async (limit = 50) => {
    loading.value = true
    try {
      const response = await deliveryApi.getList({ limit })
      if (response.success && response.data) {
        // 处理后端实际返回的数据结构
        receipts.value = response.data.receipts || response.data.items || []
      }
      return response
    } catch (error) {
      console.error('Get receipt list error:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  // 生成送达回证
  const generateReceipt = async (data: DeliveryReceiptGenerateRequest) => {
    generating.value = true
    try {
      const response = await deliveryApi.generate(data)
      if (response.success) {
        // 重新获取列表以包含新生成的回证
        await getReceiptList()
      }
      return response
    } catch (error) {
      console.error('Generate receipt error:', error)
      throw error
    } finally {
      generating.value = false
    }
  }

  // 根据快递单号获取送达回证
  const getReceiptByTrackingNumber = async (trackingNumber: string) => {
    loading.value = true
    try {
      const response = await deliveryApi.getByTrackingNumber(trackingNumber)
      if (response.success && response.data) {
        currentReceipt.value = response.data.receipt_info
      }
      return response
    } catch (error) {
      console.error('Get receipt by tracking number error:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  // 下载送达回证文档
  const downloadReceipt = async (trackingNumber: string) => {
    try {
      const result = await deliveryApi.downloadByTrackingNumber(trackingNumber)
      
      // 创建下载链接
      const url = window.URL.createObjectURL(result.blob)
      const link = document.createElement('a')
      link.href = url
      link.download = result.filename
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)
      
      return true
    } catch (error) {
      console.error('Download receipt error:', error)
      throw error
    }
  }

  // 更新送达回证状态
  const updateReceiptStatus = async (id: number, status: string) => {
    try {
      const response = await deliveryApi.updateStatus(id, status)
      if (response.success) {
        // 更新本地状态
        const index = receipts.value.findIndex(receipt => receipt.id === id)
        if (index !== -1) {
          receipts.value[index].status = status
        }
        if (currentReceipt.value?.id === id) {
          currentReceipt.value.status = status
        }
      }
      return response
    } catch (error) {
      console.error('Update receipt status error:', error)
      throw error
    }
  }

  // 清除当前回证
  const clearCurrentReceipt = () => {
    currentReceipt.value = null
  }

  return {
    // 状态
    receipts,
    currentReceipt,
    loading,
    generating,
    
    // 方法
    getReceiptList,
    generateReceipt,
    getReceiptByTrackingNumber,
    downloadReceipt,
    updateReceiptStatus,
    clearCurrentReceipt
  }
})