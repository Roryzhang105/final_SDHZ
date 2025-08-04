<template>
  <div class="page-content upload-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>批量上传图片</span>
        </div>
      </template>
      
      <!-- 上传说明 -->
      <el-alert
        title="上传说明"
        type="info"
        :closable="false"
        show-icon
        class="upload-tips"
      >
        <ul>
          <li>支持的图片格式：JPG、PNG</li>
          <li>图片中需要包含清晰的二维码</li>
          <li>系统将自动识别二维码并创建处理任务</li>
          <li>一次上传多张图片（最多20张）并并行处理</li>
        </ul>
      </el-alert>
      
      <!-- 批量上传区域 -->
      <div class="upload-container">
        <div class="batch-upload-area">
          <el-upload
            ref="batchUploadRef"
            v-model:file-list="batchFileList"
            :auto-upload="false"
            :on-preview="handlePreview"
            :on-remove="handleBatchRemove"
            :before-upload="beforeUpload"
            :on-change="handleBatchFileChange"
            name="files"
            multiple
            accept="image/jpeg,image/jpg,image/png"
            list-type="picture-card"
            class="batch-upload"
            drag
          >
            <div class="batch-upload-content">
              <el-icon class="upload-icon"><Plus /></el-icon>
              <div class="upload-text">批量上传图片</div>
              <div class="upload-hint">点击或拖拽多张图片到此处</div>
              <div class="upload-limit">最多支持20张图片</div>
            </div>
          </el-upload>
          
          <!-- 批量上传控制按钮 -->
          <div v-if="batchFileList.length > 0" class="batch-controls">
            <div class="batch-info">
              <span>已选择 {{ batchFileList.length }} 张图片</span>
              <span v-if="batchFileList.length > 20" class="error-text">（超出限制，最多20张）</span>
            </div>
            <div class="batch-actions">
              <el-button @click="clearBatchFiles">清空</el-button>
              <el-button 
                type="primary" 
                :loading="batchUploading"
                :disabled="batchFileList.length === 0 || batchFileList.length > 20"
                @click="handleBatchUpload"
              >
                <el-icon><Upload /></el-icon>
                开始批量上传
              </el-button>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 批量上传进度 -->
      <div v-if="batchUploading" class="batch-progress">
        <div class="batch-overall-progress">
          <h4>批量上传进度</h4>
          <el-progress
            :percentage="batchOverallProgress"
            :show-text="true"
            :status="batchOverallProgress === 100 ? 'success' : undefined"
          />
          <p class="progress-text">
            已完成 {{ batchCompletedCount }}/{{ batchTotalCount }} 个文件
          </p>
        </div>
        
        <!-- 每个文件的详细进度 -->
        <div class="batch-file-progress">
          <div 
            v-for="(progress, index) in batchFileProgress" 
            :key="index"
            class="file-progress-item"
          >
            <div class="file-info">
              <span class="file-name">{{ progress.name }}</span>
              <el-tag 
                :type="progress.status === 'success' ? 'success' : progress.status === 'error' ? 'danger' : 'info'"
                size="small"
              >
                {{ getProgressStatusText(progress.status) }}
              </el-tag>
            </div>
            <el-progress
              :percentage="progress.percentage"
              :show-text="false"
              :status="progress.status === 'success' ? 'success' : progress.status === 'error' ? 'exception' : undefined"
              :stroke-width="8"
            />
            <p v-if="progress.error" class="error-text">{{ progress.error }}</p>
          </div>
        </div>
      </div>
      
    </el-card>
    
    <!-- 上传结果 -->
    <el-card v-if="uploadResults.length > 0" style="margin-top: 20px;">
      <template #header>
        <div class="card-header">
          <span>处理结果</span>
          <el-button
            type="primary"
            @click="goToTaskList"
          >
            查看任务列表
          </el-button>
        </div>
      </template>
      
      <div class="results-list">
        <el-card
          v-for="result in uploadResults"
          :key="result.id"
          class="result-item"
          shadow="hover"
        >
          <div class="result-content">
            <div class="result-image">
              <el-image
                :src="result.imageUrl"
                fit="cover"
                style="width: 80px; height: 80px;"
              >
                <template #error>
                  <div class="image-slot">
                    <el-icon><Picture /></el-icon>
                  </div>
                </template>
              </el-image>
            </div>
            
            <div class="result-info">
              <div class="result-status">
                <el-tag
                  :type="result.success ? 'success' : 'danger'"
                  size="large"
                >
                  {{ result.success ? '处理成功' : '处理失败' }}
                </el-tag>
              </div>
              
              <div class="result-details">
                <p v-if="result.success">
                  <strong>任务ID:</strong> {{ result.taskId }}
                </p>
                <p v-if="result.success && result.qrCode">
                  <strong>识别到的二维码:</strong> {{ result.qrCode }}
                </p>
                <p v-if="!result.success" class="error-message">
                  <strong>错误:</strong> {{ result.error }}
                </p>
              </div>
            </div>
          </div>
        </el-card>
      </div>
    </el-card>
    
    <!-- 图片预览对话框 -->
    <el-dialog
      v-model="previewVisible"
      title="图片预览"
      width="60%"
      center
    >
      <img
        :src="previewImageUrl"
        style="width: 100%; height: auto;"
        alt="预览图片"
      />
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Plus,
  Upload,
  Delete,
  Picture
} from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'
import type { UploadFile, UploadFiles, UploadProps, UploadRawFile } from 'element-plus'
import axios from 'axios'

