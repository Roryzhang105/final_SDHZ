<template>
  <div class="page-content-full upload-page">

    <el-card class="main-card hover-lift">
      <template #header>
        <div class="card-header">
          <div class="header-content">
            <span class="header-title">批量上传图片</span>
            <div class="header-stats">
              <span class="stat-item">
                <el-icon><Picture /></el-icon>
                已选择 {{ batchFileList.length }} 张
              </span>
              <span class="stat-item" v-if="batchFileList.length > 0">
                <el-icon><Document /></el-icon>
                限制 20 张
              </span>
            </div>
          </div>
        </div>
      </template>
      
      <!-- 上传说明 -->
      <div class="upload-tips animate-on-scroll animate-fade-in-up">
        <div class="tips-header">
          <el-icon class="tips-icon"><InfoFilled /></el-icon>
          <h3>上传说明</h3>
        </div>
        <div class="tips-grid">
          <div class="tip-item">
            <el-icon class="tip-icon"><Picture /></el-icon>
            <div class="tip-content">
              <h4>支持格式</h4>
              <p>JPG、PNG 格式图片</p>
            </div>
          </div>
          <div class="tip-item">
            <el-icon class="tip-icon"><View /></el-icon>
            <div class="tip-content">
              <h4>图片要求</h4>
              <p>包含清晰的二维码</p>
            </div>
          </div>
          <div class="tip-item">
            <el-icon class="tip-icon"><Setting /></el-icon>
            <div class="tip-content">
              <h4>自动处理</h4>
              <p>识别二维码并创建任务</p>
            </div>
          </div>
          <div class="tip-item">
            <el-icon class="tip-icon"><Files /></el-icon>
            <div class="tip-content">
              <h4>批量上传</h4>
              <p>最多支持 20 张图片</p>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 批量上传区域 -->
      <div class="upload-container animate-on-scroll animate-fade-in-up">
        <div class="upload-section-title">
          <el-icon><UploadFilled /></el-icon>
          <span>拖拽上传区域</span>
        </div>
        
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
            class="batch-upload modern-upload"
            drag
          >
            <div class="batch-upload-content">
              <div class="upload-animation">
                <el-icon class="upload-icon pulse"><UploadFilled /></el-icon>
              </div>
              <div class="upload-text">批量上传图片</div>
              <div class="upload-hint">点击或拖拽多张图片到此处</div>
              <div class="upload-features">
                <span class="feature-tag">
                  <el-icon><Picture /></el-icon>
                  JPG/PNG
                </span>
                <span class="feature-tag">
                  <el-icon><Files /></el-icon>
                  最多20张
                </span>
                <span class="feature-tag">
                  <el-icon><Document /></el-icon>
                  &lt;10MB
                </span>
              </div>
            </div>
          </el-upload>
          
          <!-- 批量上传控制按钮 -->
          <transition name="slide-up" appear>
            <div v-if="batchFileList.length > 0" class="batch-controls modern-controls">
              <div class="controls-content">
                <div class="batch-info">
                  <div class="info-stats">
                    <div class="stat-card">
                      <el-icon class="stat-icon"><Picture /></el-icon>
                      <div class="stat-details">
                        <span class="stat-number">{{ batchFileList.length }}</span>
                        <span class="stat-label">张图片</span>
                      </div>
                    </div>
                    <div class="stat-card" v-if="batchFileList.length > 0">
                      <el-icon class="stat-icon" :class="batchFileList.length > 20 ? 'text-danger' : 'text-success'">
                        <CircleCheck v-if="batchFileList.length <= 20" />
                        <Warning v-else />
                      </el-icon>
                      <div class="stat-details">
                        <span class="stat-number" :class="batchFileList.length > 20 ? 'text-danger' : 'text-success'">
                          {{ batchFileList.length }}/20
                        </span>
                        <span class="stat-label">容量</span>
                      </div>
                    </div>
                  </div>
                  <div v-if="batchFileList.length > 20" class="error-warning">
                    <el-icon><Warning /></el-icon>
                    <span>超出限制，最多支持20张图片</span>
                  </div>
                </div>
                
                <div class="batch-actions">
                  <button class="btn btn-ghost" @click="clearBatchFiles">
                    <el-icon><Delete /></el-icon>
                    清空文件
                  </button>
                  <button 
                    class="btn btn-primary btn-lg"
                    :class="{ 'btn-loading': batchUploading }"
                    :disabled="batchFileList.length === 0 || batchFileList.length > 20"
                    @click="handleBatchUpload"
                  >
                    <div v-if="batchUploading" class="loading-content">
                      <div class="loading-spinner"></div>
                      <span>处理中...</span>
                    </div>
                    <div v-else class="button-content">
                      <el-icon><Upload /></el-icon>
                      <span>开始批量上传</span>
                    </div>
                  </button>
                </div>
              </div>
            </div>
          </transition>
        </div>
      </div>
      
      <!-- 批量上传进度 -->
      <transition name="slide-down" appear>
        <div v-if="batchUploading" class="batch-progress modern-progress animate-on-scroll animate-fade-in-up">
          <div class="progress-header">
            <div class="progress-title">
              <el-icon class="rotate"><Loading /></el-icon>
              <h3>批量处理进度</h3>
            </div>
            <div class="progress-stats">
              <span class="progress-fraction">{{ batchCompletedCount }}/{{ batchTotalCount }}</span>
              <span class="progress-label">个文件</span>
            </div>
          </div>
          
          <div class="overall-progress-card">
            <div class="progress-ring-container">
              <div class="progress-ring">
                <div class="progress-circle" :style="{ '--progress': batchOverallProgress }">
                  <span class="progress-percentage">{{ batchOverallProgress }}%</span>
                </div>
              </div>
            </div>
            
            <div class="progress-info">
              <div class="progress-bar-wrapper">
                <div class="progress-bar-modern">
                  <div 
                    class="progress-fill" 
                    :style="{ width: batchOverallProgress + '%' }"
                    :class="{ 'progress-complete': batchOverallProgress === 100 }"
                  ></div>
                </div>
              </div>
              
              <div class="progress-details">
                <span class="detail-item">
                  <el-icon><CircleCheck /></el-icon>
                  成功: {{ batchFileProgress.filter(p => p.status === 'success').length }}
                </span>
                <span class="detail-item">
                  <el-icon><Loading /></el-icon>
                  处理中: {{ batchFileProgress.filter(p => p.status === 'uploading').length }}
                </span>
                <span class="detail-item" v-if="batchFileProgress.filter(p => p.status === 'error').length > 0">
                  <el-icon><CircleClose /></el-icon>
                  失败: {{ batchFileProgress.filter(p => p.status === 'error').length }}
                </span>
              </div>
            </div>
          </div>
        
          <!-- 每个文件的详细进度 -->
          <div class="file-progress-section">
            <h4 class="section-subtitle">
              <el-icon><Document /></el-icon>
              文件处理详情
            </h4>
            
            <div class="file-progress-list">
              <transition-group name="list" appear>
                <div 
                  v-for="(progress, index) in batchFileProgress" 
                  :key="index"
                  class="file-progress-card"
                >
                  <div class="file-header">
                    <div class="file-info">
                      <el-icon class="file-icon">
                        <Picture v-if="progress.status === 'success'" />
                        <Loading v-else-if="progress.status === 'uploading'" class="rotate" />
                        <Warning v-else-if="progress.status === 'error'" />
                        <Document v-else />
                      </el-icon>
                      <div class="file-details">
                        <span class="file-name">{{ progress.name }}</span>
                        <span class="file-size">{{ getFileSizeText(progress.name) }}</span>
                      </div>
                    </div>
                    
                    <div class="file-status">
                      <span 
                        class="status-badge"
                        :class="`status-${progress.status}`"
                      >
                        {{ getProgressStatusText(progress.status) }}
                      </span>
                      <span class="status-percentage">{{ progress.percentage }}%</span>
                    </div>
                  </div>
                  
                  <div class="file-progress-bar">
                    <div class="progress-track">
                      <div 
                        class="progress-thumb" 
                        :class="`progress-${progress.status}`"
                        :style="{ width: progress.percentage + '%' }"
                      ></div>
                    </div>
                  </div>
                  
                  <div v-if="progress.error" class="file-error">
                    <el-icon><Warning /></el-icon>
                    <span>{{ progress.error }}</span>
                  </div>
                </div>
              </transition-group>
            </div>
          </div>
        </div>
      </transition>
      
    </el-card>
    
    <!-- 上传结果 -->
    <transition name="slide-up" appear>
      <div v-if="uploadResults.length > 0" class="results-section animate-on-scroll animate-fade-in-up">
        <el-card class="results-card hover-lift">
          <template #header>
            <div class="results-header">
              <div class="header-content">
                <div class="header-title">
                  <el-icon><DocumentChecked /></el-icon>
                  <span>处理结果</span>
                </div>
                <div class="header-summary">
                  <span class="summary-item success">
                    <el-icon><CircleCheck /></el-icon>
                    成功: {{ uploadResults.filter(r => r.success).length }}
                  </span>
                  <span class="summary-item error" v-if="uploadResults.filter(r => !r.success).length > 0">
                    <el-icon><CircleClose /></el-icon>
                    失败: {{ uploadResults.filter(r => !r.success).length }}
                  </span>
                </div>
              </div>
              <button class="btn btn-primary" @click="goToTaskList">
                <el-icon><List /></el-icon>
                查看任务列表
              </button>
            </div>
          </template>
          
          <div class="results-grid">
            <transition-group name="list" appear>
              <div
                v-for="result in uploadResults"
                :key="result.id"
                class="result-card hover-lift"
                :class="{ 'result-success': result.success, 'result-error': !result.success }"
              >
                <div class="result-header">
                  <div class="result-image">
                    <el-image
                      :src="result.imageUrl"
                      fit="cover"
                      class="image-preview"
                    >
                      <template #error>
                        <div class="image-placeholder">
                          <el-icon><Picture /></el-icon>
                        </div>
                      </template>
                    </el-image>
                  </div>
                  
                  <div class="result-status">
                    <div class="status-indicator" :class="result.success ? 'status-success' : 'status-error'">
                      <el-icon>
                        <CircleCheck v-if="result.success" />
                        <CircleClose v-else />
                      </el-icon>
                      <span>{{ result.success ? '处理成功' : '处理失败' }}</span>
                    </div>
                  </div>
                </div>
                
                <div class="result-body">
                  <div class="result-details">
                    <div v-if="result.success" class="success-details">
                      <div class="detail-item">
                        <el-icon><Key /></el-icon>
                        <div class="detail-content">
                          <span class="detail-label">任务ID</span>
                          <span class="detail-value">{{ result.taskId }}</span>
                        </div>
                      </div>
                      
                      <div v-if="result.qrCode" class="detail-item">
                        <el-icon><Cellphone /></el-icon>
                        <div class="detail-content">
                          <span class="detail-label">识别结果</span>
                          <span class="detail-value qr-code">{{ result.qrCode }}</span>
                        </div>
                      </div>
                      
                      <div class="detail-item">
                        <el-icon><Document /></el-icon>
                        <div class="detail-content">
                          <span class="detail-label">文件名</span>
                          <span class="detail-value">{{ result.filename || '未知' }}</span>
                        </div>
                      </div>
                    </div>
                    
                    <div v-else class="error-details">
                      <div class="error-message">
                        <el-icon><Warning /></el-icon>
                        <div class="error-content">
                          <span class="error-label">错误原因</span>
                          <span class="error-text">{{ result.error }}</span>
                        </div>
                      </div>
                      
                      <div v-if="result.filename" class="detail-item">
                        <el-icon><Document /></el-icon>
                        <div class="detail-content">
                          <span class="detail-label">文件名</span>
                          <span class="detail-value">{{ result.filename }}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </transition-group>
          </div>
        </el-card>
      </div>
    </transition>
    
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
  UploadFilled,
  Delete,
  Picture,
  InfoFilled,
  View,
  Setting,
  Files,
  Document,
  Warning,
  CircleCheck,
  CircleClose,
  Loading,
  DocumentChecked,
  List,
  Key,
  Cellphone
} from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'
import { useScrollAnimation } from '@/composables/useScrollAnimation'
import type { UploadFile, UploadFiles, UploadProps, UploadRawFile } from 'element-plus'
import axios from 'axios'

