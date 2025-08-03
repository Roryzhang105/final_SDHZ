<template>
  <div class="page-content task-detail">
    <!-- 顶部基本信息 -->
    <el-card class="info-card" shadow="hover">
      <div class="task-header">
        <div class="header-left">
          <h2>任务详情</h2>
          <p class="task-id">任务ID: {{ taskInfo.task_id }}</p>
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
        <div class="header-right">
          <el-tag 
            :type="getStatusType(taskInfo.status)"
            size="large"
            class="status-tag"
          >
            {{ getStatusText(taskInfo.status) }}
          </el-tag>
          <p class="create-time">创建时间: {{ formatDateTime(taskInfo.created_at) }}</p>
        </div>
      </div>
    </el-card>

    <!-- 进度时间线 -->
    <el-card class="timeline-card" shadow="hover">
      <template #header>
        <span>处理进度</span>
      </template>
      
      <el-timeline class="process-timeline">
        <el-timeline-item
          :type="getTimelineType('uploaded')"
          :hollow="!isStepCompleted('uploaded')"
          timestamp="图片上传"
          placement="top"
        >
          <div class="timeline-content">
            <h4>图片上传 ✓</h4>
            <p>已上传图片文件</p>
            <div v-if="taskInfo.image_url" class="timeline-image">
              <el-image
                :src="getImageUrl(taskInfo.image_url)"
                fit="cover"
                style="width: 100px; height: 80px; border-radius: 4px;"
                :preview-src-list="[getImageUrl(taskInfo.image_url)]"
              >
                <template #error>
                  <div class="image-error">图片加载失败</div>
                </template>
              </el-image>
            </div>
          </div>
        </el-timeline-item>

        <el-timeline-item
          :type="getTimelineType('recognized')"
          :hollow="!isStepCompleted('recognized')"
          timestamp="二维码识别"
          placement="top"
        >
          <div class="timeline-content">
            <h4>二维码识别</h4>
            <div v-if="taskInfo.qr_code || taskInfo.tracking_number">
              <p class="success-text">✓ 识别成功</p>
              <div class="qr-result">
                <strong>识别结果:</strong> {{ taskInfo.qr_code }}
              </div>
              <div v-if="taskInfo.tracking_number" class="tracking-number">
                <strong>快递单号:</strong> {{ taskInfo.tracking_number }}
              </div>
            </div>
            <div v-else-if="taskInfo.status === 'recognizing'">
              <p class="processing-text">🔄 正在识别中...</p>
            </div>
            <div v-else-if="taskInfo.status === 'failed'">
              <p class="error-text">❌ 识别失败</p>
              <p class="error-detail">{{ taskInfo.error_message }}</p>
            </div>
            <div v-else>
              <p class="pending-text">⏳ 等待识别</p>
            </div>
          </div>
        </el-timeline-item>

        <el-timeline-item
          :type="getTimelineType('tracking')"
          :hollow="!isStepCompleted('tracking')"
          timestamp="物流查询"
          placement="top"
        >
          <div class="timeline-content">
            <h4>物流查询</h4>
            <div v-if="taskInfo.tracking_data && taskInfo.delivery_status">
              <p class="success-text">✓ 查询成功</p>
              <div class="tracking-info">
                <p><strong>当前状态:</strong> {{ taskInfo.delivery_status }}</p>
                <p v-if="taskInfo.tracking_data.traces && taskInfo.tracking_data.traces.length > 0">
                  <strong>最新位置:</strong> {{ taskInfo.tracking_data.traces[0].areaName || '未知' }}
                </p>
                <p v-if="taskInfo.delivery_time">
                  <strong>签收时间:</strong> {{ formatDateTime(taskInfo.delivery_time) }}
                </p>
                <p v-if="taskInfo.tracking_data.is_signed">
                  <span class="success-text">📦 快递已签收</span>
                </p>
                <!-- 物流轨迹预览 -->
                <div v-if="taskInfo.tracking_data.traces && taskInfo.tracking_data.traces.length > 0" class="tracking-timeline">
                  <p><strong>物流轨迹:</strong></p>
                  <div class="timeline-preview">
                    <div 
                      v-for="(trace, index) in taskInfo.tracking_data.traces.slice(0, 3)" 
                      :key="index"
                      class="timeline-item"
                    >
                      <span class="timeline-time">{{ trace.ftime }}</span>
                      <span class="timeline-content">{{ trace.context }}</span>
                    </div>
                    <div v-if="taskInfo.tracking_data.traces.length > 3" class="timeline-more">
                      ...还有{{ taskInfo.tracking_data.traces.length - 3 }}条记录
                    </div>
                  </div>
                </div>
              </div>
            </div>
            <div v-else-if="taskInfo.status === 'tracking'">
              <p class="processing-text">🔄 正在查询中...</p>
            </div>
            <div v-else-if="['tracking', 'delivered'].includes(taskInfo.status) && taskInfo.error_message">
              <p class="error-text">❌ 查询失败</p>
              <p class="error-detail">{{ taskInfo.error_message }}</p>
            </div>
            <div v-else-if="!taskInfo.tracking_number">
              <p class="pending-text">⏳ 等待识别快递单号</p>
            </div>
            <div v-else>
              <p class="pending-text">⏳ 等待查询</p>
            </div>
          </div>
        </el-timeline-item>

        <el-timeline-item
          :type="getTimelineType('delivered')"
          :hollow="!isStepCompleted('delivered')"
          timestamp="等待签收"
          placement="top"
        >
          <div class="timeline-content">
            <h4>等待签收</h4>
            <div v-if="taskInfo.status === 'delivered' || taskInfo.delivery_time">
              <p class="success-text">✓ 已签收</p>
              <p>快递已成功签收，可以生成回证</p>
              <p v-if="taskInfo.delivery_time">
                <strong>签收时间:</strong> {{ formatDateTime(taskInfo.delivery_time) }}
              </p>
            </div>
            <div v-else-if="taskInfo.status === 'failed' && taskInfo.tracking_data">
              <p class="error-text">❌ 快递尚未签收</p>
              <p class="error-detail">快递还在运输中，暂时无法生成回证</p>
            </div>
            <div v-else-if="taskInfo.status === 'failed'">
              <p class="error-text">❌ 无法获取签收信息</p>
              <p class="error-detail">{{ taskInfo.error_message || '物流查询失败' }}</p>
            </div>
            <div v-else-if="taskInfo.tracking_data && !taskInfo.tracking_data.is_signed">
              <p class="processing-text">🚛 运输中</p>
              <p>快递正在运输中，等待签收</p>
            </div>
            <div v-else>
              <p class="pending-text">⏳ 等待物流信息</p>
            </div>
          </div>
        </el-timeline-item>

        <el-timeline-item
          :type="getTimelineType('generating')"
          :hollow="!isStepCompleted('generating')"
          timestamp="生成文档"
          placement="top"
        >
          <div class="timeline-content">
            <h4>生成文档</h4>
            <div v-if="taskInfo.status === 'completed'">
              <p class="success-text">✓ 文档已生成</p>
              <p>送达回证文档生成完成</p>
              <div class="generated-files">
                <p v-if="taskInfo.document_url"><strong>📄 送达回证:</strong> 已生成</p>
                <p v-if="taskInfo.screenshot_url"><strong>📊 物流截图:</strong> 已生成</p>
                <p v-if="taskInfo.extra_metadata?.qr_label_url"><strong>🏷️ 二维码标签:</strong> 已生成</p>
              </div>
            </div>
            <div v-else-if="taskInfo.status === 'generating'">
              <p class="processing-text">📝 正在生成文档...</p>
              <p>正在生成物流截图、二维码标签和送达回证</p>
            </div>
            <div v-else-if="taskInfo.status === 'failed' && (taskInfo.screenshot_url || taskInfo.extra_metadata?.qr_label_url)">
              <p class="error-text">❌ 文档生成失败</p>
              <p class="error-detail">{{ taskInfo.error_message || '送达回证生成失败' }}</p>
              <div class="generated-files">
                <p v-if="taskInfo.screenshot_url" class="success-text"><strong>📊 物流截图:</strong> 已生成</p>
                <p v-if="taskInfo.extra_metadata?.qr_label_url" class="success-text"><strong>🏷️ 二维码标签:</strong> 已生成</p>
                <p class="error-text"><strong>📄 送达回证:</strong> 生成失败</p>
              </div>
            </div>
            <div v-else-if="taskInfo.status === 'failed'">
              <p class="error-text">❌ 文档生成失败</p>
              <p class="error-detail">{{ taskInfo.error_message || '文档生成过程中出现错误' }}</p>
            </div>
            <div v-else-if="taskInfo.status === 'delivered'">
              <p class="pending-text">⏳ 准备生成文档</p>
            </div>
            <div v-else>
              <p class="pending-text">⏳ 等待生成</p>
            </div>
          </div>
        </el-timeline-item>

        <el-timeline-item
          :type="getTimelineType('completed')"
          :hollow="!isStepCompleted('completed')"
          timestamp="任务完成"
          placement="top"
        >
          <div class="timeline-content">
            <h4>任务完成</h4>
            <div v-if="taskInfo.status === 'completed'">
              <p class="success-text">🎉 任务处理完成</p>
              <p>所有步骤已完成，可下载相关文件</p>
            </div>
            <div v-else>
              <p class="pending-text">⏳ 等待完成</p>
            </div>
          </div>
        </el-timeline-item>
      </el-timeline>
    </el-card>

    <el-row :gutter="20">
      <!-- 表单信息区域 -->
      <el-col :xs="24" :lg="12">
        <el-card class="form-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <span>回证信息</span>
              <el-button 
                type="text" 
                :icon="Edit"
                @click="toggleEdit"
              >
                {{ isEditing ? '取消编辑' : '编辑信息' }}
              </el-button>
            </div>
          </template>

          <el-form
            ref="formRef"
            :model="formData"
            :rules="formRules"
            label-width="100px"
            :disabled="!isEditing"
          >
            <el-form-item label="文书标题" prop="doc_title">
              <el-input
                v-model="formData.doc_title"
                placeholder="例如：送达回证"
                clearable
              />
            </el-form-item>

            <el-form-item label="送达人" prop="sender">
              <el-input
                v-model="formData.sender"
                placeholder="请输入送达人姓名"
                clearable
              />
            </el-form-item>

            <el-form-item label="送达地点" prop="send_location">
              <el-input
                v-model="formData.send_location"
                placeholder="请输入送达地点"
                clearable
              />
            </el-form-item>

            <el-form-item label="受送达人" prop="receiver">
              <el-input
                v-model="formData.receiver"
                placeholder="请输入受送达人姓名"
                clearable
              />
            </el-form-item>

            <el-form-item label="送达时间" prop="send_time">
              <el-date-picker
                v-model="formData.send_time"
                type="datetime"
                placeholder="选择送达时间"
                format="YYYY-MM-DD HH:mm:ss"
                value-format="YYYY-MM-DD HH:mm:ss"
                style="width: 100%"
              />
              <div class="form-tip">
                留空将自动从物流数据中获取签收时间
              </div>
            </el-form-item>

            <el-form-item label="备注" prop="remarks">
              <el-input
                v-model="formData.remarks"
                type="textarea"
                :rows="3"
                placeholder="请输入备注信息"
              />
            </el-form-item>

            <el-form-item v-if="isEditing">
              <el-button type="primary" :loading="saving" @click="handleSaveForm">
                <el-icon><Check /></el-icon>
                保存信息
              </el-button>
              <el-button @click="handleCancelEdit">
                <el-icon><Close /></el-icon>
                取消
              </el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>

      <!-- 文件下载区域 -->
      <el-col :xs="24" :lg="12">
        <el-card class="download-card" shadow="hover">
          <template #header>
            <span>相关文件</span>
          </template>

          <div class="download-list">
            <!-- 送达回证文档 -->
            <div class="download-item">
              <div class="file-info">
                <el-icon class="file-icon" color="#409EFF"><Document /></el-icon>
                <div class="file-details">
                  <h4>送达回证</h4>
                  <p class="file-desc">Word文档格式</p>
                </div>
              </div>
              <div class="file-actions">
                <!-- 有文档时显示下载按钮 -->
                <el-button
                  v-if="hasExistingDocument"
                  type="success"
                  :icon="Download"
                  @click="handleDownload('document')"
                >
                  下载
                </el-button>
                
                <!-- 可以生成时显示生成/重新生成按钮 -->
                <el-button
                  v-if="canGenerateManually"
                  :type="hasExistingDocument ? 'warning' : 'primary'"
                  :icon="DocumentAdd"
                  :loading="generating"
                  @click="handleManualGenerate"
                >
                  {{ hasExistingDocument ? '重新生成' : '生成文档' }}
                </el-button>
                
                <!-- 其他状态显示标签 -->
                <el-tag v-if="!hasExistingDocument && !canGenerateManually" type="info">
                  未生成
                </el-tag>
              </div>
            </div>

            <!-- 物流截图 -->
            <div class="download-item">
              <div class="file-info">
                <el-icon class="file-icon" color="#67C23A"><Picture /></el-icon>
                <div class="file-details">
                  <h4>物流截图</h4>
                  <p class="file-desc">PNG图片格式</p>
                </div>
              </div>
              <div class="file-actions">
                <el-button
                  v-if="taskInfo.screenshot_url"
                  type="success"
                  :icon="Download"
                  @click="handleDownload('screenshot')"
                >
                  下载
                </el-button>
                <el-tag v-else type="info">未生成</el-tag>
              </div>
            </div>

            <!-- 二维码条形码标签 -->
            <div class="download-item">
              <div class="file-info">
                <el-icon class="file-icon" color="#F56C6C"><Document /></el-icon>
                <div class="file-details">
                  <h4>二维码条形码标签</h4>
                  <p class="file-desc">合成的标签图片</p>
                </div>
              </div>
              <div class="file-actions">
                <el-button
                  v-if="taskInfo.extra_metadata?.qr_label_url"
                  type="success"
                  :icon="Download"
                  @click="handleDownload('qr_label')"
                >
                  下载
                </el-button>
                <el-tag v-else type="info">未生成</el-tag>
              </div>
            </div>

            <!-- 上传的原图 -->
            <div class="download-item">
              <div class="file-info">
                <el-icon class="file-icon" color="#E6A23C"><Camera /></el-icon>
                <div class="file-details">
                  <h4>上传的图片</h4>
                  <p class="file-desc">原始图片文件</p>
                </div>
              </div>
              <div class="file-actions">
                <el-button
                  v-if="taskInfo.image_url"
                  type="primary"
                  :icon="Download"
                  @click="handleDownload('image')"
                >
                  下载
                </el-button>
                <el-tag v-else type="info">未找到</el-tag>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 操作按钮 -->
    <div class="action-buttons">
      <el-button size="large" @click="handleBack">
        <el-icon><ArrowLeft /></el-icon>
        返回列表
      </el-button>
      

      <el-button 
        v-if="taskInfo.status === 'failed'"
        type="warning" 
        size="large"
        :loading="retrying"
        @click="handleRetry"
      >
        <el-icon><Refresh /></el-icon>
        重试任务
      </el-button>

      <el-button 
        v-if="taskInfo.status === 'completed'"
        type="success" 
        size="large"
        @click="handleDownloadAll"
      >
        <el-icon><FolderOpened /></el-icon>
        下载所有文件
      </el-button>

      <el-button 
        v-if="authStore.isAdmin"
        type="danger" 
        size="large"
        :loading="deleting"
        @click="handleDeleteTask"
      >
        <el-icon><Delete /></el-icon>
        删除任务
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import {
  Edit,
  Check,
  Close,
  Download,
  Document,
  DocumentAdd,
  Picture,
  Camera,
  ArrowLeft,
  FolderOpened,
  Refresh,
  Delete
} from '@element-plus/icons-vue'
import { tasksApi } from '@/api/tasks'
import { deliveryApi } from '@/api/delivery'
import { useDeliveryStore } from '@/stores/delivery'
import { useAuthStore } from '@/stores/auth'
import { useWebSocket, type WebSocketMessage } from '@/utils/websocket'