const router = useRouter()
const authStore = useAuthStore()

// 批量上传模式（移除了单张上传模式）


// 批量上传相关状态
const batchUploadRef = ref()
const batchFileList = ref<UploadFiles>([])
const batchUploading = ref(false)
const batchFileProgress = ref<Array<{
  name: string
  percentage: number
  status: 'pending' | 'uploading' | 'success' | 'error'
  error?: string
}>>([])

// 预览相关
const previewVisible = ref(false)
const previewImageUrl = ref('')

// 上传结果
interface UploadResult {
  id: string
  imageUrl: string
  success: boolean
  taskId?: string
  qrCode?: string
  error?: string
  filename?: string
}

const uploadResults = ref<UploadResult[]>([])

// 批量上传计算属性
const batchTotalCount = computed(() => batchFileProgress.value.length)
const batchCompletedCount = computed(() => 
  batchFileProgress.value.filter(p => p.status === 'success' || p.status === 'error').length
)
const batchOverallProgress = computed(() => {
  if (batchTotalCount.value === 0) return 0
  return Math.round((batchCompletedCount.value / batchTotalCount.value) * 100)
})


// 上传前检查
const beforeUpload: UploadProps['beforeUpload'] = (rawFile: UploadRawFile) => {
  const isImage = rawFile.type === 'image/jpeg' || rawFile.type === 'image/png'
  const isLt10M = rawFile.size / 1024 / 1024 < 10

  if (!isImage) {
    ElMessage.error('只能上传 JPG/PNG 格式的图片!')
    return false
  }
  if (!isLt10M) {
    ElMessage.error('图片大小不能超过 10MB!')
    return false
  }
  return true
}


// 预览图片
const handlePreview: UploadProps['onPreview'] = (file) => {
  previewImageUrl.value = file.url || ''
  previewVisible.value = true
}



// 批量上传相关方法
const handleBatchFileChange = (file: UploadFile, files: UploadFiles) => {
  if (files.length > 20) {
    ElMessage.warning('最多只能选择20张图片')
    // 移除超出的文件
    batchFileList.value = files.slice(0, 20)
    return
  }
  batchFileList.value = files
}

const handleBatchRemove = (file: UploadFile, files: UploadFiles) => {
  batchFileList.value = files
  return true
}

const clearBatchFiles = () => {
  batchFileList.value = []
  batchFileProgress.value = []
  uploadResults.value = []
}

const handleBatchUpload = async () => {
  if (batchFileList.value.length === 0) {
    ElMessage.warning('请先选择要上传的图片')
    return
  }

  if (batchFileList.value.length > 20) {
    ElMessage.error('最多支持20张图片')
    return
  }

  batchUploading.value = true
  uploadResults.value = []
  
  // 初始化进度跟踪
  batchFileProgress.value = batchFileList.value.map(file => ({
    name: file.name || 'unknown',
    percentage: 0,
    status: 'pending' as const
  }))

  try {
    // 创建FormData
    const formData = new FormData()
    let validFileCount = 0
    
    batchFileList.value.forEach((file, index) => {
      if (file.raw) {
        formData.append('files', file.raw)
        validFileCount++
      } else {
        console.warn(`文件 ${file.name} 没有raw属性，跳过上传`)
        // 标记该文件进度为错误
        if (batchFileProgress.value[index]) {
          batchFileProgress.value[index].status = 'error'
          batchFileProgress.value[index].error = '文件数据无效'
        }
      }
    })
    
    // 检查是否有有效文件
    if (validFileCount === 0) {
      throw new Error('没有有效的文件可以上传')
    }

    const response = await axios.post(
      `${import.meta.env.VITE_API_BASE_URL}/api/v1/tasks/batch-upload`,
      formData,
      {
        headers: {
          'Authorization': `Bearer ${authStore.token}`
          // 不手动设置 Content-Type，让浏览器自动设置包含boundary的multipart/form-data
        },
        onUploadProgress: (progressEvent) => {
          if (progressEvent.total) {
            const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total)
            // 为所有文件设置上传进度
            batchFileProgress.value.forEach(progress => {
              if (progress.status === 'pending') {
                progress.status = 'uploading'
                progress.percentage = percentCompleted
              }
            })
          }
        }
      }
    )

    if (response.data.success) {
      // 处理批量上传结果
      const results = response.data.tasks || []
      const validationErrors = response.data.validation_errors || []
      
      // 更新进度状态
      batchFileProgress.value.forEach((progress, index) => {
        const result = results.find((r: any) => r.index === index)
        const validationError = validationErrors.find((e: any) => e.index === index)
        
        if (validationError) {
          progress.status = 'error'
          progress.percentage = 0
          progress.error = validationError.error
        } else if (result) {
          progress.status = result.success ? 'success' : 'error'
          progress.percentage = result.success ? 100 : 0
          if (!result.success) {
            progress.error = result.message
          }
        } else {
          progress.status = 'error'
          progress.percentage = 0
          progress.error = '未知错误'
        }
      })

      // 生成上传结果用于显示
      uploadResults.value = []
      
      // 处理验证错误
      validationErrors.forEach((error: any) => {
        uploadResults.value.push({
          id: `error_${error.index}`,
          imageUrl: '',
          success: false,
          error: error.error,
          filename: error.filename
        })
      })

      // 处理任务创建结果
      results.forEach((result: any) => {
        uploadResults.value.push({
          id: result.data?.task_id || `result_${result.index}`,
          imageUrl: result.data?.image_url || '',
          success: result.success,
          taskId: result.data?.task_id,
          error: result.success ? undefined : result.message,
          filename: result.filename
        })
      })

      ElMessage.success(response.data.message)
      
      if (response.data.batch_id) {
        console.log('批量任务批次ID:', response.data.batch_id)
        // 可以在这里启动批量状态监控
      }
      
    } else {
      throw new Error(response.data.message || '批量上传失败')
    }

  } catch (error: any) {
    console.error('批量上传失败:', error)
    
    // 将所有进度标记为错误
    batchFileProgress.value.forEach(progress => {
      progress.status = 'error'
      progress.percentage = 0
      progress.error = error.response?.data?.detail || error.message || '上传失败'
    })
    
    ElMessage.error('批量上传失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    batchUploading.value = false
  }
}

