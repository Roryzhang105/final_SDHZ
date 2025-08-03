<template>
  <div class="page-content dashboard">
    <el-row :gutter="20">
      <!-- 统计卡片 -->
      <el-col :xs="24" :sm="12" :md="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon">
              <el-icon size="40" color="#409EFF">
                <Document />
              </el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-number">{{ totalReceipts }}</div>
              <div class="stat-label">总回证数</div>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :xs="24" :sm="12" :md="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon">
              <el-icon size="40" color="#67C23A">
                <Check />
              </el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-number">{{ completedReceipts }}</div>
              <div class="stat-label">已完成</div>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :xs="24" :sm="12" :md="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon">
              <el-icon size="40" color="#E6A23C">
                <Clock />
              </el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-number">{{ pendingReceipts }}</div>
              <div class="stat-label">处理中</div>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :xs="24" :sm="12" :md="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon">
              <el-icon size="40" color="#F56C6C">
                <Warning />
              </el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-number">{{ failedReceipts }}</div>
              <div class="stat-label">失败</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
    
    <el-row :gutter="20" style="margin-top: 20px;">
      <!-- 上传图片 -->
      <el-col :xs="24" :md="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>快速上传</span>
            </div>
          </template>
          
          <div class="upload-section">
            <el-button
              type="primary"
              size="large"
              class="upload-button"
              @click="$router.push('/app/delivery/generate')"
            >
              <el-icon><Camera /></el-icon>
              上传带二维码的图片
            </el-button>
            
            <p class="upload-description">
              请上传包含二维码的图片，系统将自动识别并创建任务
            </p>
          </div>
        </el-card>
      </el-col>
      
      <!-- 最近活动 -->
      <el-col :xs="24" :md="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>最近活动</span>
              <el-button text @click="refreshData">
                <el-icon><Refresh /></el-icon>
                刷新
              </el-button>
            </div>
          </template>
          
          <el-timeline>
            <el-timeline-item
              v-for="activity in recentActivities"
              :key="activity.id"
              :timestamp="activity.time"
              :type="activity.type"
            >
              {{ activity.description }}
            </el-timeline-item>
          </el-timeline>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { 
  Document, 
  Check, 
  Clock, 
  Warning, 
  Camera,
  Refresh
} from '@element-plus/icons-vue'
import { useDeliveryStore } from '@/stores/delivery'
import { dashboardApi } from '@/api'
import { ElMessage } from 'element-plus'

const deliveryStore = useDeliveryStore()

// 统计数据
const totalReceipts = ref(0)
const completedReceipts = ref(0)
const pendingReceipts = ref(0)
const failedReceipts = ref(0)
const loading = ref(false)

// 最近活动数据
const recentActivities = ref<any[]>([])

// 自动刷新定时器
let refreshTimer: NodeJS.Timeout | null = null

// 加载数据
const loadData = async () => {
  if (loading.value) return
  
  loading.value = true
  try {
    const response = await dashboardApi.getStats()
    
    if (response.success && response.data) {
      const { statistics, recent_activities } = response.data
      
      // 更新统计数据
      totalReceipts.value = statistics.total_receipts
      completedReceipts.value = statistics.completed_receipts
      pendingReceipts.value = statistics.pending_receipts
      failedReceipts.value = statistics.failed_receipts
      
      // 更新最近活动
      recentActivities.value = recent_activities || []
    } else {
      throw new Error(response.message || '获取数据失败')
    }
  } catch (error) {
    console.error('Failed to load dashboard data:', error)
    ElMessage.error('加载仪表盘数据失败')
    
    // 如果API失败，尝试使用旧的方法作为备用
    try {
      await deliveryStore.getReceiptList()
      const receipts = deliveryStore.receipts
      totalReceipts.value = receipts.length
      completedReceipts.value = receipts.filter(r => r.status === 'completed').length
      pendingReceipts.value = receipts.filter(r => r.status === 'pending').length
      failedReceipts.value = receipts.filter(r => r.status === 'failed').length
    } catch (fallbackError) {
      console.error('Fallback data loading also failed:', fallbackError)
    }
  } finally {
    loading.value = false
  }
}

// 刷新数据
const refreshData = () => {
  loadData()
}

// 启动自动刷新
const startAutoRefresh = () => {
  // 清理之前的定时器
  if (refreshTimer) {
    clearInterval(refreshTimer)
  }
  
  // 每30秒刷新一次
  refreshTimer = setInterval(() => {
    loadData()
  }, 30000)
}

// 停止自动刷新
const stopAutoRefresh = () => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
    refreshTimer = null
  }
}

onMounted(() => {
  loadData()
  startAutoRefresh()
})

onUnmounted(() => {
  stopAutoRefresh()
})
</script>

<style scoped>
.dashboard {
  /* padding已通过page-content类提供 */
}

.stat-card {
  height: 120px;
}

.stat-content {
  display: flex;
  align-items: center;
  height: 100%;
}

.stat-icon {
  margin-right: 15px;
}

.stat-info {
  flex: 1;
}

.stat-number {
  font-size: 32px;
  font-weight: bold;
  color: #333;
  line-height: 1;
}

.stat-label {
  font-size: 14px;
  color: #666;
  margin-top: 5px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.upload-section {
  text-align: center;
  padding: 20px 0;
}

.upload-button {
  height: 80px;
  font-size: 18px;
  padding: 0 40px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  width: 100%;
  max-width: 300px;
  margin: 0 auto;
}

.upload-description {
  color: #666;
  font-size: 14px;
  margin-top: 15px;
  line-height: 1.6;
}

@media (max-width: 768px) {
  .upload-button {
    font-size: 16px;
    height: 70px;
    max-width: 100%;
  }
}
</style>