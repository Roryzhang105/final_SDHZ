<template>
  <div class="page-content-full task-list">
    <el-card class="filter-card" shadow="hover">
      <template #header>
        <div class="card-header">
          <div class="header-left">
            <span>任务列表</span>
            <div class="connection-status">
              <el-tag 
                v-if="wsClient" 
                :type="wsClient.connectionStatus.value.connected ? 'success' : 'warning'"
                size="small"
              >
                {{ wsClient.connectionStatus.value.connected ? '实时连接' : '连接中...' }}
              </el-tag>
            </div>
          </div>
          <el-button type="primary" :icon="Upload" @click="handleUploadNew">
            上传新图片
          </el-button>
        </div>
      </template>
      
      <el-form :inline="true" :model="filterForm" class="filter-form">
        <el-form-item label="快递单号">
          <el-input 
            v-model="filterForm.trackingNumber" 
            placeholder="请输入快递单号"
            clearable
            @keyup.enter="handleSearch"
          />
        </el-form-item>
        <el-form-item label="案号">
          <el-input 
            v-model="filterForm.caseNumber" 
            placeholder="请输入案号"
            clearable
            @keyup.enter="handleSearch"
          />
        </el-form-item>
        <el-form-item label="文书类型">
          <el-input 
            v-model="filterForm.documentType" 
            placeholder="请输入文书类型"
            clearable
            @keyup.enter="handleSearch"
          />
        </el-form-item>
        <el-form-item label="受送达人">
          <el-input 
            v-model="filterForm.receiver" 
            placeholder="请输入受送达人"
            clearable
            @keyup.enter="handleSearch"
          />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="filterForm.status" placeholder="请选择状态" clearable>
            <el-option label="全部" value="" />
            <el-option label="待处理" value="pending" />
            <el-option label="识别中" value="recognizing" />
            <el-option label="查询物流中" value="tracking" />
            <el-option label="已签收" value="delivered" />
            <el-option label="生成文档中" value="generating" />
            <el-option label="已完成" value="completed" />
            <el-option label="失败" value="failed" />
          </el-select>
        </el-form-item>
        <el-form-item label="排序">
          <el-select v-model="filterForm.sortBy" placeholder="请选择排序方式">
            <el-option label="最新优先" value="created_desc" />
            <el-option label="最早优先" value="created_asc" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :icon="Search" @click="handleSearch">搜索</el-button>
          <el-button :icon="Refresh" @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card class="table-card" shadow="hover">
      <div class="table-container">
        <el-table
          :data="tableData"
          :loading="loading"
          stripe
          border
          style="width: 100%"
          row-key="id"
          @sort-change="handleSortChange"
        >
        <el-table-column prop="task_id" :width="showTaskIdColumn ? 180 : 40" class-name="collapsible-column">
          <template #header>
            <div class="collapsible-header" @click="toggleTaskIdColumn">
              <div v-if="showTaskIdColumn" class="header-content">
                <span class="column-title">任务ID</span>
                <div class="collapse-controls">
                  <span class="hide-text">隐藏</span>
                  <el-icon class="collapse-icon">
                    <ArrowLeft />
                  </el-icon>
                </div>
              </div>
              <el-icon v-else class="collapse-icon collapsed">
                <ArrowRight />
              </el-icon>
            </div>
          </template>
          <template #default="{ row }" v-if="showTaskIdColumn">
            {{ row.task_id }}
          </template>
          <template #default v-else>
            <div class="collapsed-content">
              <el-icon class="expand-icon" @click="toggleTaskIdColumn">
                <ArrowRight />
              </el-icon>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="tracking_number" :width="showTrackingNumberColumn ? 150 : 40" class-name="collapsible-column">
          <template #header>
            <div class="collapsible-header" @click="toggleTrackingNumberColumn">
              <div v-if="showTrackingNumberColumn" class="header-content">
                <span class="column-title">快递单号</span>
                <div class="collapse-controls">
                  <span class="hide-text">隐藏</span>
                  <el-icon class="collapse-icon">
                    <ArrowLeft />
                  </el-icon>
                </div>
              </div>
              <el-icon v-else class="collapse-icon collapsed">
                <ArrowRight />
              </el-icon>
            </div>
          </template>
          <template #default="{ row }" v-if="showTrackingNumberColumn">
            <span v-if="row.tracking_number">{{ row.tracking_number }}</span>
            <el-tag v-else type="info" size="small">未识别</el-tag>
          </template>
          <template #default v-else>
            <div class="collapsed-content">
              <el-icon class="expand-icon" @click="toggleTrackingNumberColumn">
                <ArrowRight />
              </el-icon>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" width="180" sortable="custom" class-name="sortable-column">
          <template #header>
            <div class="sortable-header">
              <span>创建时间</span><el-icon :class="['sort-icon', getSortClass('created_at')]"><component :is="getSortIcon('created_at')" /></el-icon>
            </div>
          </template>
          <template #default="{ row }">
            {{ formatDateTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column prop="case_number" width="120" sortable="custom" class-name="sortable-column">
          <template #header>
            <div class="sortable-header">
              <span>案号</span><el-icon :class="['sort-icon', getSortClass('case_number')]"><component :is="getSortIcon('case_number')" /></el-icon>
            </div>
          </template>
          <template #default="{ row }">
            <span v-if="row.case_number" class="case-number">{{ extractCaseNumber(row.case_number) }}</span>
            <el-tag v-else type="info" size="small">未设置</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="document_type" label="文书类型" min-width="120">
          <template #default="{ row }">
            <span v-if="row.document_type" class="document-type">{{ row.document_type }}</span>
            <el-tag v-else type="info" size="small">未设置</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="receiver" label="受送达人" min-width="100">
          <template #default="{ row }">
            <span v-if="row.receiver" class="receiver">{{ row.receiver }}</span>
            <el-tag v-else type="info" size="small">未填写</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" width="140" sortable="custom" class-name="sortable-column">
          <template #header>
            <div class="sortable-header">
              <span>当前状态</span><el-icon :class="['sort-icon', getSortClass('status')]"><component :is="getSortIcon('status')" /></el-icon>
            </div>
          </template>
          <template #default="{ row }">
            <el-tag 
              :type="getStatusType(row.status)"
              :class="`status-${getStatusType(row.status)}`"
            >
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button
              type="primary"
              size="small"
              :icon="View"
              @click="handleView(row)"
            >
              查看详情
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      </div>

      <div class="pagination-container">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.size"
          :page-sizes="[10, 20, 50, 100]"
          :total="pagination.total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>

    <!-- 任务详情对话框 -->
    <el-dialog
      v-model="dialogVisible"
      title="任务详情"
      width="80%"
      :before-close="handleCloseDialog"
    >
      <div v-if="currentTask" class="detail-content">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="任务ID">
            {{ currentTask.task_id }}
          </el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="getStatusType(currentTask.status)">
              {{ getStatusText(currentTask.status) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="快递单号">
            {{ currentTask.tracking_number || '未识别' }}
          </el-descriptions-item>
          <el-descriptions-item label="创建时间">
            {{ formatDateTime(currentTask.created_at) }}
          </el-descriptions-item>
          <el-descriptions-item label="更新时间">
            {{ formatDateTime(currentTask.updated_at) }}
          </el-descriptions-item>
          <el-descriptions-item label="完成进度">
            {{ currentTask.progress || getProgressPercentage(currentTask.status) }}%
          </el-descriptions-item>
        </el-descriptions>
        
        <!-- 处理步骤 -->
        <div class="process-steps">
          <h4>处理步骤</h4>
          <el-steps :active="getStepIndex(currentTask.status)" finish-status="success">
            <el-step title="图片上传" description="上传包含二维码的图片" />
            <el-step title="二维码识别" description="识别图片中的二维码" />
            <el-step title="物流查询" description="查询快递物流信息" />
            <el-step title="文档生成" description="生成送达回证文档" />
            <el-step title="任务完成" description="任务处理完成" />
          </el-steps>
        </div>
        
        <!-- 上传的图片 -->
        <div v-if="currentTask.image_url" class="image-section">
          <h4>上传的图片</h4>
          <el-image
            :src="currentTask.image_url"
            :preview-src-list="[currentTask.image_url]"
            fit="contain"
            style="width: 300px; height: 200px; border: 1px solid #ddd; border-radius: 4px;"
          >
            <template #error>
              <div class="image-slot">
                <el-icon><Picture /></el-icon>
                <p>图片加载失败</p>
              </div>
            </template>
          </el-image>
        </div>
        
        <!-- 识别结果 -->
        <div v-if="currentTask.qr_result" class="qr-result-section">
          <h4>二维码识别结果</h4>
          <pre class="qr-result">{{ currentTask.qr_result }}</pre>
        </div>
        
        <!-- 错误信息 -->
        <div v-if="currentTask.error_message && currentTask.status === 'failed'" class="error-section">
          <h4>错误信息</h4>
          <el-alert
            :title="currentTask.error_message"
            type="error"
            :closable="false"
            show-icon
          />
        </div>
        
        <!-- 文档下载 -->
        <div v-if="currentTask.status === 'completed' && currentTask.document_url" class="download-section">
          <h4>生成的文档</h4>
          <el-button type="success" :icon="Download" @click="handleDownload(currentTask)">
            下载送达回证
          </el-button>
        </div>
      </div>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">关闭</el-button>
          <el-button 
            v-if="currentTask && currentTask.status === 'completed'" 
            type="primary" 
            :icon="Download"
            @click="handleDownload(currentTask)"
          >
            下载文档
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Upload,
  Search,
  Refresh,
  View,
  Download,
  Picture,
  ArrowRight,
  ArrowLeft,
  ArrowUp,
  ArrowDown,
  Sort
} from '@element-plus/icons-vue'
import { tasksApi } from '@/api/tasks'
import { useWebSocket, type WebSocketMessage } from '@/utils/websocket'
import { useAuthStore } from '@/stores/auth'
import type { Task, TaskStatus, SortState } from '@/types'

const router = useRouter()
const authStore = useAuthStore()

// 响应式数据
const loading = ref(false)
const dialogVisible = ref(false)
const tableData = ref<Task[]>([])
const currentTask = ref<Task | null>(null)

// 控制列显示的独立变量
const showTaskIdColumn = ref(true)
const showTrackingNumberColumn = ref(true)

// 排序状态
const sortState = ref<SortState>({
  column: null,
  order: null
})

// WebSocket客户端
let wsClient: ReturnType<typeof useWebSocket> | null = null

// 筛选表单
const filterForm = reactive({
  trackingNumber: '',
  caseNumber: '',
  documentType: '',
  receiver: '',
  status: '',
  sortBy: 'created_desc'
})

// 分页配置
const pagination = reactive({
  page: 1,
  size: 20,
  total: 0
})

// 任务状态映射
const statusMap: Record<string, { text: string; type: string; progress: number }> = {
  pending: { text: '待处理', type: 'info', progress: 10 },
  recognizing: { text: '识别中', type: 'warning', progress: 25 },
  tracking: { text: '查询物流中', type: 'warning', progress: 50 },
  delivered: { text: '已签收', type: 'success', progress: 75 },
  generating: { text: '生成文档中', type: 'warning', progress: 90 },
  completed: { text: '已完成', type: 'success', progress: 100 },
  failed: { text: '失败', type: 'danger', progress: 0 }
}

// 获取列表数据
const fetchList = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      size: pagination.size,
      tracking_number: filterForm.trackingNumber,
      case_number: filterForm.caseNumber,
      document_type: filterForm.documentType,
      receiver: filterForm.receiver,
      status: filterForm.status,
      sort_by: filterForm.sortBy
    }
    
    // 调用真实API
    const response = await tasksApi.getTaskList(params)
    tableData.value = response.data.items || []
    pagination.total = response.data.total || 0
  } catch (error) {
    console.error('获取任务列表失败:', error)
    ElMessage.error('获取任务列表失败')
  } finally {
    loading.value = false
  }
}