const router = useRouter()
const authStore = useAuthStore()

// 初始化滚动动画
const { refreshElements, showAllElements } = useScrollAnimation({
  threshold: 0.1,
  rootMargin: '0px 0px -50px 0px',
  once: true
})

// 确保页面加载后所有元素都可见（备用方案）
// 这解决了用户看到"大框框，元素被遮住"的问题
setTimeout(() => {
  showAllElements()
}, 200)

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
      
      // 刷新滚动动画，以处理新添加的结果元素
      setTimeout(() => {
        refreshElements()
      }, 100)
      
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

// 获取文件大小文本（模拟）
const getFileSizeText = (filename: string) => {
  // 这里可以根据实际文件信息返回大小
  // 目前返回模拟数据
  return '< 10MB'
}

// 跳转到任务列表
const goToTaskList = () => {
  router.push('/app/delivery/list')
}
</script>

<style scoped>
/* ========== 页面基础样式 ========== */
.upload-page {
  min-height: 100vh;
  position: relative;
}


/* ========== 主卡片 ========== */
.main-card {
  margin-top: var(--spacing-6);
  margin-bottom: var(--spacing-8);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.5);
  background: rgba(255, 255, 255, 0.9);
}

.card-header {
  padding: 0;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.header-title {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
  color: var(--color-gray-800);
}

.header-stats {
  display: flex;
  gap: var(--spacing-4);
  align-items: center;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-1);
  font-size: var(--font-size-sm);
  color: var(--color-gray-600);
  padding: var(--spacing-1) var(--spacing-2);
  background: rgba(94, 114, 228, 0.1);
  border-radius: var(--radius-full);
}

