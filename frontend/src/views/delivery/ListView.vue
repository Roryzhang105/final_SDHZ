<template>
  <div class="task-list">
    <el-card class="filter-card" shadow="hover">
      <template #header>
        <div class="card-header">
          <span>任务列表</span>
          <el-button type="primary" :icon="Upload" @click="handleUploadNew">
            上传新图片
          </el-button>
        </div>
      </template>
      
      <el-form :inline="true" :model="filterForm" class="filter-form">
        <el-form-item label="任务ID">
          <el-input 
            v-model="filterForm.taskId" 
            placeholder="请输入任务ID"
            clearable
            @keyup.enter="handleSearch"
          />
        </el-form-item>
        <el-form-item label="快递单号">
          <el-input 
            v-model="filterForm.trackingNumber" 
            placeholder="请输入快递单号"
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
      <el-table
        :data="tableData"
        :loading="loading"
        stripe
        border
        style="width: 100%"
        row-key="id"
      >
        <el-table-column prop="task_id" label="任务ID" width="180" />
        <el-table-column prop="tracking_number" label="快递单号" min-width="150">
          <template #default="{ row }">
            <span v-if="row.tracking_number">{{ row.tracking_number }}</span>
            <el-tag v-else type="info" size="small">未识别</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="160">
          <template #default="{ row }">
            {{ formatDateTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="当前状态" width="120">
          <template #default="{ row }">
            <el-tag 
              :type="getStatusType(row.status)"
              :class="`status-${getStatusType(row.status)}`"
            >
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="进度" width="200">
          <template #default="{ row }">
            <div class="progress-container">
              <el-progress
                :percentage="getProgressPercentage(row.status)"
                :status="getProgressStatus(row.status)"
                :stroke-width="12"
                :show-text="false"
              />
              <span class="progress-text">{{ getProgressPercentage(row.status) }}%</span>
            </div>
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
            {{ getProgressPercentage(currentTask.status) }}%
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
  Picture
} from '@element-plus/icons-vue'

const router = useRouter()

// 响应式数据
const loading = ref(false)
const dialogVisible = ref(false)
const tableData = ref([])
const currentTask = ref(null)
let refreshTimer: number | null = null

// 筛选表单
const filterForm = reactive({
  taskId: '',
  trackingNumber: '',
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
const statusMap = {
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
      task_id: filterForm.taskId,
      tracking_number: filterForm.trackingNumber,
      status: filterForm.status,
      sort_by: filterForm.sortBy
    }
    
    // 模拟API调用
    const response = await mockApiCall(params)
    tableData.value = response.data.items
    pagination.total = response.data.total
  } catch (error) {
    console.error('获取任务列表失败:', error)
    ElMessage.error('获取任务列表失败')
  } finally {
    loading.value = false
  }
}

// 模拟API调用 (实际项目中应该调用真实API)
const mockApiCall = async (params: any) => {
  await new Promise(resolve => setTimeout(resolve, 1000))
  
  // 模拟数据
  const mockData = [
    {
      id: 1,
      task_id: 'task_1151242358360',
      tracking_number: '1151242358360',
      status: 'completed',
      created_at: '2024-01-30 14:30:00',
      updated_at: '2024-01-30 15:45:00',
      image_url: '/uploads/image1.jpg',
      qr_result: '1151242358360',
      document_url: '/downloads/receipt1.docx'
    },
    {
      id: 2,
      task_id: 'task_1151240728560',
      tracking_number: '1151240728560',
      status: 'generating',
      created_at: '2024-01-30 13:45:00',
      updated_at: '2024-01-30 14:20:00',
      image_url: '/uploads/image2.jpg',
      qr_result: '1151240728560'
    },
    {
      id: 3,
      task_id: 'task_1151238971060',
      tracking_number: null,
      status: 'recognizing',
      created_at: '2024-01-30 12:20:00',
      updated_at: '2024-01-30 12:25:00',
      image_url: '/uploads/image3.jpg'
    },
    {
      id: 4,
      task_id: 'task_1151235647120',
      tracking_number: null,
      status: 'failed',
      created_at: '2024-01-30 11:15:00',
      updated_at: '2024-01-30 11:20:00',
      image_url: '/uploads/image4.jpg',
      error_message: '图片中未检测到清晰的二维码'
    }
  ]
  
  return {
    data: {
      items: mockData,
      total: mockData.length
    }
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
  const stepMap = {
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

// 格式化日期时间
const formatDateTime = (dateString: string) => {
  if (!dateString) return '-'
  return new Date(dateString.replace(/-/g, '/')).toLocaleString('zh-CN')
}

// 处理搜索
const handleSearch = () => {
  pagination.page = 1
  fetchList()
}

// 处理重置
const handleReset = () => {
  Object.assign(filterForm, {
    taskId: '',
    trackingNumber: '',
    status: '',
    sortBy: 'created_desc'
  })
  pagination.page = 1
  fetchList()
}

// 处理上传新图片
const handleUploadNew = () => {
  router.push('/delivery/generate')
}

// 处理查看详情
const handleView = (row: any) => {
  currentTask.value = row
  dialogVisible.value = true
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

// 自动刷新任务状态
const startAutoRefresh = () => {
  refreshTimer = window.setInterval(() => {
    // 只有在有处理中的任务时才自动刷新
    const hasProcessingTasks = tableData.value.some((task: any) => 
      ['pending', 'recognizing', 'tracking', 'generating'].includes(task.status)
    )
    if (hasProcessingTasks) {
      fetchList()
    }
  }, 10000) // 每10秒刷新一次
}

const stopAutoRefresh = () => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
    refreshTimer = null
  }
}

// 组件挂载时获取数据并开始自动刷新
onMounted(() => {
  fetchList()
  startAutoRefresh()
})

// 组件卸载时停止自动刷新
onUnmounted(() => {
  stopAutoRefresh()
})
</script>

<style scoped>
.task-list {
  padding: 0;
}

.filter-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.filter-form {
  margin: 0;
}

.table-card {
  margin-bottom: 20px;
}

.pagination-container {
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
}

.progress-container {
  display: flex;
  align-items: center;
  gap: 10px;
}

.progress-text {
  font-size: 12px;
  color: #666;
  min-width: 30px;
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
  
  .progress-container {
    flex-direction: column;
    gap: 5px;
  }
  
  .progress-text {
    text-align: center;
  }
}
</style>