// 状态类型映射
const getStatusType = (status: string) => {
  return statusMap[status]?.type || 'info'
}

// 状态文本映射
const getStatusText = (status: string) => {
  return statusMap[status]?.text || '未知'
}

// 获取进度百分比
const getProgressPercentage = (status: string) => {
  return statusMap[status]?.progress || 0
}

// 获取进度状态
const getProgressStatus = (status: string) => {
  if (status === 'failed') return 'exception'
  if (status === 'completed') return 'success'
  return undefined
}

// 获取步骤索引
const getStepIndex = (status: string) => {
  const stepMap: Record<string, number> = {
    pending: 0,
    recognizing: 1,
    tracking: 2,
    delivered: 2,
    generating: 3,
    completed: 4,
    failed: -1
  }
  return stepMap[status] || 0
}

// 切换任务ID列显示状态
const toggleTaskIdColumn = () => {
  showTaskIdColumn.value = !showTaskIdColumn.value
}

// 切换快递单号列显示状态
const toggleTrackingNumberColumn = () => {
  showTrackingNumberColumn.value = !showTrackingNumberColumn.value
}

// 提取案号数字部分
const extractCaseNumber = (fullCaseNumber: string) => {
  if (!fullCaseNumber) return null
  
  // 使用正则表达式匹配"第xxxx号"格式中的数字
  const match = fullCaseNumber.match(/第(\d+)号/)
  return match ? match[1] : fullCaseNumber // 如果匹配不到，返回原始值
}