const route = useRoute()
const router = useRouter()  
const deliveryStore = useDeliveryStore()
const authStore = useAuthStore()

// 响应式数据
const taskInfo = ref({
  task_id: '',
  status: 'pending',
  created_at: '',
  updated_at: '',
  image_url: '',
  qr_result: '',
  tracking_number: '',
  document_url: '',
  screenshot_url: '',
  error_message: ''
})

const trackingInfo = ref(null)
const isEditing = ref(false)
const saving = ref(false)
const generating = ref(false)
const retrying = ref(false)
const deleting = ref(false)
const formRef = ref<FormInstance>()

// WebSocket客户端
let wsClient: ReturnType<typeof useWebSocket> | null = null

// 表单数据
const formData = reactive({
  doc_title: '送达回证',
  sender: '',
  send_location: '',
  receiver: '',
  send_time: '',
  remarks: ''
})

// 表单验证规则
const formRules: FormRules = {
  doc_title: [
    { required: true, message: '请输入文书标题', trigger: 'blur' }
  ]
}

// 任务状态映射
const statusMap = {
  pending: { text: '待处理', type: 'info' },
  recognizing: { text: '识别中', type: 'warning' },
  tracking: { text: '查询物流中', type: 'warning' },
  delivered: { text: '已签收', type: 'success' },
  generating: { text: '生成文档中', type: 'warning' },
  completed: { text: '已完成', type: 'success' },
  failed: { text: '失败', type: 'danger' }
}

