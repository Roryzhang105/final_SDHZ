<template>
  <div class="page-content upload-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>上传图片</span>
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
          <li>支持同时上传多张图片</li>
        </ul>
      </el-alert>
      
      <!-- 图片上传区域 -->
      <div class="upload-container">
        <el-upload
          ref="uploadRef"
          v-model:file-list="fileList"
          :action="uploadUrl"
          :headers="uploadHeaders"
          :on-preview="handlePreview"
          :on-remove="handleRemove"
          :on-success="handleUploadSuccess"
          :on-error="handleUploadError"
          :before-upload="beforeUpload"
          :on-progress="handleProgress"
          multiple
          accept="image/jpeg,image/jpg,image/png"
          list-type="picture-card"
          class="upload-area"
        >
          <div class="upload-content">
            <el-icon class="upload-icon"><Plus /></el-icon>
            <div class="upload-text">点击上传或拖拽文件到此处</div>
            <div class="upload-hint">支持 JPG、PNG 格式</div>
          </div>
        </el-upload>
      </div>
      
      <!-- 上传进度 -->
      <div v-if="uploading" class="upload-progress">
        <el-progress
          :percentage="uploadProgress"
          :show-text="true"
          :status="uploadProgress === 100 ? 'success' : undefined"
        />
        <p class="progress-text">
          {{ uploadProgress === 100 ? '上传完成，正在处理...' : '正在上传图片...' }}
        </p>
      </div>
      
      <!-- 操作按钮 -->
      <div class="action-buttons" v-if="fileList.length > 0">
        <el-button
          type="primary"
          size="large"
          :loading="uploading"
          :disabled="fileList.length === 0"
          @click="handleBatchUpload"
        >
          <el-icon><Upload /></el-icon>
          {{ uploading ? '上传中...' : `开始处理 (${fileList.length}张图片)` }}
        </el-button>
        
        <el-button
          size="large"
          @click="clearAll"
          :disabled="uploading"
        >
          <el-icon><Delete /></el-icon>
          清空所有
        </el-button>
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

const router = useRouter()
const authStore = useAuthStore()

// 上传相关状态
const uploadRef = ref()
const fileList = ref<UploadFiles>([])
const uploading = ref(false)
const uploadProgress = ref(0)

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
}

const uploadResults = ref<UploadResult[]>([])

// 上传配置
const uploadUrl = computed(() => {
  return `${import.meta.env.VITE_API_BASE_URL}/api/v1/upload/image`
})

const uploadHeaders = computed(() => {
  return {
    'Authorization': `Bearer ${authStore.token}`
  }
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

// 处理上传进度
const handleProgress: UploadProps['onProgress'] = (evt) => {
  uploadProgress.value = Math.round(evt.percent || 0)
}

// 处理上传成功
const handleUploadSuccess: UploadProps['onSuccess'] = (response, file) => {
  console.log('Upload success:', response, file)
  
  if (response.success) {
    uploadResults.value.push({
      id: file.uid || Date.now().toString(),
      imageUrl: file.url || '',
      success: true,
      taskId: response.data?.task_id,
      qrCode: response.data?.qr_code
    })
    ElMessage.success(`图片 ${file.name} 上传并处理成功!`)
  } else {
    uploadResults.value.push({
      id: file.uid || Date.now().toString(),
      imageUrl: file.url || '',
      success: false,
      error: response.message || '处理失败'
    })
    ElMessage.error(`图片 ${file.name} 处理失败: ${response.message}`)
  }
}

// 处理上传错误
const handleUploadError: UploadProps['onError'] = (error, file) => {
  console.error('Upload error:', error)
  uploadResults.value.push({
    id: file.uid || Date.now().toString(),
    imageUrl: file.url || '',
    success: false,
    error: '上传失败，请重试'
  })
  ElMessage.error(`图片 ${file.name} 上传失败，请重试`)
}

// 预览图片
const handlePreview: UploadProps['onPreview'] = (file) => {
  previewImageUrl.value = file.url || ''
  previewVisible.value = true
}

// 移除图片
const handleRemove: UploadProps['onRemove'] = (file) => {
  // 移除对应的结果
  uploadResults.value = uploadResults.value.filter(result => result.id !== file.uid)
  return true
}

// 批量上传处理
const handleBatchUpload = async () => {
  if (fileList.value.length === 0) {
    ElMessage.warning('请先选择要上传的图片')
    return
  }

  try {
    uploading.value = true
    uploadProgress.value = 0
    
    // 清空之前的结果
    uploadResults.value = []
    
    // 触发上传
    uploadRef.value?.submit()
    
  } catch (error) {
    console.error('Upload failed:', error)
    ElMessage.error('上传失败，请重试')
  } finally {
    uploading.value = false
  }
}

// 清空所有文件
const clearAll = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要清空所有文件吗？',
      '提示',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    uploadRef.value?.clearFiles()
    fileList.value = []
    uploadResults.value = []
    uploadProgress.value = 0
    
    ElMessage.success('已清空所有文件')
  } catch {
    // 用户取消
  }
}

// 跳转到任务列表
const goToTaskList = () => {
  router.push('/delivery/list')
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

.upload-container {
  margin: 20px 0;
}

.upload-area {
  width: 100%;
}

.upload-area :deep(.el-upload) {
  border: 2px dashed #d9d9d9;
  border-radius: 6px;
  cursor: pointer;
  position: relative;
  overflow: hidden;
  transition: all 0.3s;
  width: 100%;
  height: 200px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.upload-area :deep(.el-upload:hover) {
  border-color: #409eff;
}

.upload-content {
  text-align: center;
  color: #606266;
}

.upload-icon {
  font-size: 48px;
  color: #c0c4cc;
  margin-bottom: 16px;
}

.upload-text {
  font-size: 16px;
  margin-bottom: 8px;
}

.upload-hint {
  font-size: 14px;
  color: #909399;
}

.upload-progress {
  margin: 20px 0;
  text-align: center;
}

.progress-text {
  margin-top: 10px;
  color: #606266;
  font-size: 14px;
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

@media (max-width: 768px) {
  
  .upload-area :deep(.el-upload) {
    height: 150px;
  }
  
  .upload-icon {
    font-size: 36px;
  }
  
  .upload-text {
    font-size: 14px;
  }
  
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