// 处理排序变化
const handleSortChange = ({ prop, order }: { prop: string | null, order: 'ascending' | 'descending' | null }) => {
  console.log('排序变化:', { prop, order })
  
  // 更新排序状态
  if (prop && order) {
    sortState.value.column = prop
    sortState.value.order = order === 'ascending' ? 'asc' : 'desc'
    
    // 映射到后端的排序字段
    let sortBy = ''
    if (prop === 'created_at') {
      sortBy = order === 'ascending' ? 'created_asc' : 'created_desc'
    } else if (prop === 'status') {
      sortBy = order === 'ascending' ? 'status_asc' : 'status_desc'
    } else if (prop === 'case_number') {
      sortBy = order === 'ascending' ? 'case_number_asc' : 'case_number_desc'
    }
    
    filterForm.sortBy = sortBy
  } else {
    // 取消排序，恢复默认
    sortState.value.column = null
    sortState.value.order = null
    filterForm.sortBy = 'created_desc'
  }
  
  // 重新获取数据
  pagination.page = 1
  fetchList()
}

// 获取排序图标
const getSortIcon = (column: string) => {
  if (sortState.value.column !== column) {
    return Sort // 无排序状态
  }
  
  return sortState.value.order === 'asc' ? ArrowUp : ArrowDown
}

