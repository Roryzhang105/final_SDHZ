<template>
  <div class="dashboard">
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
              @click="$router.push('/delivery/generate')"
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
import { ref, computed, onMounted } from 'vue'
import { 
  Document, 
  Check, 
  Clock, 
  Warning, 
  Camera,
  Refresh
} from '@element-plus/icons-vue'
import { useDeliveryStore } from '@/stores/delivery'

const deliveryStore = useDeliveryStore()

// 模拟统计数据
const totalReceipts = ref(0)
const completedReceipts = ref(0)
const pendingReceipts = ref(0)
const failedReceipts = ref(0)

// 模拟最近活动数据
const recentActivities = ref([
  {
    id: 1,
    description: '任务 #1151242358360 处理完成，送达回证已生成',
    time: '2024-01-30 14:30:00',
    type: 'success'
  },
  {
    id: 2,
    description: '任务 #1151240728560 开始处理，正在识别二维码',
    time: '2024-01-30 13:45:00',
    type: 'primary'
  },
  {
    id: 3,
    description: '新任务 #1151238971060 已创建，等待处理',
    time: '2024-01-30 12:20:00',
    type: 'info'
  },
  {
    id: 4,
    description: '任务 #1151235647120 处理失败，二维码识别异常',
    time: '2024-01-30 11:15:00',
    type: 'warning'
  }
])

// 加载数据
const loadData = async () => {
  try {
    await deliveryStore.getReceiptList()
    
    // 计算统计数据
    const receipts = deliveryStore.receipts
    totalReceipts.value = receipts.length
    
    // 根据实际状态统计
    completedReceipts.value = receipts.filter(r => r.status === 'completed').length
    pendingReceipts.value = receipts.filter(r => r.status === 'pending').length
    failedReceipts.value = receipts.filter(r => r.status === 'failed').length
  } catch (error) {
    console.error('Failed to load dashboard data:', error)
  }
}

// 刷新数据
const refreshData = () => {
  loadData()
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.dashboard {
  padding: 20px;
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
}

.upload-description {
  color: #666;
  font-size: 14px;
  margin-top: 15px;
  line-height: 1.6;
}

@media (max-width: 768px) {
  .dashboard {
    padding: 10px;
  }
  
  .upload-button {
    font-size: 16px;
    height: 70px;
    max-width: 100%;
  }
}
</style>