// 计算属性
const canGenerateManually = computed(() => {
  // 只要有快递单号且任务不是处理中状态，就可以手动生成
  return taskInfo.value.tracking_number && 
         !['pending', 'recognizing', 'tracking', 'generating'].includes(taskInfo.value.status)
})

// 检查是否有现有文档
const hasExistingDocument = computed(() => {
  return !!taskInfo.value.document_url
})

// 获取状态类型
const getStatusType = (status: string) => {
  return statusMap[status]?.type || 'info'
}

// 获取状态文本
const getStatusText = (status: string) => {
  return statusMap[status]?.text || '未知'
}

// 判断步骤是否完成
const isStepCompleted = (step: string) => {
  const stepOrder = ['uploaded', 'recognized', 'tracking', 'delivered', 'generating', 'completed']
  const currentIndex = stepOrder.indexOf(getStepFromStatus(taskInfo.value.status))
  const stepIndex = stepOrder.indexOf(step)
  
  if (taskInfo.value.status === 'failed') {
    // 失败状态下根据已有数据判断完成了哪些步骤
    if (step === 'uploaded') return true  // 上传肯定完成了
    if (step === 'recognized' && (taskInfo.value.qr_code || taskInfo.value.tracking_number)) return true
    if (step === 'tracking' && taskInfo.value.tracking_data) return true
    if (step === 'delivered' && taskInfo.value.delivery_time) return true
    if (step === 'generating' && taskInfo.value.document_url) return true
    return false
  }
  
  return stepIndex <= currentIndex
}