// 获取排序状态类名
const getSortClass = (column: string) => {
  if (sortState.value.column !== column) {
    return 'sort-none'
  }
  
  return sortState.value.order === 'asc' ? 'sort-asc' : 'sort-desc'
}

// 格式化日期时间
const formatDateTime = (dateString: string) => {
  if (!dateString) return '-'
  try {
    const date = new Date(dateString)
    if (isNaN(date.getTime())) {
      return '-'
    }
    return date.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    })
  } catch (error) {
    console.error('日期格式化失败:', error)
    return '-'
  }
}

// 处理搜索
const handleSearch = () => {
  pagination.page = 1
  fetchList()
}

// 处理重置
const handleReset = () => {
  Object.assign(filterForm, {
    trackingNumber: '',
    caseNumber: '',
    documentType: '',
    receiver: '',
    status: '',
    sortBy: 'created_desc'
  })
  pagination.page = 1
  fetchList()
}

// 处理上传新图片
const handleUploadNew = () => {
  router.push('/app/delivery/generate')
}

// 处理查看详情
const handleView = (row: any) => {
  router.push(`/app/delivery/detail/${row.task_id}`)
}

// 处理下载
const handleDownload = async (row: any) => {
  try {
    if (!row.document_url) {
      ElMessage.warning('文档尚未生成完成')
      return
    }
    
    // 模拟下载
    ElMessage.success('下载开始')
    // 实际项目中应该调用真实的下载API
    // const response = await taskApi.download(row.task_id)
    // downloadFile(response.data, `送达回证_${row.tracking_number}.docx`)
    
  } catch (error) {
    console.error('下载失败:', error)
    ElMessage.error('下载失败')
  }
}

// 处理分页大小变化
const handleSizeChange = (size: number) => {
  pagination.size = size
  pagination.page = 1
  fetchList()
}

// 处理当前页变化
const handleCurrentChange = (page: number) => {
  pagination.page = page
  fetchList()
}

// 关闭对话框
const handleCloseDialog = () => {
  dialogVisible.value = false
  currentTask.value = null
}