/* ========== 上传说明 ========== */
.upload-tips {
  margin-bottom: var(--spacing-4);
  padding: var(--spacing-5);
  background: var(--gradient-glass);
  backdrop-filter: var(--backdrop-blur);
  border: 1px solid rgba(94, 114, 228, 0.2);
  border-radius: var(--radius-xl);
  box-shadow: 0 4px 16px rgba(94, 114, 228, 0.1);
  position: relative;
}

.tips-header {
  display: flex;
  align-items: center;
  gap: var(--spacing-3);
  margin-bottom: var(--spacing-4);
}

.tips-icon {
  font-size: var(--font-size-xl);
  color: var(--color-info);
}

.tips-header h3 {
  margin: 0;
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
  color: var(--color-gray-800);
}

.tips-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: var(--spacing-3);
}

.tip-item {
  display: flex;
  align-items: flex-start;
  gap: var(--spacing-2);
  padding: var(--spacing-3);
  background: rgba(255, 255, 255, 0.7);
  border-radius: var(--radius-lg);
  border: 1px solid rgba(255, 255, 255, 0.3);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  transition: all var(--duration-200) var(--ease-out);
}

.tip-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(94, 114, 228, 0.15);
  border-color: rgba(94, 114, 228, 0.2);
}

.tip-icon {
  font-size: var(--font-size-lg);
  color: var(--color-primary);
  margin-top: var(--spacing-1);
}