// 从状态获取步骤
const getStepFromStatus = (status: string) => {
  const statusStepMap = {
    pending: 'uploaded',
    recognizing: 'uploaded',
    tracking: 'recognized',
    delivered: 'tracking',
    generating: 'delivered',
    completed: 'completed',
    failed: 'uploaded'
  }
  return statusStepMap[status] || 'uploaded'
}

// 获取时间线类型
const getTimelineType = (step: string) => {
  if (taskInfo.value.status === 'failed') {
    // 失败状态下，已完成的步骤显示成功，未完成的显示危险
    return isStepCompleted(step) ? 'success' : 'danger'
  }
  
  // 正常状态下，已完成显示成功，未完成显示信息
  if (isStepCompleted(step)) {
    return 'success'
  }
  
  // 当前正在进行的步骤显示警告色
  const currentStep = getStepFromStatus(taskInfo.value.status)
  if (step === currentStep) {
    return 'warning'
  }
  
  return 'info'
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

// 获取图片URL
const getImageUrl = (imageUrl: string) => {
  if (!imageUrl) return ''
  // 如果已经是完整URL，直接返回
  if (imageUrl.startsWith('http://') || imageUrl.startsWith('https://')) {
    return imageUrl
  }
  // 如果是相对路径，拼接后端地址
  const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
  return imageUrl.startsWith('/') ? `${baseUrl}${imageUrl}` : `${baseUrl}/${imageUrl}`
}

// 获取任务详情
const fetchTaskDetail = async (taskId: string) => {
  try {
    // 调用真实API
    const response = await tasksApi.getTaskDetail(taskId)
    
    if (response.success) {
      taskInfo.value = response.data
      
      // 尝试获取已保存的回证信息
      if (taskInfo.value.tracking_number) {
        try {
          const receiptResponse = await deliveryApi.getByTrackingNumber(taskInfo.value.tracking_number)
          
          if (receiptResponse.success && receiptResponse.data.receipt_info) {
            const receiptInfo = receiptResponse.data.receipt_info
            // 使用已保存的数据填充表单
            Object.assign(formData, {
              doc_title: receiptInfo.doc_title || '送达回证',
              sender: receiptInfo.sender || '',
              send_location: receiptInfo.send_location || '',
              receiver: receiptInfo.receiver || '',
              send_time: receiptInfo.send_time || '',
              remarks: receiptInfo.remarks || ''
            })
          } else {
            // 使用默认值
            Object.assign(formData, {
              doc_title: '送达回证',
              sender: '',
              send_location: '',
              receiver: '',
              send_time: '',
              remarks: ''
            })
          }
        } catch (receiptError) {
          console.log('获取回证信息失败，使用默认值:', receiptError)
          // 使用默认值
          Object.assign(formData, {
            doc_title: '送达回证',
            sender: '',
            send_location: '',
            receiver: '',
            send_time: '',
            remarks: ''
          })
        }
      } else {
        // 设置表单数据的默认值
        Object.assign(formData, {
          doc_title: '送达回证',
          sender: '',
          send_location: '',
          receiver: '',
          send_time: '',
          remarks: ''
        })
      }
      
      // 物流信息暂时为空，等待实现真实的物流查询
      trackingInfo.value = null
      
    } else {
      throw new Error(response.message || '获取任务详情失败')
    }
    
  } catch (error) {
    console.error('获取任务详情失败:', error)
    ElMessage.error('获取任务详情失败')
  }
}

// 切换编辑模式
const toggleEdit = () => {
  isEditing.value = !isEditing.value
}

// 保存表单
const handleSaveForm = async () => {
  if (!formRef.value) return
  
  try {
    await formRef.value.validate()
    saving.value = true
    
    // 调用真实的保存API
    const response = await deliveryApi.updateInfo(taskInfo.value.tracking_number, {
      doc_title: formData.doc_title,
      sender: formData.sender,
      send_time: formData.send_time,
      send_location: formData.send_location,
      receiver: formData.receiver,
      remarks: formData.remarks
    })
    
    if (response.success) {
      ElMessage.success('信息保存成功')
      isEditing.value = false
    } else {
      throw new Error(response.message || '保存失败')
    }
  } catch (error) {
    console.error('保存失败:', error)
    if (error.response?.data?.detail) {
      ElMessage.error(`保存失败: ${error.response.data.detail}`)
    } else {
      ElMessage.error('保存失败，请重试')
    }
  } finally {
    saving.value = false
  }
}

// 取消编辑
const handleCancelEdit = async () => {
  isEditing.value = false
  // 重新获取数据以重置表单
  await fetchTaskDetail(taskInfo.value.task_id)
}

// 手动生成回证
const handleManualGenerate = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要手动生成送达回证吗？这将重新生成文档并替换现有文件。',
      '确认操作',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    generating.value = true
    
    // 调用真实的重新生成API
    const response = await deliveryApi.regenerate(taskInfo.value.tracking_number)
    
    if (response.success) {
      ElMessage.success('送达回证重新生成成功！')
      
      // 更新任务信息
      taskInfo.value.status = 'completed'
      taskInfo.value.document_url = `/static/documents/${response.data.doc_filename}`
      
      // 重新获取任务详情以确保数据一致
      await fetchTaskDetail(taskInfo.value.task_id)
    } else {
      throw new Error(response.message || '生成失败')
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('生成失败:', error)
      if (error.response?.data?.detail) {
        ElMessage.error(`生成失败: ${error.response.data.detail}`)
      } else {
        ElMessage.error('生成失败，请重试')
      }
    }
  } finally {
    generating.value = false
  }
}

