<template>
  <div class="tracking-view">
    <el-card class="search-card" shadow="hover">
      <template #header>
        <div class="card-header">
          <span>物流跟踪查询</span>
        </div>
      </template>
      
      <el-form :model="searchForm" :rules="searchRules" ref="searchFormRef" class="search-form">
        <el-row :gutter="20">
          <el-col :span="16">
            <el-form-item prop="trackingNumber">
              <el-input
                v-model="searchForm.trackingNumber"
                placeholder="请输入快递单号"
                size="large"
                clearable
                @keyup.enter="handleSearch"
              >
                <template #prepend>
                  <el-icon><Van /></el-icon>
                </template>
              </el-input>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item>
              <el-button
                type="primary"
                size="large"
                :loading="loading"
                @click="handleSearch"
                class="search-button"
              >
                <el-icon><Search /></el-icon>
                查询物流
              </el-button>
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
    </el-card>

    <!-- 物流信息展示 -->
    <el-card v-if="trackingInfo" class="result-card" shadow="hover">
      <template #header>
        <div class="result-header">
          <span>物流信息</span>
          <el-tag :type="getStatusType(trackingInfo.status)" size="large">
            {{ trackingInfo.status }}
          </el-tag>
        </div>
      </template>
      
      <div class="tracking-info">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="快递单号">
            {{ trackingInfo.tracking_number }}
          </el-descriptions-item>
          <el-descriptions-item label="快递公司">
            {{ trackingInfo.courier_company }}
          </el-descriptions-item>
          <el-descriptions-item label="寄件人">
            {{ trackingInfo.sender_name || '未知' }}
          </el-descriptions-item>
          <el-descriptions-item label="收件人">
            {{ trackingInfo.recipient_name || '未知' }}
          </el-descriptions-item>
          <el-descriptions-item label="收件地址" :span="2">
            {{ trackingInfo.recipient_address || '未知' }}
          </el-descriptions-item>
          <el-descriptions-item label="当前状态">
            <el-tag :type="getStatusType(trackingInfo.status)">
              {{ trackingInfo.status }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="最后更新">
            {{ formatDate(trackingInfo.last_update_time) }}
          </el-descriptions-item>
        </el-descriptions>
      </div>

      <!-- 物流轨迹时间线 -->
      <div class="timeline-section">
        <h4>物流轨迹</h4>
        <el-timeline>
          <el-timeline-item
            v-for="(trace, index) in trackingTraces"
            :key="index"
            :timestamp="formatDate(trace.time)"
            :type="getTraceType(trace, index)"
            :color="getTraceColor(trace, index)"
            :size="index === 0 ? 'large' : 'normal'"
          >
            <el-card class="trace-card">
              <div class="trace-content">
                <div class="trace-status">{{ trace.status }}</div>
                <div class="trace-desc">{{ trace.desc }}</div>
                <div v-if="trace.location" class="trace-location">
                  <el-icon><Location /></el-icon>
                  {{ trace.location }}
                </div>
              </div>
            </el-card>
          </el-timeline-item>
        </el-timeline>
      </div>

      <!-- 操作按钮 -->
      <div class="action-section">
        <el-button type="primary" :icon="Refresh" @click="handleRefresh">
          刷新物流信息
        </el-button>
        <el-button type="success" :icon="Document" @click="handleGenerateReceipt">
          生成送达回证
        </el-button>
      </div>
    </el-card>

    <!-- 空状态 -->
    <el-empty v-else-if="!loading && searched" description="未找到物流信息">
      <el-button type="primary" @click="handleReset">重新查询</el-button>
    </el-empty>

    <!-- 历史查询记录 -->
    <el-card v-if="searchHistory.length > 0" class="history-card" shadow="hover">
      <template #header>
        <div class="card-header">
          <span>最近查询</span>
          <el-button type="text" @click="clearHistory">
            <el-icon><Delete /></el-icon>
            清空记录
          </el-button>
        </div>
      </template>
      
      <div class="history-list">
        <el-tag
          v-for="(number, index) in searchHistory"
          :key="index"
          class="history-tag"
          closable
          @close="removeFromHistory(index)"
          @click="searchFromHistory(number)"
        >
          {{ number }}
        </el-tag>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import {
  Van,
  Search,
  Refresh,
  Document,
  Delete,
  Location
} from '@element-plus/icons-vue'
import { trackingApi } from '@/api/tracking'

const router = useRouter()

// 响应式数据
const loading = ref(false)
const searched = ref(false)
const trackingInfo = ref(null)
const searchHistory = ref<string[]>([])

// 搜索表单
const searchFormRef = ref<FormInstance>()
const searchForm = reactive({
  trackingNumber: ''
})

// 表单验证规则
const searchRules: FormRules = {
  trackingNumber: [
    { required: true, message: '请输入快递单号', trigger: 'blur' },
    { min: 8, message: '快递单号长度不能少于8位', trigger: 'blur' }
  ]
}

// 物流轨迹数据
const trackingTraces = computed(() => {
  if (!trackingInfo.value?.traces) return []
  
  try {
    const traces = typeof trackingInfo.value.traces === 'string' 
      ? JSON.parse(trackingInfo.value.traces) 
      : trackingInfo.value.traces
    
    return Array.isArray(traces) ? traces : []
  } catch (error) {
    console.error('解析物流轨迹失败:', error)
    return []
  }
})

// 获取状态类型
const getStatusType = (status: string) => {
  if (status?.includes('已签收') || status?.includes('已送达')) return 'success'
  if (status?.includes('运输中') || status?.includes('派送中')) return 'warning'
  if (status?.includes('异常') || status?.includes('失败')) return 'danger'
  return 'info'
}

// 获取轨迹类型
const getTraceType = (trace: any, index: number) => {
  if (index === 0) return 'primary'
  if (trace.status?.includes('签收') || trace.status?.includes('送达')) return 'success'
  if (trace.status?.includes('异常')) return 'danger'
  return 'info'
}

// 获取轨迹颜色
const getTraceColor = (trace: any, index: number) => {
  if (index === 0) return '#409eff'
  if (trace.status?.includes('签收') || trace.status?.includes('送达')) return '#67c23a'
  if (trace.status?.includes('异常')) return '#f56c6c'
  return '#909399'
}

// 格式化日期
const formatDate = (dateStr: string) => {
  if (!dateStr) return '未知'
  try {
    const date = new Date(dateStr)
    return date.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    })
  } catch (error) {
    return dateStr
  }
}