const getProgressStatusText = (status: string) => {
  const statusMap = {
    pending: '等待中',
    uploading: '上传中',
    success: '成功',
    error: '失败'
  }
  return statusMap[status as keyof typeof statusMap] || status
}

// 跳转到任务列表
const goToTaskList = () => {
  router.push('/app/delivery/list')
}
</script>

<style scoped>
.upload-page {
  /* padding已通过page-content类提供 */
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}


.upload-tips {
  margin-bottom: 20px;
}

.upload-tips ul {
  margin: 0;
  padding-left: 20px;
}

.upload-tips li {
  margin: 5px 0;
  color: #606266;
}

.upload-tip {
  margin: 15px 0;
}

.upload-container {
  margin: 20px 0;
}


.action-buttons {
  display: flex;
  justify-content: center;
  gap: 15px;
  margin-top: 20px;
}

.results-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
  gap: 15px;
}

.result-item {
  border-radius: 8px;
}

.result-content {
  display: flex;
  align-items: flex-start;
  gap: 15px;
}

.result-image {
  flex-shrink: 0;
}

.image-slot {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 80px;
  height: 80px;
  background-color: #f5f7fa;
  color: #909399;
  font-size: 24px;
}

.result-info {
  flex: 1;
}

.result-status {
  margin-bottom: 10px;
}

.result-details p {
  margin: 5px 0;
  font-size: 14px;
  color: #606266;
}

.error-message {
  color: #f56c6c !important;
}

/* 批量上传样式 */
.batch-upload-area {
  position: relative;
}

.batch-upload :deep(.el-upload-dragger) {
  width: 100%;
  height: 200px;
  border: 2px dashed #d9d9d9;
  border-radius: 6px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.batch-upload :deep(.el-upload-dragger:hover) {
  border-color: #409eff;
}

.batch-upload :deep(.el-upload-dragger.is-dragover) {
  border-color: #409eff;
  background-color: rgba(64, 158, 255, 0.05);
}

.batch-upload-content {
  text-align: center;
  color: #606266;
}

.upload-limit {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

.batch-controls {
  margin-top: 20px;
  padding: 20px;
  background-color: #f8f9fa;
  border-radius: 6px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.batch-info {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 14px;
  color: #606266;
}

.batch-actions {
  display: flex;
  gap: 10px;
}

.batch-progress {
  margin: 20px 0;
  padding: 20px;
  background-color: #f8f9fa;
  border-radius: 6px;
}

.batch-overall-progress {
  margin-bottom: 20px;
}

.batch-overall-progress h4 {
  margin: 0 0 15px 0;
  color: #333;
  font-size: 16px;
}

.batch-file-progress {
  max-height: 300px;
  overflow-y: auto;
}

.file-progress-item {
  margin-bottom: 15px;
  padding: 12px;
  background-color: white;
  border-radius: 4px;
  border: 1px solid #e4e7ed;
}

.file-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.file-name {
  font-size: 14px;
  color: #606266;
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  margin-right: 10px;
}

.error-text {
  color: #f56c6c;
  font-size: 12px;
  margin: 5px 0 0 0;
}

@media (max-width: 768px) {
  
  
  .action-buttons {
    flex-direction: column;
    align-items: center;
  }
  
  .action-buttons .el-button {
    width: 100%;
    max-width: 300px;
  }
  
  .results-list {
    grid-template-columns: 1fr;
  }
  
  .result-content {
    flex-direction: column;
    align-items: center;
    text-align: center;
  }
}
</style>