.tip-content h4 {
  margin: 0 0 var(--spacing-1) 0;
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  color: var(--color-gray-800);
}

.tip-content p {
  margin: 0;
  font-size: var(--font-size-xs);
  color: var(--color-gray-600);
}

/* ========== 上传区域 ========== */
.upload-container {
  margin: var(--spacing-3) 0;
  padding: var(--spacing-4);
  background: rgba(255, 255, 255, 0.6);
  border-radius: var(--radius-2xl);
  backdrop-filter: var(--backdrop-blur-sm);
  border: 1px solid rgba(94, 114, 228, 0.15);
  box-shadow: 0 6px 24px rgba(94, 114, 228, 0.08);
  min-height: 400px; /* 确保最小高度能容纳拖拽区域 */
  height: auto; /* 自适应内容高度 */
}

.upload-section-title {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: var(--spacing-2);
  margin-bottom: var(--spacing-4);
  font-size: var(--font-size-xl);
  font-weight: var(--font-weight-semibold);
  color: var(--color-gray-800);
}

.batch-upload-area {
  position: relative;
  max-width: 1200px;
  margin: 0 auto;
  width: 100%;
  padding: 0 var(--spacing-2); /* 添加内边距防止溢出 */
  box-sizing: border-box;
  min-height: 350px; /* 确保有足够高度显示拖拽区域 */
}