// WebSocket连接和消息处理
const initWebSocket = () => {
  const token = authStore.token
  if (!token) {
    console.warn('未找到认证token，无法建立WebSocket连接')
    return
  }
  
  wsClient = useWebSocket(token)
  if (!wsClient) {
    console.error('WebSocket客户端创建失败')
    return
  }
  
  // 监听连接状态变化
  wsClient.onConnectionChange((connected: boolean) => {
    if (connected) {
      console.log('WebSocket连接成功')
      ElMessage.success('实时连接已建立')
    } else {
      console.log('WebSocket连接断开')
      ElMessage.warning('实时连接已断开，正在尝试重连...')
    }
  })
  
  // 监听任务状态更新
  wsClient.on('task_update', handleTaskUpdate)
  wsClient.on('status_changed', handleTaskUpdate)
  wsClient.on('recognition_started', handleTaskUpdate)
  wsClient.on('recognition_completed', handleTaskUpdate)
  wsClient.on('recognition_failed', handleTaskUpdate)
  wsClient.on('tracking_started', handleTaskUpdate)
  wsClient.on('package_delivered', handleTaskUpdate)
  wsClient.on('generating_documents', handleTaskUpdate)
  wsClient.on('task_completed', handleTaskUpdate)
  wsClient.on('task_failed', handleTaskUpdate)
  
  // 监听新任务创建
  wsClient.on('task_created', handleTaskCreated)
  
  // 建立连接
  wsClient.connect()
}

const handleTaskUpdate = (message: WebSocketMessage) => {
  console.log('收到任务更新:', message)
  
  const taskId = message.task_id
  if (!taskId) return
  
  // 查找并更新对应的任务
  const taskIndex = tableData.value.findIndex((task: any) => task.task_id === taskId)
  if (taskIndex !== -1) {
    // 更新现有任务
    const updatedTask = {
      ...tableData.value[taskIndex],
      status: message.status || tableData.value[taskIndex].status,
      progress: message.progress || getProgressPercentage(message.status || tableData.value[taskIndex].status),
      ...message.data
    }
    tableData.value[taskIndex] = updatedTask
    
    // 如果当前查看的是这个任务，也更新详情
    if (currentTask.value && currentTask.value.task_id === taskId) {
      currentTask.value = updatedTask
    }
    
    // 显示状态更新消息
    if (message.message) {
      ElMessage.info(`${taskId}: ${message.message}`)
    }
  } else {
    // 如果是新任务，重新获取列表
    console.log('检测到新任务，刷新列表')
    fetchList()
  }
}

const handleTaskCreated = (message: WebSocketMessage) => {
  console.log('收到新任务创建消息:', message)
  
  // 刷新任务列表以显示新创建的任务
  fetchList()
  
  // 显示任务创建成功的消息
  const taskId = message.task_id
  if (taskId) {
    ElMessage.success(`新任务 ${taskId} 已创建`)
  }
}

const cleanupWebSocket = () => {
  if (wsClient) {
    wsClient.disconnect()
    wsClient = null
  }
}

// 检查表格是否需要滚动
const checkTableScroll = () => {
  const container = document.querySelector('.table-container')
  if (container) {
    const hasScroll = container.scrollWidth > container.clientWidth
    container.classList.toggle('has-scroll', hasScroll)
    
    // 添加滚动事件监听
    let scrollTimer: NodeJS.Timeout
    container.addEventListener('scroll', () => {
      container.classList.add('scrolling')
      clearTimeout(scrollTimer)
      scrollTimer = setTimeout(() => {
        container.classList.remove('scrolling')
      }, 150)
    })
  }
}

// 组件挂载时获取数据并初始化WebSocket
onMounted(() => {
  fetchList()
  initWebSocket()
  
  // 延迟检查滚动，确保表格已渲染
  setTimeout(() => {
    checkTableScroll()
  }, 100)
})

// 组件卸载时清理WebSocket连接
onUnmounted(() => {
  cleanupWebSocket()
})
</script>

<style scoped>
.task-list {
  /* padding已通过page-content-full类提供 */
}

.filter-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 15px;
}

.connection-status {
  display: flex;
  align-items: center;
}

.filter-form {
  margin: 0;
}

