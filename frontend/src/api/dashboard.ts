import request from '@/utils/request'
import type { ApiResponse } from '@/types'

export interface DashboardStats {
  total_receipts: number
  completed_receipts: number
  pending_receipts: number
  failed_receipts: number
}

export interface RecentActivity {
  id: number
  description: string
  time: string
  type: 'success' | 'info' | 'warning' | 'primary' | 'danger'
}

export interface DashboardData {
  statistics: DashboardStats
  recent_activities: RecentActivity[]
}

export const dashboardApi = {
  // 获取仪表盘统计数据
  getStats(): Promise<ApiResponse<DashboardData>> {
    return request.get('/api/v1/dashboard/stats')
  },

  // 获取最近活动
  getRecentActivities(limit = 20): Promise<ApiResponse<{ activities: RecentActivity[], count: number }>> {
    return request.get('/api/v1/dashboard/activities', { params: { limit } })
  },

  // 记录活动日志
  logActivity(data: {
    action_type: string
    description: string
    entity_type?: string
    entity_id?: string
    status?: string
  }): Promise<ApiResponse<any>> {
    return request.post('/api/v1/dashboard/activities/log', data)
  }
}