// 下载文件
const handleDownload = async (type: 'document' | 'screenshot' | 'image' | 'qr_label') => {
  try {
    // Word文档通过API下载，其他文件直接下载
    if (type === 'document') {
      await handleDownloadDocument()
      return
    }
    
    const fileMap = {
      screenshot: { url: taskInfo.value.screenshot_url, name: `物流截图_${taskInfo.value.tracking_number}.png` },
      image: { url: taskInfo.value.image_url, name: `原图_${taskInfo.value.task_id}.jpg` },
      qr_label: { url: taskInfo.value.extra_metadata?.qr_label_url, name: `二维码标签_${taskInfo.value.tracking_number}.png` }
    }
    
    const file = fileMap[type]
    if (!file.url) {
      ElMessage.warning('文件不存在')
      return
    }
    
    // 使用getImageUrl处理URL
    const downloadUrl = getImageUrl(file.url)
    
    // 创建下载链接
    const link = document.createElement('a')
    link.href = downloadUrl
    link.download = file.name
    link.target = '_blank'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    
    ElMessage.success(`开始下载 ${file.name}`)
    
  } catch (error) {
    console.error('下载失败:', error)
    ElMessage.error('下载失败')
  }
}

// 通过API下载Word文档
const handleDownloadDocument = async () => {
  try {
    const trackingNumber = taskInfo.value?.tracking_number
    if (!trackingNumber) {
      ElMessage.error('找不到快递单号')
      return
    }
    
    // 调用store中的下载方法
    await deliveryStore.downloadReceipt(trackingNumber)
    ElMessage.success('送达回证下载成功')
    
  } catch (error) {
    console.error('下载送达回证失败:', error)
    ElMessage.error('下载送达回证失败')
  }
}

