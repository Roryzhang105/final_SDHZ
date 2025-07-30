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
      <!-- 快速操作 -->
      <el-col :xs="24" :md="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>快速操作</span>
            </div>
          </template>
          
          <div class="quick-actions">
            <el-button
              type="primary"
              size="large"
              @click="$router.push('/delivery/generate')"
            >
              <el-icon><Plus /></el-icon>
              生成送达回证
            </el-button>
            
            <el-button
              size="large"
              @click="$router.push('/tracking')"
            >
              <el-icon><Search /></el-icon>
              查询物流信息
            </el-button>
            
            <el-button
              size="large"
              @click="$router.push('/qr/generate')"
            >
              <el-icon><Grid /></el-icon>
              生成二维码
            </el-button>
            
            <el-button
              size="large"
              @click="$router.push('/qr/recognize')"
            >
              <el-icon><Camera /></el-icon>
              识别二维码
            </el-button>
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
  Plus, 
  Search, 
  Grid, 
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
    description: '生成送达回证 #1151242358360',
    time: '2024-01-30 14:30:00',
    type: 'success'
  },
  {
    id: 2,
    description: '更新物流信息 #1151240728560',
    time: '2024-01-30 13:45:00',
    type: 'primary'
  },
  {
    id: 3,
    description: '生成二维码标签',
    time: '2024-01-30 12:20:00',
    type: 'info'
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

.quick-actions {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 15px;
}

.quick-actions .el-button {
  height: 60px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 5px;
}

@media (max-width: 768px) {
  .dashboard {
    padding: 10px;
  }
  
  .quick-actions {
    grid-template-columns: 1fr;
  }
}
</style>