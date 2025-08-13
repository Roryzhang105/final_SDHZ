<template>
  <div class="celery-monitor">
    <!-- 页面标题 -->
    <div class="page-header">
      <div class="header-content">
        <h1 class="page-title">Celery监控</h1>
        <div class="page-description">
          监控Celery任务执行状态、Worker性能和Beat健康状态
        </div>
      </div>
      <div class="header-actions">
        <el-button @click="refreshData" :loading="loading">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </div>
    </div>

    <!-- 系统状态卡片 -->
    <div class="status-cards">
      <!-- Beat健康状态 -->
      <div class="status-card beat-health" :class="{ 'healthy': beatHealth?.is_healthy, 'unhealthy': !beatHealth?.is_healthy }">
        <div class="card-header">
          <span class="card-title">Beat状态</span>
          <el-tag :type="beatHealth?.is_healthy ? 'success' : 'danger'" size="small">
            {{ beatHealth?.is_healthy ? '健康' : '异常' }}
          </el-tag>
        </div>
        <div class="card-content">
          <div class="stat-item">
            <span class="stat-label">CPU使用率:</span>
            <span class="stat-value">{{ beatHealth?.cpu_percent?.toFixed(1) || 0 }}%</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">内存使用:</span>
            <span class="stat-value">{{ beatHealth?.memory_mb?.toFixed(0) || 0 }}MB</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">最后心跳:</span>
            <span class="stat-value">{{ formatRelativeTime(beatHealth?.last_heartbeat) }}</span>
          </div>
        </div>
      </div>

      <!-- 今日任务统计 -->
      <div class="status-card">
        <div class="card-header">
          <span class="card-title">今日任务</span>
          <el-icon><DataBoard /></el-icon>
        </div>
        <div class="card-content">
          <div class="big-number">{{ dashboardStats?.today_tasks || 0 }}</div>
          <div class="success-rate">
            成功率: {{ dashboardStats?.success_rate?.toFixed(1) || 0 }}%
          </div>
          <div class="stat-row">
            <span class="success">成功: {{ dashboardStats?.success_today || 0 }}</span>
            <span class="failed">失败: {{ dashboardStats?.failed_today || 0 }}</span>
          </div>
        </div>
      </div>

      <!-- Worker统计 -->
      <div class="status-card">
        <div class="card-header">
          <span class="card-title">Worker状态</span>
          <el-icon><Monitor /></el-icon>
        </div>
        <div class="card-content">
          <div class="big-number">{{ systemStatus?.total_workers || 0 }}</div>
          <div class="stat-label">活跃Worker数量</div>
          <div class="stat-row">
            <span>活动任务: {{ systemStatus?.total_active_tasks || 0 }}</span>
            <span>等待任务: {{ systemStatus?.total_reserved_tasks || 0 }}</span>
          </div>
        </div>
      </div>

      <!-- 总任务数 -->
      <div class="status-card">
        <div class="card-header">
          <span class="card-title">总任务数</span>
          <el-icon><Document /></el-icon>
        </div>
        <div class="card-content">
          <div class="big-number">{{ dashboardStats?.total_tasks || 0 }}</div>
          <div class="stat-label">历史总计</div>
        </div>
      </div>
    </div>

    <!-- 主要内容区域 -->
    <div class="main-content">
      <!-- Tab 切换 -->
      <el-tabs v-model="activeTab" @tab-click="handleTabClick">
        <!-- 任务监控 -->
        <el-tab-pane label="任务监控" name="tasks">
          <div class="tasks-panel">
            <!-- 筛选条件 -->
            <div class="filter-bar">
              <el-select v-model="taskFilters.hours" @change="loadTaskHistory" style="width: 150px">
                <el-option label="最近1小时" :value="1" />
                <el-option label="最近6小时" :value="6" />
                <el-option label="最近24小时" :value="24" />
                <el-option label="最近3天" :value="72" />
              </el-select>
              
              <el-input 
                v-model="taskFilters.taskName" 
                placeholder="任务名称筛选" 
                clearable
                @change="loadTaskHistory"
                style="width: 200px; margin-left: 10px"
              >
                <template #prefix>
                  <el-icon><Search /></el-icon>
                </template>
              </el-input>
            </div>

            <!-- 任务列表 -->
            <el-table 
              :data="taskHistory" 
              v-loading="tasksLoading"
              stripe
              style="width: 100%"
              :default-sort="{ prop: 'created_at', order: 'descending' }"
            >
              <el-table-column prop="task_name" label="任务名称" width="200" show-overflow-tooltip />
              
              <el-table-column prop="status" label="状态" width="100">
                <template #default="{ row }">
                  <el-tag :type="getStatusType(row.status)" size="small">
                    {{ getStatusText(row.status) }}
                  </el-tag>
                </template>
              </el-table-column>
              
              <el-table-column prop="queue_name" label="队列" width="100" />
              
              <el-table-column prop="worker_name" label="Worker" width="150" show-overflow-tooltip />
              
              <el-table-column prop="runtime_seconds" label="执行时长" width="100">
                <template #default="{ row }">
                  {{ row.runtime_seconds ? `${row.runtime_seconds.toFixed(2)}s` : '-' }}
                </template>
              </el-table-column>
              
              <el-table-column prop="retries" label="重试次数" width="80" />
              
              <el-table-column prop="created_at" label="创建时间" width="150">
                <template #default="{ row }">
                  {{ formatDateTime(row.created_at) }}
                </template>
              </el-table-column>
              
              <el-table-column label="操作" width="200">
                <template #default="{ row }">
                  <el-button 
                    v-if="row.status === 'FAILURE'" 
                    type="primary" 
                    size="small" 
                    @click="retryTask(row.task_id)"
                  >
                    重试
                  </el-button>
                  
                  <el-button 
                    v-if="['PENDING', 'STARTED'].includes(row.status)" 
                    type="warning" 
                    size="small" 
                    @click="revokeTask(row.task_id)"
                  >
                    撤销
                  </el-button>
                  
                  <el-button 
                    size="small" 
                    @click="viewTaskDetail(row)"
                  >
                    详情
                  </el-button>
                </template>
              </el-table-column>
            </el-table>

            <!-- 分页 -->
            <div class="pagination-container">
              <el-pagination
                v-model:current-page="taskPagination.page"
                v-model:page-size="taskPagination.size"
                :total="taskPagination.total"
                :page-sizes="[20, 50, 100]"
                layout="total, sizes, prev, pager, next"
                @size-change="handleTaskPageSizeChange"
                @current-change="handleTaskPageChange"
              />
            </div>
          </div>
        </el-tab-pane>

        <!-- 活动任务 -->
        <el-tab-pane label="活动任务" name="active">
          <div class="active-tasks-panel">
            <el-table 
              :data="activeTasks" 
              v-loading="activeTasksLoading"
              stripe
              style="width: 100%"
            >
              <el-table-column prop="task_name" label="任务名称" width="200" show-overflow-tooltip />
              <el-table-column prop="status" label="状态" width="100">
                <template #default="{ row }">
                  <el-tag :type="getStatusType(row.status)" size="small">
                    {{ getStatusText(row.status) }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="worker_name" label="Worker" width="150" show-overflow-tooltip />
              <el-table-column prop="started_at" label="开始时间" width="150">
                <template #default="{ row }">
                  {{ row.started_at ? formatDateTime(row.started_at) : '-' }}
                </template>
              </el-table-column>
              <el-table-column label="运行时长" width="100">
                <template #default="{ row }">
                  {{ row.started_at ? formatDuration(row.started_at) : '-' }}
                </template>
              </el-table-column>
              <el-table-column label="操作" width="150">
                <template #default="{ row }">
                  <el-button 
                    type="warning" 
                    size="small" 
                    @click="revokeTask(row.task_id, true)"
                  >
                    强制终止
                  </el-button>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </el-tab-pane>

        <!-- 定时任务 -->
        <el-tab-pane label="定时任务" name="scheduled">
          <div class="scheduled-tasks-panel">
            <el-table 
              :data="scheduledTasks" 
              v-loading="scheduledLoading"
              stripe
              style="width: 100%"
            >
              <el-table-column prop="name" label="任务名称" width="200" />
              <el-table-column prop="task" label="任务路径" width="300" show-overflow-tooltip />
              <el-table-column prop="schedule" label="调度规则" width="150" />
              <el-table-column prop="queue" label="队列" width="100" />
              <el-table-column prop="description" label="描述" show-overflow-tooltip />
            </el-table>
          </div>
        </el-tab-pane>

        <!-- 统计图表 -->
        <el-tab-pane label="统计图表" name="charts">
          <div class="charts-panel">
            <!-- 队列统计 -->
            <div class="chart-card">
              <h3>队列任务分布</h3>
              <div id="queueChart" style="width: 100%; height: 300px;"></div>
            </div>

            <!-- 错误分类统计 -->
            <div class="chart-card">
              <h3>错误分类统计</h3>
              <div id="errorChart" style="width: 100%; height: 300px;"></div>
            </div>
          </div>
        </el-tab-pane>
      </el-tabs>
    </div>

    <!-- 任务详情对话框 -->
    <el-dialog 
      v-model="showTaskDetail" 
      title="任务详情" 
      width="800px"
      :close-on-click-modal="false"
    >
      <div v-if="selectedTask" class="task-detail">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="任务ID">{{ selectedTask.task_id }}</el-descriptions-item>
          <el-descriptions-item label="任务名称">{{ selectedTask.task_name }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="getStatusType(selectedTask.status)">
              {{ getStatusText(selectedTask.status) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="队列">{{ selectedTask.queue_name }}</el-descriptions-item>
          <el-descriptions-item label="Worker">{{ selectedTask.worker_name || '-' }}</el-descriptions-item>
          <el-descriptions-item label="执行时长">
            {{ selectedTask.runtime_seconds ? `${selectedTask.runtime_seconds.toFixed(2)}s` : '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="重试次数">{{ selectedTask.retries }}/{{ selectedTask.max_retries }}</el-descriptions-item>
          <el-descriptions-item label="错误类型">{{ selectedTask.error_category || '-' }}</el-descriptions-item>
          <el-descriptions-item label="创建时间">{{ formatDateTime(selectedTask.created_at) }}</el-descriptions-item>
          <el-descriptions-item label="完成时间">{{ selectedTask.completed_at ? formatDateTime(selectedTask.completed_at) : '-' }}</el-descriptions-item>
        </el-descriptions>

        <!-- 参数信息 -->
        <div v-if="selectedTask.args || selectedTask.kwargs" style="margin-top: 20px;">
          <h4>参数信息</h4>
          <el-tabs>
            <el-tab-pane v-if="selectedTask.args" label="位置参数">
              <pre>{{ JSON.stringify(selectedTask.args, null, 2) }}</pre>
            </el-tab-pane>
            <el-tab-pane v-if="selectedTask.kwargs" label="关键字参数">
              <pre>{{ JSON.stringify(selectedTask.kwargs, null, 2) }}</pre>
            </el-tab-pane>
          </el-tabs>
        </div>

        <!-- 结果/错误信息 -->
        <div v-if="selectedTask.result" style="margin-top: 20px;">
          <h4>{{ selectedTask.status === 'FAILURE' ? '错误信息' : '执行结果' }}</h4>
          <el-input 
            type="textarea" 
            :rows="6" 
            :value="JSON.stringify(selectedTask.result, null, 2)" 
            readonly
          />
        </div>

        <!-- 堆栈跟踪 -->
        <div v-if="selectedTask.traceback" style="margin-top: 20px;">
          <h4>堆栈跟踪</h4>
          <el-input 
            type="textarea" 
            :rows="10" 
            :value="selectedTask.traceback" 
            readonly
            style="font-family: monospace;"
          />
        </div>
      </div>

      <template #footer>
        <el-button @click="showTaskDetail = false">关闭</el-button>
        <el-button 
          v-if="selectedTask?.status === 'FAILURE'" 
          type="primary" 
          @click="retryTask(selectedTask.task_id)"
        >
          重试任务
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Refresh,
  DataBoard,
  Monitor,
  Document,
  Search
} from '@element-plus/icons-vue'
import request from '@/utils/request'
import * as echarts from 'echarts'

// 响应式数据
const loading = ref(false)
const activeTab = ref('tasks')

// 调试信息
console.log('🚀 CeleryMonitor组件初始化')

// 仪表板数据
const dashboardStats = ref<any>({})
const systemStatus = ref<any>({})
const beatHealth = ref<any>(null)

// 任务相关数据
const taskHistory = ref<any[]>([])
const activeTasks = ref<any[]>([])
const scheduledTasks = ref<any[]>([])
const tasksLoading = ref(false)
const activeTasksLoading = ref(false)
const scheduledLoading = ref(false)

// 任务筛选
const taskFilters = ref({
  hours: 24,
  taskName: ''
})

// 分页
const taskPagination = ref({
  page: 1,
  size: 50,
  total: 0
})

// 任务详情对话框
const showTaskDetail = ref(false)
const selectedTask = ref<any>(null)

// 自动刷新定时器
let refreshTimer: NodeJS.Timeout | null = null

// 生命周期
onMounted(() => {
  console.log('🎯 Celery监控页面已挂载，开始初始化数据...')
  refreshData()
  startAutoRefresh()
})

onUnmounted(() => {
  stopAutoRefresh()
})

// 刷新所有数据
const refreshData = async () => {
  console.log('🔄 开始刷新所有数据...')
  loading.value = true
  try {
    await Promise.all([
      loadDashboardStats(),
      loadSystemStatus(), 
      loadBeatHealth(),
      loadTaskHistory(),
      loadActiveTasks(),
      loadScheduledTasks()
    ])
    console.log('✅ 所有数据刷新完成')
  } catch (error) {
    console.error('❌ 数据刷新过程中出错:', error)
  } finally {
    loading.value = false
  }
}

// 加载仪表板统计
const loadDashboardStats = async () => {
  try {
    console.log('🔄 开始加载仪表板统计...')
    const response = await request.get('/api/v1/celery/dashboard')
    console.log('📥 仪表板API响应:', response)
    
    if (response.success) {
      dashboardStats.value = response.data
      console.log('✅ 仪表板数据已更新:', dashboardStats.value)
    } else {
      console.warn('⚠️ 仪表板API返回失败:', response)
    }
  } catch (error) {
    console.error('❌ 加载仪表板统计失败:', error)
    console.error('错误详情:', error.response || error.message || error)
  }
}

// 加载系统状态
const loadSystemStatus = async () => {
  try {
    console.log('🔄 开始加载系统状态...')
    const response = await request.get('/api/v1/celery/system-status')
    console.log('📥 系统状态API响应:', response)
    
    if (response.success) {
      systemStatus.value = response.data
      console.log('✅ 系统状态数据已更新:', systemStatus.value)
    } else {
      console.warn('⚠️ 系统状态API返回失败:', response)
    }
  } catch (error) {
    console.error('❌ 加载系统状态失败:', error)
    console.error('错误详情:', error.response || error.message || error)
  }
}

// 加载Beat健康状态
const loadBeatHealth = async () => {
  try {
    console.log('🔄 开始加载Beat健康状态...')
    const response = await request.get('/api/v1/celery/beat/health')
    console.log('📥 Beat健康API响应:', response)
    
    if (response.success) {
      beatHealth.value = response.data
      console.log('✅ Beat健康数据已更新:', beatHealth.value)
    } else {
      console.warn('⚠️ Beat健康API返回失败:', response)
    }
  } catch (error) {
    console.error('❌ 加载Beat健康状态失败:', error)
    console.error('错误详情:', error.response || error.message || error)
  }
}

// 加载任务历史
const loadTaskHistory = async () => {
  tasksLoading.value = true
  try {
    console.log('🔄 开始加载任务历史...')
    const params = {
      hours: taskFilters.value.hours,
      page: taskPagination.value.page,
      size: taskPagination.value.size,
      ...(taskFilters.value.taskName && { task_name: taskFilters.value.taskName })
    }
    
    const response = await request.get('/api/v1/celery/tasks', { params })
    console.log('📥 任务历史API响应:', response)
    
    if (response.success) {
      taskHistory.value = response.data.tasks
      taskPagination.value.total = response.data.pagination.total
      console.log('✅ 任务历史数据已更新:', taskHistory.value.length, '个任务')
    } else {
      console.warn('⚠️ 任务历史API返回失败:', response)
    }
  } catch (error) {
    console.error('❌ 加载任务历史失败:', error)
    console.error('错误详情:', error.response || error.message || error)
  } finally {
    tasksLoading.value = false
  }
}

// 加载活动任务
const loadActiveTasks = async () => {
  activeTasksLoading.value = true
  try {
    console.log('🔄 开始加载活动任务...')
    const response = await request.get('/api/v1/celery/tasks/active')
    console.log('📥 活动任务API响应:', response)
    
    if (response.success) {
      activeTasks.value = response.data
      console.log('✅ 活动任务数据已更新:', activeTasks.value.length, '个任务')
    } else {
      console.warn('⚠️ 活动任务API返回失败:', response)
    }
  } catch (error) {
    console.error('❌ 加载活动任务失败:', error)
    console.error('错误详情:', error.response || error.message || error)
  } finally {
    activeTasksLoading.value = false
  }
}

// 加载定时任务
const loadScheduledTasks = async () => {
  scheduledLoading.value = true
  try {
    console.log('🔄 开始加载定时任务...')
    const response = await request.get('/api/v1/celery/scheduled-tasks')
    console.log('📥 定时任务API响应:', response)
    
    if (response.success) {
      scheduledTasks.value = response.data
      console.log('✅ 定时任务数据已更新:', scheduledTasks.value.length, '个任务')
    } else {
      console.warn('⚠️ 定时任务API返回失败:', response)
    }
  } catch (error) {
    console.error('❌ 加载定时任务失败:', error)
    console.error('错误详情:', error.response || error.message || error)
  } finally {
    scheduledLoading.value = false
  }
}

// Tab切换处理
const handleTabClick = (tab: any) => {
  if (tab.name === 'charts') {
    setTimeout(() => {
      renderCharts()
    }, 100)
  }
}

// 渲染图表
const renderCharts = () => {
  // 队列统计图表
  const queueChart = echarts.init(document.getElementById('queueChart'))
  const queueData = dashboardStats.value.queue_stats || []
  
  queueChart.setOption({
    title: { text: '队列任务分布' },
    tooltip: { trigger: 'item' },
    series: [{
      type: 'pie',
      radius: '50%',
      data: queueData.map((item: any) => ({
        name: item.queue,
        value: item.count
      }))
    }]
  })

  // 错误分类图表
  const errorChart = echarts.init(document.getElementById('errorChart'))
  const errorData = dashboardStats.value.error_stats || []
  
  errorChart.setOption({
    title: { text: '错误分类统计' },
    tooltip: { trigger: 'axis' },
    xAxis: {
      type: 'category',
      data: errorData.map((item: any) => item.category)
    },
    yAxis: { type: 'value' },
    series: [{
      type: 'bar',
      data: errorData.map((item: any) => item.count)
    }]
  })
}

// 任务状态相关函数
const getStatusType = (status: string) => {
  const statusMap: Record<string, string> = {
    'SUCCESS': 'success',
    'FAILURE': 'danger',
    'PENDING': 'info',
    'STARTED': 'warning',
    'RETRY': 'warning',
    'REVOKED': 'info'
  }
  return statusMap[status] || 'info'
}

const getStatusText = (status: string) => {
  const statusMap: Record<string, string> = {
    'SUCCESS': '成功',
    'FAILURE': '失败',
    'PENDING': '等待中',
    'STARTED': '执行中',
    'RETRY': '重试中',
    'REVOKED': '已撤销'
  }
  return statusMap[status] || status
}

// 重试任务
const retryTask = async (taskId: string) => {
  try {
    await ElMessageBox.confirm('确认要重试这个任务吗？', '确认重试', {
      type: 'warning'
    })
    
    const response = await request.post('/api/v1/celery/tasks/retry', {
      task_id: taskId,
      force: false
    })
    
    if (response.data.success) {
      ElMessage.success('任务重试已提交')
      loadTaskHistory()
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('重试任务失败')
    }
  }
}

// 撤销任务
const revokeTask = async (taskId: string, terminate: boolean = false) => {
  try {
    const action = terminate ? '强制终止' : '撤销'
    await ElMessageBox.confirm(`确认要${action}这个任务吗？`, `确认${action}`, {
      type: 'warning'
    })
    
    const response = await request.post(`/api/v1/celery/tasks/${taskId}/revoke?terminate=${terminate}`)
    
    if (response.data.success) {
      ElMessage.success(`任务${action}成功`)
      loadActiveTasks()
      loadTaskHistory()
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(`${terminate ? '终止' : '撤销'}任务失败`)
    }
  }
}

// 查看任务详情
const viewTaskDetail = (task: any) => {
  selectedTask.value = task
  showTaskDetail.value = true
}

// 分页处理
const handleTaskPageSizeChange = (size: number) => {
  taskPagination.value.size = size
  taskPagination.value.page = 1
  loadTaskHistory()
}

const handleTaskPageChange = (page: number) => {
  taskPagination.value.page = page
  loadTaskHistory()
}

// 自动刷新
const startAutoRefresh = () => {
  refreshTimer = setInterval(() => {
    loadDashboardStats()
    loadSystemStatus()
    loadBeatHealth()
    if (activeTab.value === 'active') {
      loadActiveTasks()
    }
  }, 30000) // 30秒刷新一次
}

const stopAutoRefresh = () => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
    refreshTimer = null
  }
}

// 工具函数
const formatDateTime = (dateString: string) => {
  if (!dateString) return '-'
  return new Date(dateString).toLocaleString('zh-CN')
}

const formatRelativeTime = (dateString: string) => {
  if (!dateString) return '-'
  const date = new Date(dateString)
  const now = new Date()
  const diff = Math.floor((now.getTime() - date.getTime()) / 1000)
  
  if (diff < 60) return '刚刚'
  if (diff < 3600) return `${Math.floor(diff / 60)}分钟前`
  if (diff < 86400) return `${Math.floor(diff / 3600)}小时前`
  return `${Math.floor(diff / 86400)}天前`
}

const formatDuration = (startTime: string) => {
  if (!startTime) return '-'
  const start = new Date(startTime)
  const now = new Date()
  const diff = Math.floor((now.getTime() - start.getTime()) / 1000)
  
  const hours = Math.floor(diff / 3600)
  const minutes = Math.floor((diff % 3600) / 60)
  const seconds = diff % 60
  
  if (hours > 0) return `${hours}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`
  return `${minutes}:${seconds.toString().padStart(2, '0')}`
}
</script>

<style scoped>
.celery-monitor {
  padding: 24px;
  background: #f5f5f5;
  min-height: 100vh;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
  background: white;
  padding: 24px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.page-title {
  font-size: 28px;
  font-weight: 600;
  color: #2c3e50;
  margin: 0 0 8px 0;
}

.page-description {
  color: #7f8c8d;
  font-size: 16px;
}

.status-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}

.status-card {
  background: white;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.status-card.beat-health.healthy {
  border-left: 4px solid #67C23A;
}

.status-card.beat-health.unhealthy {
  border-left: 4px solid #F56C6C;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.card-title {
  font-size: 14px;
  font-weight: 600;
  color: #666;
  text-transform: uppercase;
}

.big-number {
  font-size: 32px;
  font-weight: 700;
  color: #2c3e50;
  line-height: 1;
}

.success-rate {
  color: #67C23A;
  font-size: 14px;
  margin: 8px 0;
}

.stat-item {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
}

.stat-label {
  color: #666;
  font-size: 13px;
}

.stat-value {
  font-weight: 600;
  color: #2c3e50;
  font-size: 13px;
}

.stat-row {
  display: flex;
  justify-content: space-between;
  margin-top: 12px;
  font-size: 13px;
}

.stat-row .success {
  color: #67C23A;
}

.stat-row .failed {
  color: #F56C6C;
}

.main-content {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  padding: 24px;
}

.filter-bar {
  display: flex;
  align-items: center;
  margin-bottom: 16px;
}

.pagination-container {
  display: flex;
  justify-content: center;
  margin-top: 24px;
}

.chart-card {
  background: #f8f9fa;
  padding: 20px;
  border-radius: 8px;
  margin-bottom: 20px;
}

.chart-card h3 {
  margin: 0 0 16px 0;
  color: #2c3e50;
}

.task-detail {
  max-height: 600px;
  overflow-y: auto;
}

.task-detail pre {
  background: #f8f9fa;
  padding: 12px;
  border-radius: 4px;
  font-size: 12px;
  max-height: 200px;
  overflow-y: auto;
}
</style>