// 下载所有文件
const handleDownloadAll = async () => {
  try {
    ElMessage.success('开始打包下载所有文件')
    // 实际项目中调用打包下载API
  } catch (error) {
    console.error('下载失败:', error)
    ElMessage.error('下载失败')
  }
}

// 重试任务
const handleRetry = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要重试这个任务吗？系统会根据当前进度从合适的步骤开始重新处理。',
      '确认重试',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    retrying.value = true
    
    // 调用重试API
    const response = await tasksApi.retryTask(taskInfo.value.task_id)
    
    if (response.success) {
      ElMessage.success('任务重试已启动，请稍候查看处理结果')
      // 重新获取任务详情
      await fetchTaskDetail(taskInfo.value.task_id)
    } else {
      throw new Error(response.message || '重试失败')
    }
    
  } catch (error) {
    if (error !== 'cancel') {
      console.error('重试失败:', error)
      ElMessage.error('重试失败，请稍后再试')
    }
  } finally {
    retrying.value = false
  }
}

// 删除任务
const handleDeleteTask = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要删除这个任务吗？此操作将永久删除任务及其相关的所有文件，无法恢复。',
      '危险操作确认',
      {
        confirmButtonText: '确定删除',
        cancelButtonText: '取消',
        type: 'error',
        customClass: 'delete-confirm-dialog'
      }
    )
    
    deleting.value = true
    
    // 调用删除API
    await tasksApi.deleteTask(taskInfo.value.task_id)
    
    ElMessage.success('任务删除成功')
    
    // 返回任务列表
    router.push('/app/delivery/list')
    
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除任务失败:', error)
      if (error.response?.status === 403) {
        ElMessage.error('权限不足，仅管理员可删除任务')
      } else if (error.response?.data?.detail) {
        ElMessage.error(`删除失败: ${error.response.data.detail}`)
      } else {
        ElMessage.error('删除任务失败，请稍后再试')
      }
    }
  } finally {
    deleting.value = false
  }
}