/* 现代化上传样式 */
.modern-upload :deep(.el-upload-dragger) {
  width: 100%;
  max-width: 100%; /* 确保不超出父容器 */
  height: 320px;
  border: 2px dashed rgba(94, 114, 228, 0.3);
  border-radius: var(--radius-2xl);
  background: var(--gradient-glass);
  backdrop-filter: var(--backdrop-blur);
  text-align: center;
  cursor: pointer;
  transition: all var(--duration-300) var(--ease-out);
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;
  margin: var(--spacing-2) 0; /* 减少上下边距避免被遮挡 */
  box-sizing: border-box;
}

.modern-upload :deep(.el-upload-dragger::before) {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(45deg, transparent, rgba(94, 114, 228, 0.05), transparent);
  transform: translateX(-100%);
  transition: transform var(--duration-500) var(--ease-out);
}

.modern-upload :deep(.el-upload-dragger:hover) {
  border-color: var(--color-primary);
  background: rgba(94, 114, 228, 0.05);
  transform: translateY(-4px);
  box-shadow: var(--shadow-primary);
}

.modern-upload :deep(.el-upload-dragger:hover::before) {
  transform: translateX(100%);
}

.modern-upload :deep(.el-upload-dragger.is-dragover) {
  border-color: var(--color-success);
  background: rgba(45, 206, 137, 0.1);
  transform: scale(1.02);
  box-shadow: var(--shadow-success);
}

.batch-upload-content {
  text-align: center;
  color: var(--color-gray-700);
  z-index: 1;
  position: relative;
}

.upload-animation {
  margin-bottom: var(--spacing-4);
}

.upload-icon {
  font-size: 4rem;
  color: var(--color-primary);
  margin-bottom: var(--spacing-3);
}

.upload-text {
  font-size: var(--font-size-xl);
  font-weight: var(--font-weight-semibold);
  color: var(--color-gray-800);
  margin-bottom: var(--spacing-2);
}

.upload-hint {
  font-size: var(--font-size-base);
  color: var(--color-gray-600);
  margin-bottom: var(--spacing-4);
}

.upload-features {
  display: flex;
  justify-content: center;
  gap: var(--spacing-3);
  flex-wrap: wrap;
}

.feature-tag {
  display: flex;
  align-items: center;
  gap: var(--spacing-1);
  padding: var(--spacing-1) var(--spacing-3);
  background: rgba(94, 114, 228, 0.1);
  color: var(--color-primary-dark);
  border-radius: var(--radius-full);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-medium);
}

/* ========== 控制面板 ========== */
.modern-controls {
  margin-top: var(--spacing-6);
  background: var(--gradient-card);
  backdrop-filter: var(--backdrop-blur);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: var(--radius-2xl);
  padding: var(--spacing-6);
  box-shadow: var(--shadow-lg);
  max-width: 1200px;
  margin-left: auto;
  margin-right: auto;
  width: 100%;
  box-sizing: border-box;
}

.controls-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--spacing-6);
}

.batch-info {
  flex: 1;
}

.info-stats {
  display: flex;
  gap: var(--spacing-4);
  margin-bottom: var(--spacing-3);
}

.stat-card {
  display: flex;
  align-items: center;
  gap: var(--spacing-3);
  padding: var(--spacing-3) var(--spacing-4);
  background: rgba(255, 255, 255, 0.7);
  border-radius: var(--radius-lg);
  border: 1px solid rgba(255, 255, 255, 0.3);
}

.stat-icon {
  font-size: var(--font-size-lg);
}

.stat-details {
  display: flex;
  flex-direction: column;
}

.stat-number {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-bold);
  line-height: 1;
}