// 处理搜索
const handleSearch = async () => {
  if (!searchFormRef.value) return
  
  try {
    await searchFormRef.value.validate()
    
    loading.value = true
    searched.value = true
    
    const response = await trackingApi.query(searchForm.trackingNumber)
    trackingInfo.value = response.data
    
    // 添加到搜索历史
    addToHistory(searchForm.trackingNumber)
    
    ElMessage.success('查询成功')
  } catch (error) {
    console.error('查询失败:', error)
    if (error?.response?.status === 404) {
      ElMessage.warning('未找到该快递单号的物流信息')
      trackingInfo.value = null
    } else {
      ElMessage.error('查询失败，请稍后重试')
    }
  } finally {
    loading.value = false
  }
}

// 处理刷新
const handleRefresh = async () => {
  if (!trackingInfo.value?.tracking_number) return
  
  loading.value = true
  try {
    const response = await trackingApi.query(trackingInfo.value.tracking_number)
    trackingInfo.value = response.data
    ElMessage.success('刷新成功')
  } catch (error) {
    console.error('刷新失败:', error)
    ElMessage.error('刷新失败')
  } finally {
    loading.value = false
  }
}

// 处理生成送达回证
const handleGenerateReceipt = () => {
  if (!trackingInfo.value?.tracking_number) return
  
  router.push({
    path: '/delivery/generate',
    query: {
      trackingNumber: trackingInfo.value.tracking_number
    }
  })
}

// 处理重置
const handleReset = () => {
  searchForm.trackingNumber = ''
  trackingInfo.value = null
  searched.value = false
  searchFormRef.value?.clearValidate()
}

// 添加到搜索历史
const addToHistory = (trackingNumber: string) => {
  const history = [...searchHistory.value]
  const index = history.indexOf(trackingNumber)
  
  if (index > -1) {
    history.splice(index, 1)
  }
  
  history.unshift(trackingNumber)
  
  // 只保留最近10条记录
  if (history.length > 10) {
    history.pop()
  }
  
  searchHistory.value = history
  localStorage.setItem('trackingSearchHistory', JSON.stringify(history))
}

// 从历史记录搜索
const searchFromHistory = (trackingNumber: string) => {
  searchForm.trackingNumber = trackingNumber
  handleSearch()
}

// 从历史记录中移除
const removeFromHistory = (index: number) => {
  searchHistory.value.splice(index, 1)
  localStorage.setItem('trackingSearchHistory', JSON.stringify(searchHistory.value))
}

// 清空历史记录
const clearHistory = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要清空所有搜索记录吗？',
      '确认清空',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    searchHistory.value = []
    localStorage.removeItem('trackingSearchHistory')
    ElMessage.success('已清空搜索记录')
  } catch (error) {
    // 用户取消
  }
}

// 加载搜索历史
const loadSearchHistory = () => {
  try {
    const history = localStorage.getItem('trackingSearchHistory')
    if (history) {
      searchHistory.value = JSON.parse(history)
    }
  } catch (error) {
    console.error('加载搜索历史失败:', error)
  }
}

// 组件挂载时加载历史记录
onMounted(() => {
  loadSearchHistory()
})
</script>

<style scoped>
.tracking-view {
  padding: 0;
}

.search-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.search-form {
  margin: 0;
}

.search-button {
  width: 100%;
}

.result-card {
  margin-bottom: 20px;
}

.tracking-info {
  margin-bottom: 30px;
}

.timeline-section {
  margin: 30px 0;
}

.timeline-section h4 {
  margin-bottom: 20px;
  color: #333;
  font-size: 16px;
  font-weight: 600;
}

.trace-card {
  margin-bottom: 0;
  box-shadow: none;
  border: 1px solid #e4e7ed;
}

.trace-content {
  padding: 5px 0;
}

.trace-status {
  font-weight: 600;
  color: #333;
  margin-bottom: 5px;
}

.trace-desc {
  color: #666;
  font-size: 14px;
  margin-bottom: 5px;
}

.trace-location {
  color: #909399;
  font-size: 12px;
  display: flex;
  align-items: center;
  gap: 4px;
}

.action-section {
  text-align: center;
  padding-top: 20px;
  border-top: 1px solid #e4e7ed;
}

.action-section .el-button {
  margin: 0 10px;
}

.history-card {
  margin-top: 20px;
}

.history-list {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.history-tag {
  cursor: pointer;
  transition: all 0.3s;
}

.history-tag:hover {
  background-color: #409eff;
  color: white;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .search-form .el-col {
    margin-bottom: 15px;
  }
  
  .result-header {
    flex-direction: column;
    gap: 10px;
    align-items: flex-start;
  }
  
  .action-section .el-button {
    margin: 5px;
    width: calc(50% - 10px);
  }
  
  .timeline-section {
    margin: 20px 0;
  }
}
</style>