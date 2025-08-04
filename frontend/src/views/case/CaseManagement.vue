<template>
  <div class="case-management">
    <!-- 页面标题和操作按钮 -->
    <div class="page-header">
      <div class="header-content">
        <h1 class="page-title">案件管理</h1>
        <div class="page-description">
          管理和查看所有案件信息，支持Excel批量导入
        </div>
      </div>
      <div class="header-actions">
        <el-button type="primary" @click="showImportDialog = true">
          <el-icon><Upload /></el-icon>
          导入Excel文件
        </el-button>
        <el-button @click="refreshData">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-cards">
      <div class="stats-card">
        <div class="stats-title">总案件数</div>
        <div class="stats-value">{{ stats.total_cases }}</div>
      </div>
      <div class="stats-card">
        <div class="stats-title">今年新增</div>
        <div class="stats-value">{{ stats.this_year_cases }}</div>
      </div>
      <div class="stats-card">
        <div class="stats-title">已结案</div>
        <div class="stats-value">{{ stats.closed_cases }}</div>
      </div>
      <div class="stats-card">
        <div class="stats-title">进行中</div>
        <div class="stats-value">{{ stats.active_cases }}</div>
      </div>
    </div>

    <!-- 搜索和筛选 -->
    <div class="search-bar">
      <div class="search-left">
        <el-input
          v-model="searchQuery"
          placeholder="输入案号、申请人、被申请人进行搜索..."
          clearable
          @keyup.enter="handleSearch"
          @clear="handleClearSearch"
          style="width: 400px"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        <el-button type="primary" @click="handleSearch" :loading="loading">
          搜索
        </el-button>
      </div>
      <div class="search-right">
        <el-select v-model="statusFilter" placeholder="状态筛选" @change="handleStatusFilter" clearable style="width: 120px">
          <el-option label="活跃" value="active" />
          <el-option label="非活跃" value="inactive" />
        </el-select>
      </div>
    </div>

    <!-- 案件列表表格 -->
    <div class="table-container">
      <el-table
        :data="caseList"
        v-loading="loading"
        stripe
        border
        style="width: 100%"
        :default-sort="{ prop: 'created_at', order: 'descending' }"
      >
        <el-table-column prop="case_number" label="案号" width="150" fixed="left">
          <template #default="{ row }">
            <el-link type="primary" @click="viewCaseDetail(row)">
              {{ row.case_number }}
            </el-link>
          </template>
        </el-table-column>
        
        <el-table-column prop="applicant" label="申请人" width="120" />
        
        <el-table-column prop="respondent" label="被申请人" width="150" />
        
        <el-table-column prop="third_party" label="第三人" width="120">
          <template #default="{ row }">
            {{ row.third_party || '-' }}
          </template>
        </el-table-column>
        
        <el-table-column prop="applicant_address" label="申请人地址" width="200" show-overflow-tooltip />
        
        <el-table-column prop="closure_date" label="结案日期" width="120">
          <template #default="{ row }">
            {{ row.closure_date ? formatDate(row.closure_date) : '-' }}
          </template>
        </el-table-column>
        
        <el-table-column prop="status" label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.status === 'active' ? 'success' : 'info'">
              {{ row.status === 'active' ? '活跃' : '非活跃' }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="created_at" label="创建时间" width="160">
          <template #default="{ row }">
            {{ formatDateTime(row.created_at) }}
          </template>
        </el-table-column>
        
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" size="small" @click="viewCaseDetail(row)">
              查看
            </el-button>
            <el-button type="warning" size="small" @click="editCase(row)">
              编辑
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 分页 -->
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

    <!-- Excel导入对话框 -->
    <el-dialog
      v-model="showImportDialog"
      title="导入Excel文件"
      width="600px"
      :close-on-click-modal="false"
    >
      <div class="import-dialog-content">
        <!-- 文件上传区域 -->
        <div class="upload-area" v-if="!importResult">
          <el-upload
            ref="uploadRef"
            class="upload-dragger"
            drag
            :auto-upload="false"
            :limit="1"
            :on-change="handleFileChange"
            :before-upload="beforeUpload"
            accept=".xlsx,.xls"
          >
            <el-icon class="el-icon--upload"><upload-filled /></el-icon>
            <div class="el-upload__text">
              将Excel文件拖到此处，或<em>点击上传</em>
            </div>
            <template #tip>
              <div class="el-upload__tip">
                只能上传 .xlsx/.xls 文件，文件大小不超过10MB
              </div>
            </template>
          </el-upload>
          
          <div v-if="selectedFile" class="selected-file">
            <el-icon><Document /></el-icon>
            <span>{{ selectedFile.name }}</span>
            <el-button type="text" @click="removeFile">
              <el-icon><Close /></el-icon>
            </el-button>
          </div>
        </div>

        <!-- 导入进度 -->
        <div v-if="importing" class="import-progress">
          <el-progress :percentage="importProgress" :status="importProgress === 100 ? 'success' : undefined" />
          <p>正在导入Excel文件，请稍候...</p>
        </div>

        <!-- 导入结果 -->
        <div v-if="importResult" class="import-result">
          <div class="result-header">
            <el-icon class="result-icon success"><CircleCheck /></el-icon>
            <h3>导入完成</h3>
          </div>
          
          <div class="result-stats">
            <div class="stat-item">
              <span class="stat-label">总行数：</span>
              <span class="stat-value">{{ importResult.total_rows }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">新增案件：</span>
              <span class="stat-value success">{{ importResult.imported }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">更新案件：</span>
              <span class="stat-value warning">{{ importResult.updated }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">错误数量：</span>
              <span class="stat-value danger">{{ importResult.errors.length }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">成功率：</span>
              <span class="stat-value">{{ importResult.success_rate }}%</span>
            </div>
          </div>

          <div v-if="importResult.errors.length > 0" class="error-list">
            <h4>错误详情：</h4>
            <div class="error-items">
              <div v-for="(error, index) in importResult.errors.slice(0, 10)" :key="index" class="error-item">
                {{ error }}
              </div>
              <div v-if="importResult.errors.length > 10" class="error-more">
                还有 {{ importResult.errors.length - 10 }} 个错误...
              </div>
            </div>
          </div>
        </div>
      </div>

      <template #footer>
        <div class="dialog-footer">
          <el-button v-if="!importResult" @click="closeImportDialog">取消</el-button>
          <el-button 
            v-if="!importResult && selectedFile" 
            type="primary" 
            @click="handleImport"
            :loading="importing"
          >
            开始导入
          </el-button>
          <el-button v-if="importResult" type="primary" @click="closeImportDialog">
            完成
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 案件详情对话框 -->
    <el-dialog
      v-model="showDetailDialog"
      title="案件详情"
      width="800px"
    >
      <div v-if="selectedCase" class="case-detail">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="案号">{{ selectedCase.case_number }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="selectedCase.status === 'active' ? 'success' : 'info'">
              {{ selectedCase.status === 'active' ? '活跃' : '非活跃' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="申请人">{{ selectedCase.applicant }}</el-descriptions-item>
          <el-descriptions-item label="被申请人">{{ selectedCase.respondent }}</el-descriptions-item>
          <el-descriptions-item label="第三人">{{ selectedCase.third_party || '-' }}</el-descriptions-item>
          <el-descriptions-item label="结案日期">{{ selectedCase.closure_date ? formatDate(selectedCase.closure_date) : '-' }}</el-descriptions-item>
          <el-descriptions-item label="申请人地址" span="2">{{ selectedCase.applicant_address }}</el-descriptions-item>
          <el-descriptions-item label="被申请人地址" span="2">{{ selectedCase.respondent_address }}</el-descriptions-item>
          <el-descriptions-item label="第三人地址" span="2">{{ selectedCase.third_party_address || '-' }}</el-descriptions-item>
          <el-descriptions-item label="创建时间">{{ formatDateTime(selectedCase.created_at) }}</el-descriptions-item>
          <el-descriptions-item label="更新时间">{{ formatDateTime(selectedCase.updated_at) }}</el-descriptions-item>
        </el-descriptions>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Upload,
  Refresh,
  Search,
  Document,
  Close,
  CircleCheck,
  UploadFilled
} from '@element-plus/icons-vue'
import {
  getCaseList,
  searchCases,
  importCases,
  getCaseStats
} from '@/api/case'
import type {
  CaseInfo,
  CaseImportResult,
  CaseListParams,
  CaseSearchParams
} from '@/api/case'

// 响应式数据
const loading = ref(false)
const caseList = ref<CaseInfo[]>([])
const searchQuery = ref('')
const statusFilter = ref('')
const isSearchMode = ref(false)

// 分页
const pagination = ref({
  page: 1,
  size: 20,
  total: 0
})

// 统计数据
const stats = ref({
  total_cases: 0,
  this_year_cases: 0,
  closed_cases: 0,
  active_cases: 0
})

// 导入相关
const showImportDialog = ref(false)
const selectedFile = ref<File | null>(null)
const importing = ref(false)
const importProgress = ref(0)
const importResult = ref<CaseImportResult | null>(null)

// 案件详情
const showDetailDialog = ref(false)
const selectedCase = ref<CaseInfo | null>(null)

// 生命周期钩子
onMounted(() => {
  loadCaseList()
  loadStats()
})

// 加载案件列表
const loadCaseList = async () => {
  try {
    loading.value = true
    
    let response
    if (isSearchMode.value && searchQuery.value) {
      const params: CaseSearchParams = {
        q: searchQuery.value,
        page: pagination.value.page,
        size: pagination.value.size
      }
      response = await searchCases(params)
    } else {
      const params: CaseListParams = {
        page: pagination.value.page,
        size: pagination.value.size,
        ...(statusFilter.value && { status: statusFilter.value })
      }
      response = await getCaseList(params)
    }
    
    if (response.success) {
      caseList.value = response.data.cases
      pagination.value = {
        ...pagination.value,
        total: response.data.pagination.total,
        page: response.data.pagination.page
      }
    }
  } catch (error) {
    console.error('加载案件列表失败:', error)
    ElMessage.error('加载案件列表失败')
  } finally {
    loading.value = false
  }
}

// 加载统计数据
const loadStats = async () => {
  try {
    const response = await getCaseStats()
    if (response.success) {
      stats.value = response.data
    }
  } catch (error) {
    console.error('加载统计数据失败:', error)
  }
}

// 搜索处理
const handleSearch = () => {
  if (searchQuery.value.trim()) {
    isSearchMode.value = true
    pagination.value.page = 1
    loadCaseList()
  } else {
    handleClearSearch()
  }
}

// 清除搜索
const handleClearSearch = () => {
  searchQuery.value = ''
  isSearchMode.value = false
  pagination.value.page = 1
  loadCaseList()
}

// 状态筛选
const handleStatusFilter = () => {
  pagination.value.page = 1
  isSearchMode.value = false
  loadCaseList()
}

// 分页处理
const handleSizeChange = (size: number) => {
  pagination.value.size = size
  pagination.value.page = 1
  loadCaseList()
}

const handleCurrentChange = (page: number) => {
  pagination.value.page = page
  loadCaseList()
}

// 刷新数据
const refreshData = () => {
  loadCaseList()
  loadStats()
}

// 文件上传处理
const handleFileChange = (file: any) => {
  selectedFile.value = file.raw
}

const beforeUpload = (file: File) => {
  const isExcel = file.type === 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' || 
                  file.type === 'application/vnd.ms-excel'
  const isLt10M = file.size / 1024 / 1024 < 10

  if (!isExcel) {
    ElMessage.error('只能上传Excel文件!')
    return false
  }
  if (!isLt10M) {
    ElMessage.error('文件大小不能超过10MB!')
    return false
  }
  return false // 阻止自动上传
}

const removeFile = () => {
  selectedFile.value = null
}

// Excel导入
const handleImport = async () => {
  if (!selectedFile.value) {
    ElMessage.warning('请选择要导入的Excel文件')
    return
  }

  try {
    importing.value = true
    importProgress.value = 0
    
    // 模拟进度更新
    const progressInterval = setInterval(() => {
      if (importProgress.value < 90) {
        importProgress.value += Math.random() * 20
      }
    }, 500)

    const response = await importCases(selectedFile.value)
    
    clearInterval(progressInterval)
    importProgress.value = 100
    
    if (response.success) {
      importResult.value = response.data
      ElMessage.success('Excel导入完成')
      // 刷新数据
      await refreshData()
    }
    
  } catch (error) {
    console.error('导入失败:', error)
    ElMessage.error('Excel导入失败')
  } finally {
    importing.value = false
  }
}

// 关闭导入对话框
const closeImportDialog = () => {
  showImportDialog.value = false
  selectedFile.value = null
  importing.value = false
  importProgress.value = 0
  importResult.value = null
}

// 查看案件详情
const viewCaseDetail = (case_info: CaseInfo) => {
  selectedCase.value = case_info
  showDetailDialog.value = true
}

// 编辑案件
const editCase = (case_info: CaseInfo) => {
  ElMessage.info('编辑功能暂未实现')
}

// 工具函数
const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleDateString('zh-CN')
}

const formatDateTime = (dateString: string) => {
  return new Date(dateString).toLocaleString('zh-CN')
}
</script>

<style scoped>
.case-management {
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

.header-actions {
  display: flex;
  gap: 12px;
}

.stats-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}

.stats-card {
  background: white;
  padding: 24px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  text-align: center;
}

.stats-title {
  font-size: 14px;
  color: #7f8c8d;
  margin-bottom: 8px;
}

.stats-value {
  font-size: 32px;
  font-weight: 600;
  color: #2c3e50;
}

.search-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  background: white;
  padding: 16px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.search-left {
  display: flex;
  gap: 12px;
  align-items: center;
}

.table-container {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  overflow: hidden;
}

.pagination-container {
  display: flex;
  justify-content: center;
  margin-top: 24px;
}

.import-dialog-content {
  min-height: 200px;
}

.upload-area {
  margin-bottom: 16px;
}

.selected-file {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 16px;
  padding: 8px;
  background: #f8f9fa;
  border-radius: 4px;
}

.import-progress {
  text-align: center;
  padding: 40px 20px;
}

.import-result {
  padding: 20px;
}

.result-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 24px;
}

.result-icon {
  font-size: 24px;
}

.result-icon.success {
  color: #67c23a;
}

.result-stats {
  display: grid;
  gap: 12px;
  margin-bottom: 24px;
}

.stat-item {
  display: flex;
  justify-content: space-between;
  padding: 8px 0;
  border-bottom: 1px solid #eee;
}

.stat-label {
  color: #666;
}

.stat-value {
  font-weight: 600;
}

.stat-value.success {
  color: #67c23a;
}

.stat-value.warning {
  color: #e6a23c;
}

.stat-value.danger {
  color: #f56c6c;
}

.error-list {
  background: #fff2f0;
  padding: 16px;
  border-radius: 4px;
  border-left: 4px solid #f56c6c;
}

.error-list h4 {
  margin: 0 0 12px 0;
  color: #f56c6c;
}

.error-items {
  max-height: 200px;
  overflow-y: auto;
}

.error-item {
  padding: 4px 0;
  font-size: 14px;
  color: #666;
  border-bottom: 1px solid #ffe4e1;
}

.error-more {
  padding: 8px 0;
  text-align: center;
  color: #999;
  font-style: italic;
}

.case-detail {
  padding: 16px;
}
</style>