.stat-label {
  font-size: var(--font-size-xs);
  color: var(--color-gray-500);
}

.text-success { color: var(--color-success) !important; }
.text-danger { color: var(--color-danger) !important; }

.error-warning {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  padding: var(--spacing-2) var(--spacing-3);
  background: rgba(245, 54, 92, 0.1);
  color: var(--color-danger-dark);
  border-radius: var(--radius-lg);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
}

.batch-actions {
  display: flex;
  gap: var(--spacing-3);
  align-items: center;
}

.button-content {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
}

.loading-content {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
}

.btn-loading {
  opacity: 0.8;
  pointer-events: none;
}

/* ========== 进度显示 ========== */
.modern-progress {
  margin: var(--spacing-6) 0;
  background: var(--gradient-card);
  backdrop-filter: var(--backdrop-blur);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: var(--radius-2xl);
  padding: var(--spacing-8);
  box-shadow: var(--shadow-xl);
}

.progress-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-8);
}

.progress-title {
  display: flex;
  align-items: center;
  gap: var(--spacing-3);
}

.progress-title h3 {
  margin: 0;
  font-size: var(--font-size-2xl);
  font-weight: var(--font-weight-semibold);
  color: var(--color-gray-800);
}

.progress-stats {
  display: flex;
  align-items: baseline;
  gap: var(--spacing-2);
}

.progress-fraction {
  font-size: var(--font-size-2xl);
  font-weight: var(--font-weight-bold);
  color: var(--color-primary);
}

.progress-label {
  font-size: var(--font-size-sm);
  color: var(--color-gray-600);
}

.overall-progress-card {
  display: flex;
  align-items: center;
  gap: var(--spacing-8);
  margin-bottom: var(--spacing-8);
  padding: var(--spacing-6);
  background: rgba(255, 255, 255, 0.5);
  border-radius: var(--radius-xl);
}

.progress-ring-container {
  flex-shrink: 0;
}

.progress-ring {
  position: relative;
  width: 120px;
  height: 120px;
}

.progress-circle {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  background: conic-gradient(var(--color-primary) calc(var(--progress) * 1%), rgba(148, 163, 184, 0.2) 0);
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
}

.progress-circle::before {
  content: '';
  position: absolute;
  inset: 12px;
  border-radius: 50%;
  background: white;
}

.progress-percentage {
  position: relative;
  z-index: 1;
  font-size: var(--font-size-xl);
  font-weight: var(--font-weight-bold);
  color: var(--color-primary);
}

.progress-info {
  flex: 1;
}

.progress-bar-wrapper {
  margin-bottom: var(--spacing-4);
}

.progress-bar-modern {
  width: 100%;
  height: 12px;
  background: rgba(148, 163, 184, 0.2);
  border-radius: var(--radius-full);
  overflow: hidden;
  position: relative;
}

.progress-fill {
  height: 100%;
  background: var(--gradient-primary);
  border-radius: var(--radius-full);
  transition: width var(--duration-500) var(--ease-out);
  position: relative;
  overflow: hidden;
}

.progress-fill::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.4), transparent);
  animation: shimmer 2s infinite;
}

.progress-complete {
  background: var(--gradient-success) !important;
}

.progress-details {
  display: flex;
  gap: var(--spacing-4);
  flex-wrap: wrap;
}

.detail-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-1);
  font-size: var(--font-size-sm);
  color: var(--color-gray-600);
}

/* ========== 文件进度列表 ========== */
.file-progress-section {
  margin-top: var(--spacing-8);
}

.section-subtitle {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  margin-bottom: var(--spacing-6);
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
  color: var(--color-gray-800);
}

.file-progress-list {
  max-height: 400px;
  overflow-y: auto;
  padding-right: var(--spacing-2);
}

.file-progress-card {
  background: rgba(255, 255, 255, 0.7);
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: var(--radius-lg);
  padding: var(--spacing-4);
  margin-bottom: var(--spacing-3);
  transition: all var(--duration-200) var(--ease-out);
}

.file-progress-card:hover {
  transform: translateX(4px);
  box-shadow: var(--shadow-md);
}

.file-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-3);
}