.table-card {
  margin-bottom: 20px;
}

/* 表格容器滚动样式 */
.table-container {
  overflow-x: auto;
  overflow-y: hidden;
  border-radius: 6px;
  border: 1px solid #ebeef5;
  position: relative;
}

/* 自定义滚动条样式 */
.table-container::-webkit-scrollbar {
  height: 8px;
}

.table-container::-webkit-scrollbar-track {
  background: #f8f9fa;
  border-radius: 4px;
}

.table-container::-webkit-scrollbar-thumb {
  background: #d1d5db;
  border-radius: 4px;
  transition: background-color 0.3s ease;
}

.table-container::-webkit-scrollbar-thumb:hover {
  background: #9ca3af;
}

.table-container::-webkit-scrollbar-thumb:active {
  background: #6b7280;
}

/* Firefox滚动条样式 */
.table-container {
  scrollbar-width: thin;
  scrollbar-color: #d1d5db #f8f9fa;
}

/* 表格内边框调整 */
.table-container .el-table {
  border: none !important;
}

.table-container .el-table::before {
  display: none;
}

.table-container .el-table::after {
  display: none;
}

/* 滚动提示渐变遮罩 */
.table-container::after {
  content: '';
  position: absolute;
  top: 0;
  right: 0;
  width: 20px;
  height: 100%;
  background: linear-gradient(to left, rgba(255, 255, 255, 0.8), transparent);
  pointer-events: none;
  opacity: 0;
  transition: opacity 0.3s ease;
}

/* 当表格可以滚动时显示渐变提示 */
.table-container.has-scroll::after {
  opacity: 1;
}

/* 滚动时隐藏提示 */
.table-container.scrolling::after {
  opacity: 0;
}

.pagination-container {
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
}


.detail-content {
  padding: 20px 0;
}

.process-steps {
  margin: 30px 0;
}

.process-steps h4 {
  margin-bottom: 20px;
  color: #333;
}

.image-section {
  margin: 30px 0;
}

.image-section h4 {
  margin-bottom: 15px;
  color: #333;
}

.image-slot {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  background-color: #f5f7fa;
  color: #909399;
}

.image-slot p {
  margin-top: 10px;
  font-size: 14px;
}

.qr-result-section {
  margin: 30px 0;
}

.qr-result-section h4 {
  margin-bottom: 15px;
  color: #333;
}

.qr-result {
  background-color: #f5f7fa;
  padding: 15px;
  border-radius: 4px;
  font-family: monospace;
  color: #333;
  margin: 0;
  word-break: break-all;
}

.error-section {
  margin: 30px 0;
}

.error-section h4 {
  margin-bottom: 15px;
  color: #f56c6c;
}

.download-section {
  margin: 30px 0;
}