// 返回列表
const handleBack = () => {
  router.push('/app/delivery/list')
}

// WebSocket连接和消息处理
const initWebSocket = (taskId: string) => {
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
      // 订阅当前任务的更新
      wsClient?.subscribeToTask(taskId)
    } else {
      console.log('WebSocket连接断开')
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
  
  // 建立连接
  wsClient.connect()
}

const handleTaskUpdate = (message: WebSocketMessage) => {
  console.log('收到任务更新:', message)
  
  const taskId = message.task_id
  if (!taskId || taskId !== taskInfo.value.task_id) return
  
  // 更新任务信息
  if (message.status) {
    taskInfo.value.status = message.status
  }
  
  // 合并新数据
  if (message.data) {
    Object.assign(taskInfo.value, message.data)
  }
  
  // 显示状态更新消息
  if (message.message) {
    ElMessage.info(`任务更新: ${message.message}`)
  }
  
  // 如果状态为已完成，可能需要刷新表单数据
  if (message.status === 'completed' && message.data?.document_url) {
    ElMessage.success('文档生成完成！')
  }
}

const cleanupWebSocket = () => {
  if (wsClient) {
    wsClient.disconnect()
    wsClient = null
  }
}

// 组件挂载时获取数据
onMounted(() => {
  const taskId = route.params.id as string
  if (taskId) {
    fetchTaskDetail(taskId)
    initWebSocket(taskId)
  } else {
    ElMessage.error('任务ID不存在')
    router.push('/app/delivery/list')
  }
})