.file-info {
  display: flex;
  align-items: center;
  gap: var(--spacing-3);
  flex: 1;
  min-width: 0;
}

.file-icon {
  font-size: var(--font-size-lg);
  color: var(--color-primary);
}

.file-details {
  display: flex;
  flex-direction: column;
  min-width: 0;
  flex: 1;
}

.file-name {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--color-gray-800);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.file-size {
  font-size: var(--font-size-xs);
  color: var(--color-gray-500);
}

.file-status {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
}

.status-badge {
  padding: var(--spacing-1) var(--spacing-2);
  border-radius: var(--radius-sm);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-medium);
}

.status-pending {
  background: rgba(148, 163, 184, 0.1);
  color: var(--color-gray-600);
}

.status-uploading {
  background: rgba(17, 205, 239, 0.1);
  color: var(--color-info-dark);
}

.status-success {
  background: rgba(45, 206, 137, 0.1);
  color: var(--color-success-dark);
}

.status-error {
  background: rgba(245, 54, 92, 0.1);
  color: var(--color-danger-dark);
}

.status-percentage {
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-bold);
  color: var(--color-gray-700);
}

.file-progress-bar {
  margin-bottom: var(--spacing-2);
}

.progress-track {
  width: 100%;
  height: 6px;
  background: rgba(148, 163, 184, 0.2);
  border-radius: var(--radius-full);
  overflow: hidden;
}

.progress-thumb {
  height: 100%;
  border-radius: var(--radius-full);
  transition: width var(--duration-300) var(--ease-out);
}

.progress-pending { background: var(--color-gray-400); }
.progress-uploading { background: var(--color-info); }
.progress-success { background: var(--color-success); }
.progress-error { background: var(--color-danger); }

.file-error {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  padding: var(--spacing-2) var(--spacing-3);
  background: rgba(245, 54, 92, 0.1);
  color: var(--color-danger-dark);
  border-radius: var(--radius-md);
  font-size: var(--font-size-xs);
}

/* ========== 结果区域 ========== */
.results-section {
  margin-top: var(--spacing-6);
}

.results-card {
  background: var(--gradient-card);
  backdrop-filter: var(--backdrop-blur);
}

.results-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0;
}

.header-content {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-3);
  flex: 1;
}

.header-title {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
  color: var(--color-gray-800);
}

.header-summary {
  display: flex;
  gap: var(--spacing-4);
}

.summary-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-1);
  padding: var(--spacing-1) var(--spacing-3);
  border-radius: var(--radius-full);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
}

.summary-item.success {
  background: rgba(45, 206, 137, 0.1);
  color: var(--color-success-dark);
}

.summary-item.error {
  background: rgba(245, 54, 92, 0.1);
  color: var(--color-danger-dark);
}

.results-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
  gap: var(--spacing-6);
  margin-top: var(--spacing-6);
}

.result-card {
  background: rgba(255, 255, 255, 0.7);
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: var(--radius-xl);
  padding: var(--spacing-6);
  transition: all var(--duration-300) var(--ease-out);
  position: relative;
  overflow: hidden;
}

.result-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  border-radius: var(--radius-xl) var(--radius-xl) 0 0;
  transition: all var(--duration-200) var(--ease-out);
}

.result-success::before {
  background: var(--gradient-success);
}

.result-error::before {
  background: linear-gradient(135deg, var(--color-danger) 0%, var(--color-danger-dark) 100%);
}

.result-header {
  display: flex;
  align-items: center;
  gap: var(--spacing-4);
  margin-bottom: var(--spacing-4);
}

.result-image {
  flex-shrink: 0;
}

.image-preview {
  width: 80px;
  height: 80px;
  border-radius: var(--radius-lg);
  overflow: hidden;
  border: 2px solid rgba(255, 255, 255, 0.5);
}

.image-placeholder {
  width: 80px;
  height: 80px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-gray-100);
  color: var(--color-gray-400);
  font-size: var(--font-size-2xl);
  border-radius: var(--radius-lg);
}

.result-status {
  flex: 1;
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  padding: var(--spacing-2) var(--spacing-4);
  border-radius: var(--radius-full);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
}