.download-section h4 {
  margin-bottom: 15px;
  color: #333;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

/* 状态标签样式 */
.status-success {
  background-color: #f0f9ff;
  color: #67c23a;
  border: 1px solid #e1f3d8;
}

.status-warning {
  background-color: #fdf6ec;
  color: #e6a23c;
  border: 1px solid #faecd8;
}

.status-danger {
  background-color: #fef0f0;
  color: #f56c6c;
  border: 1px solid #fde2e2;
}

.status-info {
  background-color: #f4f4f5;
  color: #909399;
  border: 1px solid #e4e7ed;
}

/* 新增列样式 */
.case-number {
  font-family: monospace;
  font-size: 13px;
  color: #606266;
  font-weight: 500;
}

.document-type {
  background-color: #ecf5ff;
  color: #409eff;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}

.receiver {
  color: #67c23a;
  font-weight: 500;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .filter-form .el-form-item {
    margin-bottom: 15px;
  }
  
  .card-header {
    flex-direction: column;
    gap: 15px;
    align-items: stretch;
  }
}

/* 折叠功能样式 */
.collapsible-header {
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  padding: 0 4px;
  transition: all 0.2s ease;
  min-height: 32px;
  width: 100%;
}

.collapsible-header:hover {
  background-color: #f5f7fa;
  border-radius: 4px;
}

.header-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
}

.column-title {
  font-weight: 500;
  color: #303133;
}

.collapse-controls {
  display: flex;
  align-items: center;
  gap: 4px;
}

.hide-text {
  font-size: 12px;
  color: #909399;
  font-weight: normal;
  transition: color 0.2s ease;
}

.collapsible-header:hover .hide-text {
  color: #409eff;
}

.collapse-icon {
  font-size: 14px;
  color: #909399;
  transition: transform 0.2s ease, color 0.2s ease;
  flex-shrink: 0;
}

.collapse-icon:hover,
.collapsible-header:hover .collapse-icon {
  color: #409eff;
}

.collapse-icon.collapsed {
  transform: rotate(0deg);
}

/* 折叠列样式 */
:deep(.collapsible-column) {
  transition: width 0.3s ease;
  overflow: hidden;
}

.collapsed-content {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  min-height: 32px;
}

.expand-icon {
  font-size: 14px;
  color: #909399;
  cursor: pointer;
  transition: color 0.2s ease, transform 0.2s ease;
  padding: 4px;
  border-radius: 4px;
}

.expand-icon:hover {
  color: #409eff;
  background-color: #f0f9ff;
  transform: scale(1.1);
}


/* 排序功能样式 */
.sortable-header {
  display: inline-block !important;
  white-space: nowrap !important;
  cursor: pointer;
  padding: 4px !important;
  transition: all 0.2s ease;
  border-radius: 4px;
  text-align: center !important;
  line-height: 1.4 !important;
  font-size: 14px !important;
}

.sortable-header:hover {
  background-color: #f0f9ff;
}

.sortable-header span {
  font-weight: 500;
  color: #303133;
  vertical-align: middle !important;
  display: inline !important;
}

.sort-icon {
  font-size: 12px !important;
  color: #c0c4cc;
  transition: color 0.2s ease, transform 0.2s ease;
  vertical-align: middle !important;
  display: inline-block !important;
  margin-left: 2px !important;
  width: 14px !important;
  height: 14px !important;
  line-height: 1 !important;
}

.sort-icon.sort-none {
  color: #c0c4cc;
}

.sort-icon.sort-asc,
.sort-icon.sort-desc {
  color: #409eff;
}

.sortable-header:hover .sort-icon {
  color: #409eff;
  transform: scale(1.1);
}

/* 排序列样式 - 强制覆盖Element Plus样式 */
:deep(.sortable-column) {
  .el-table__header .cell {
    padding: 8px 4px !important;
    white-space: nowrap !important;
    overflow: visible !important;
    text-overflow: clip !important;
    text-align: center !important;
    vertical-align: middle !important;
    line-height: 1 !important;
  }
  
  .el-table__header th {
    padding: 0 !important;
    height: auto !important;
    vertical-align: middle !important;
  }
  
  .el-table__header .cell .sortable-header {
    width: 100% !important;
    height: auto !important;
    line-height: 1.4 !important;
  }
  
  /* 强制所有图标内联显示 */
  .el-icon {
    display: inline-block !important;
    vertical-align: middle !important;
    width: 14px !important;
    height: 14px !important;
    line-height: 1 !important;
    margin-left: 2px !important;
  }
  
  .el-icon svg {
    display: inline-block !important;
    vertical-align: middle !important;
    width: 14px !important;
    height: 14px !important;
  }
  
  /* 特别针对Sort图标的样式 */
  .el-icon .sort-icon,
  .sortable-header .el-icon {
    margin-left: 2px !important;
    vertical-align: middle !important;
    display: inline-block !important;
  }
}

/* 响应式优化 */
@media (max-width: 768px) {
  .table-container::-webkit-scrollbar {
    height: 6px;
  }
  
  .table-container {
    border-radius: 4px;
  }
  
  /* 小屏幕下优化分页容器 */
  .pagination-container {
    overflow-x: auto;
    padding: 10px 0;
  }
  
  .pagination-container .el-pagination {
    white-space: nowrap;
  }
}

@media (max-width: 480px) {
  .table-container::-webkit-scrollbar {
    height: 4px;
  }
}

/* 大屏幕优化 */
@media (min-width: 1200px) {
  .case-number {
    font-size: 14px;
  }
  
  .document-type {
    font-size: 13px;
  }
  
  .sort-icon {
    font-size: 16px;
  }
  
  .table-container::-webkit-scrollbar {
    height: 10px;
  }
}
</style>