// 组件卸载时清理WebSocket连接
onUnmounted(() => {
  cleanupWebSocket()
})
</script>

<style scoped>
.task-detail {
  /* padding已通过page-content类提供 */
}

.info-card {
  margin-bottom: 20px;
}

.task-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.header-left h2 {
  margin: 0 0 5px 0;
  font-size: 24px;
  color: #333;
}

.task-id {
  color: #666;
  font-size: 14px;
  margin: 0 0 10px 0;
}

.connection-status {
  margin-top: 5px;
}

.header-right {
  text-align: right;
}

.status-tag {
  margin-bottom: 10px;
}

.create-time {
  color: #666;
  font-size: 14px;
  margin: 0;
}

.timeline-card {
  margin-bottom: 20px;
}

.process-timeline {
  padding: 20px 0;
}

.timeline-content h4 {
  margin: 0 0 10px 0;
  color: #333;
}

.timeline-content p {
  margin: 5px 0;
  color: #666;
}

.timeline-image {
  margin-top: 10px;
}

.image-error {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100px;
  height: 80px;
  background-color: #f5f7fa;
  color: #909399;
  font-size: 12px;
  border-radius: 4px;
}

.qr-result {
  background-color: #f0f9ff;
  padding: 10px;
  border-radius: 4px;
  margin-top: 10px;
  font-family: monospace;
}

.tracking-number {
  background-color: #f0f9ff;
  padding: 10px;
  border-radius: 4px;
  margin-top: 10px;
  font-family: monospace;
}

.tracking-info {
  background-color: #f0f9ff;
  padding: 10px;
  border-radius: 4px;
  margin-top: 10px;
}

.tracking-info p {
  margin: 5px 0;
}

.tracking-timeline {
  margin-top: 15px;
}

.timeline-preview {
  background-color: #fafafa;
  border-radius: 4px;
  padding: 10px;
  margin-top: 8px;
}

.timeline-item {
  display: block;
  margin-bottom: 8px;
  font-size: 12px;
  line-height: 1.4;
}

.timeline-time {
  color: #909399;
  margin-right: 10px;
  font-weight: bold;
}

.timeline-content {
  color: #606266;
}

.timeline-more {
  color: #909399;
  font-size: 11px;
  text-align: center;
  margin-top: 8px;
}

.generated-files {
  margin-top: 10px;
}

.generated-files p {
  margin: 3px 0;
  font-size: 13px;
  color: #67c23a;
}

.success-text {
  color: #67c23a;
  font-weight: bold;
}

.processing-text {
  color: #e6a23c;
  font-weight: bold;
}

.error-text {
  color: #f56c6c;
  font-weight: bold;
}

.pending-text {
  color: #909399;
}

.error-detail {
  color: #f56c6c;
  font-size: 12px;
}

.form-card, .download-card {
  height: fit-content;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.form-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 5px;
}


.download-list {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.download-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  transition: all 0.3s;
}

.download-item:hover {
  border-color: #409eff;
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.1);
}

.file-info {
  display: flex;
  align-items: center;
  gap: 15px;
}

.file-icon {
  font-size: 32px;
}

.file-details h4 {
  margin: 0 0 5px 0;
  color: #333;
  font-size: 16px;
}

.file-desc {
  margin: 0;
  color: #666;
  font-size: 12px;
}

.action-buttons {
  display: flex;
  justify-content: center;
  gap: 15px;
  margin-top: 30px;
}

@media (max-width: 768px) {
  
  .task-header {
    flex-direction: column;
    gap: 15px;
  }
  
  .header-right {
    text-align: left;
  }
  
  .download-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 15px;
  }
  
  .file-actions {
    width: 100%;
    display: flex;
    justify-content: center;
  }
  
  .action-buttons {
    flex-direction: column;
    align-items: center;
  }
  
  .action-buttons .el-button {
    width: 100%;
    max-width: 300px;
  }
}

/* 删除确认对话框样式 */
:deep(.delete-confirm-dialog) {
  .el-message-box__title {
    color: #f56c6c;
  }
  
  .el-message-box__message {
    color: #606266;
    font-weight: 500;
  }
  
  .el-button--primary {
    background-color: #f56c6c;
    border-color: #f56c6c;
  }
  
  .el-button--primary:hover {
    background-color: #f78989;
    border-color: #f78989;
  }
}
</style>