.status-indicator.status-success {
  background: rgba(45, 206, 137, 0.1);
  color: var(--color-success-dark);
}

.status-indicator.status-error {
  background: rgba(245, 54, 92, 0.1);
  color: var(--color-danger-dark);
}

.result-body {
  border-top: 1px solid rgba(255, 255, 255, 0.3);
  padding-top: var(--spacing-4);
}

.detail-item {
  display: flex;
  align-items: flex-start;
  gap: var(--spacing-3);
  margin-bottom: var(--spacing-3);
}

.detail-item:last-child {
  margin-bottom: 0;
}

.detail-content {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-1);
  flex: 1;
}

.detail-label {
  font-size: var(--font-size-xs);
  color: var(--color-gray-500);
  font-weight: var(--font-weight-medium);
}

.detail-value {
  font-size: var(--font-size-sm);
  color: var(--color-gray-800);
  font-weight: var(--font-weight-medium);
}

.qr-code {
  font-family: var(--font-family-mono);
  background: rgba(94, 114, 228, 0.1);
  padding: var(--spacing-1) var(--spacing-2);
  border-radius: var(--radius-sm);
  word-break: break-all;
}

.error-message {
  display: flex;
  align-items: flex-start;
  gap: var(--spacing-3);
  padding: var(--spacing-3);
  background: rgba(245, 54, 92, 0.1);
  border-radius: var(--radius-lg);
  margin-bottom: var(--spacing-3);
}

.error-content {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-1);
}

.error-label {
  font-size: var(--font-size-xs);
  color: var(--color-danger-dark);
  font-weight: var(--font-weight-medium);
}

.error-text {
  font-size: var(--font-size-sm);
  color: var(--color-danger-dark);
  font-weight: var(--font-weight-medium);
}

/* ========== 动画 ========== */
.rotate {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* ========== 动画修复 ========== */
/* 确保元素默认可见，防止滚动动画失效导致元素不可见 */
.animate-on-scroll {
  opacity: 1 !important;
  transform: translateY(0) !important;
}

.animate-on-scroll.in-view {
  opacity: 1;
  transform: translateY(0);
}

/* ========== 响应式设计 ========== */
@media (max-width: 768px) {
  .header-content {
    flex-direction: column;
    align-items: flex-start;
    gap: var(--spacing-3);
  }
  
  .header-stats {
    align-self: stretch;
    justify-content: space-between;
  }
  
  .tips-grid {
    grid-template-columns: 1fr;
  }
  
  .modern-upload :deep(.el-upload-dragger) {
    height: 280px;
  }
  
  .upload-container {
    padding: var(--spacing-4);
  }
  
  .batch-upload-area {
    max-width: 100%;
  }
  
  .upload-icon {
    font-size: 3rem;
  }
  
  .upload-text {
    font-size: var(--font-size-lg);
  }
  
  .controls-content {
    flex-direction: column;
    align-items: stretch;
    gap: var(--spacing-4);
  }
  
  .info-stats {
    justify-content: space-around;
  }
  
  .batch-actions {
    justify-content: stretch;
  }
  
  .batch-actions .btn {
    flex: 1;
  }
  
  .overall-progress-card {
    flex-direction: column;
    text-align: center;
    gap: var(--spacing-6);
  }
  
  .progress-details {
    justify-content: center;
  }
  
  .results-grid {
    grid-template-columns: 1fr;
  }
  
  .results-header {
    flex-direction: column;
    align-items: stretch;
    gap: var(--spacing-4);
  }
  
  .header-content {
    align-items: center;
    text-align: center;
  }
  
  .header-summary {
    justify-content: center;
  }
  
  .result-header {
    flex-direction: column;
    text-align: center;
  }
}

@media (max-width: 480px) {
  .upload-features {
    flex-direction: column;
    align-items: center;
  }
  
  .feature-tag {
    justify-content: center;
    min-width: 120px;
  }
  
  .file-header {
    flex-direction: column;
    align-items: flex-start;
    gap: var(--spacing-2);
  }
  
  .file-status {
    align-self: stretch;
    justify-content: space-between;
  }
}
</style>