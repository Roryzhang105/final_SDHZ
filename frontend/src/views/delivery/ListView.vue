<template>
  <div class="delivery-list">
    <el-card class="filter-card" shadow="hover">
      <template #header>
        <div class="card-header">
          <span>送达回证列表</span>
          <el-button type="primary" :icon="Plus" @click="handleGenerate">
            生成新回证
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
        <el-form-item label="状态">
          <el-select v-model="filterForm.status" placeholder="请选择状态" clearable>
            <el-option label="已生成" value="generated" />
            <el-option label="处理中" value="processing" />
            <el-option label="失败" value="failed" />
          </el-select>
        </el-form-item>
        <el-form-item label="日期范围">
          <el-date-picker
            v-model="filterForm.dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
          />
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
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="55" />
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="trackingNumber" label="快递单号" min-width="150" />
        <el-table-column prop="recipientName" label="收件人" min-width="100" />
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag 
              :type="getStatusType(row.status)"
              :class="`status-${getStatusType(row.status)}`"
            >
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="deliveryTime" label="送达时间" width="160" />
        <el-table-column prop="createdAt" label="创建时间" width="160" />
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button
              type="primary"
              size="small"
              :icon="View"
              @click="handleView(row)"
            >
              查看
            </el-button>
            <el-button
              type="success"
              size="small"
              :icon="Download"
              @click="handleDownload(row)"
            >
              下载
            </el-button>
            <el-button
              type="danger"
              size="small"
              :icon="Delete"
              @click="handleDelete(row)"
            >
              删除
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

    <!-- 查看详情对话框 -->
    <el-dialog
      v-model="dialogVisible"
      title="回证详情"
      width="80%"
      :before-close="handleCloseDialog"
    >
      <div v-if="currentRecord" class="detail-content">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="快递单号">
            {{ currentRecord.trackingNumber }}
          </el-descriptions-item>
          <el-descriptions-item label="收件人">
            {{ currentRecord.recipientName }}
          </el-descriptions-item>
          <el-descriptions-item label="收件人电话">
            {{ currentRecord.recipientPhone }}
          </el-descriptions-item>
          <el-descriptions-item label="收件地址">
            {{ currentRecord.recipientAddress }}
          </el-descriptions-item>
          <el-descriptions-item label="送达时间">
            {{ currentRecord.deliveryTime }}
          </el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="getStatusType(currentRecord.status)">
              {{ getStatusText(currentRecord.status) }}
            </el-tag>
          </el-descriptions-item>
        </el-descriptions>
        
        <!-- 如果有截图，显示截图 -->
        <div v-if="currentRecord.screenshotPath" class="screenshot-section">
          <h4>截图预览</h4>
          <el-image
            :src="currentRecord.screenshotPath"
            :preview-src-list="[currentRecord.screenshotPath]"
            fit="contain"
            style="width: 300px; height: 200px;"
          />
        </div>
      </div>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">关闭</el-button>
          <el-button type="primary" @click="handleDownload(currentRecord)">
            下载回证
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Plus,
  Search,
  Refresh,
  View,
  Download,
  Delete
} from '@element-plus/icons-vue'
import { deliveryApi } from '@/api/delivery'

const router = useRouter()

// 响应式数据
const loading = ref(false)
const dialogVisible = ref(false)
const tableData = ref([])
const currentRecord = ref(null)
const selectedRows = ref([])

// 筛选表单
const filterForm = reactive({
  trackingNumber: '',
  status: '',
  dateRange: []
})

// 分页配置
const pagination = reactive({
  page: 1,
  size: 20,
  total: 0
})

// 获取列表数据
const fetchList = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      size: pagination.size,
      tracking_number: filterForm.trackingNumber,
      status: filterForm.status,
      start_date: filterForm.dateRange?.[0],
      end_date: filterForm.dateRange?.[1]
    }
    
    const response = await deliveryApi.getList(params)
    tableData.value = response.data.items
    pagination.total = response.data.total
  } catch (error) {
    console.error('获取列表失败:', error)
    ElMessage.error('获取列表失败')
  } finally {
    loading.value = false
  }
}

// 状态类型映射
const getStatusType = (status: string) => {
  const statusMap = {
    generated: 'success',
    processing: 'warning',
    failed: 'danger'
  }
  return statusMap[status] || 'info'
}

// 状态文本映射
const getStatusText = (status: string) => {
  const statusMap = {
    generated: '已生成',
    processing: '处理中',
    failed: '失败'
  }
  return statusMap[status] || '未知'
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
    status: '',
    dateRange: []
  })
  pagination.page = 1
  fetchList()
}

// 处理生成新回证
const handleGenerate = () => {
  router.push('/delivery/generate')
}

// 处理查看详情
const handleView = (row: any) => {
  currentRecord.value = row
  dialogVisible.value = true
}

// 处理下载
const handleDownload = async (row: any) => {
  try {
    const response = await deliveryApi.download(row.id)
    
    // 创建下载链接
    const blob = new Blob([response.data], { 
      type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' 
    })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `送达回证_${row.trackingNumber}.docx`
    link.click()
    window.URL.revokeObjectURL(url)
    
    ElMessage.success('下载成功')
  } catch (error) {
    console.error('下载失败:', error)
    ElMessage.error('下载失败')
  }
}

// 处理删除
const handleDelete = async (row: any) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除快递单号为 ${row.trackingNumber} 的回证吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await deliveryApi.delete(row.id)
    ElMessage.success('删除成功')
    fetchList()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除失败:', error)
      ElMessage.error('删除失败')
    }
  }
}

// 处理选择变化
const handleSelectionChange = (selection: any[]) => {
  selectedRows.value = selection
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
  currentRecord.value = null
}

// 组件挂载时获取数据
onMounted(() => {
  fetchList()
})
</script>

<style scoped>
.delivery-list {
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

.detail-content {
  padding: 20px 0;
}

.screenshot-section {
  margin-top: 20px;
}

.screenshot-section h4 {
  margin-bottom: 10px;
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
</style>