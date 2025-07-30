<template>
  <div class="qr-recognize">
    <el-row :gutter="20">
      <!-- 上传区域 -->
      <el-col :span="12">
        <el-card class="upload-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <el-icon><Picture /></el-icon>
              <span>二维码识别</span>
            </div>
          </template>
          
          <div class="upload-section">
            <el-upload
              class="qr-uploader"
              drag
              :auto-upload="false"
              :show-file-list="false"
              accept="image/*"
              :on-change="handleFileChange"
            >
              <div class="upload-content">
                <el-icon class="upload-icon"><Upload /></el-icon>
                <div class="upload-text">
                  <p>点击或拖拽图片到此处上传</p>
                  <p class="upload-tip">支持 JPG、PNG、GIF 格式，文件大小不超过 10MB</p>
                </div>
              </div>
            </el-upload>
            
            <div v-if="uploadedImage" class="uploaded-image">
              <img :src="uploadedImage" alt="上传的图片" />
              <div class="image-actions">
                <el-button type="primary" :loading="recognizing" @click="handleRecognize">
                  <el-icon><Search /></el-icon>
                  识别二维码
                </el-button>
                <el-button @click="clearImage">清除图片</el-button>
              </div>
            </div>
          </div>
          
          <!-- 摄像头拍照 -->
          <el-divider content-position="center">或</el-divider>
          
          <div class="camera-section">
            <el-button type="success" :icon="Camera" @click="openCamera" :disabled="cameraActive">
              {{ cameraActive ? '摄像头已开启' : '使用摄像头拍照' }}
            </el-button>
            
            <div v-if="cameraActive" class="camera-container">
              <video ref="videoRef" autoplay muted class="camera-video"></video>
              <div class="camera-actions">
                <el-button type="primary" @click="capturePhoto">拍照</el-button>
                <el-button @click="closeCamera">关闭摄像头</el-button>
              </div>
              <canvas ref="canvasRef" style="display: none;"></canvas>
            </div>
          </div>
        </el-card>
      </el-col>

      <!-- 结果区域 -->
      <el-col :span="12">
        <el-card class="result-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <el-icon><DataLine /></el-icon>
              <span>识别结果</span>
            </div>
          </template>
          
          <div class="result-content">
            <!-- 识别成功 -->
            <div v-if="recognitionResult" class="result-success">
              <el-alert
                title="识别成功"
                type="success"
                :closable="false"
                show-icon
                class="result-alert"
              />
              
              <div class="result-details">
                <el-descriptions :column="1" border>
                  <el-descriptions-item label="识别类型">
                    <el-tag :type="getContentType(recognitionResult.content)">
                      {{ getContentTypeText(recognitionResult.content) }}
                    </el-tag>
                  </el-descriptions-item>
                  <el-descriptions-item label="识别内容">
                    <div class="content-display">
                      {{ recognitionResult.content }}
                    </div>
                  </el-descriptions-item>
                  <el-descriptions-item label="识别时间">
                    {{ recognitionResult.timestamp }}
                  </el-descriptions-item>
                </el-descriptions>
              </div>
              
              <!-- 操作按钮 -->
              <div class="result-actions">
                <el-button type="primary" :icon="DocumentCopy" @click="copyContent">
                  复制内容
                </el-button>
                <el-button
                  v-if="isUrl(recognitionResult.content)"
                  type="success"
                  :icon="Link"
                  @click="openUrl"
                >
                  打开网址
                </el-button>
                <el-button
                  v-if="isPhone(recognitionResult.content)"
                  type="warning"
                  :icon="Phone"
                  @click="callPhone"
                >
                  拨打电话
                </el-button>
              </div>
              
              <!-- 详细解析 -->
              <div v-if="parsedContent" class="parsed-content">
                <el-divider content-position="left">详细信息</el-divider>
                <component :is="getContentComponent()" :content="parsedContent" />
              </div>
            </div>
            
            <!-- 识别失败 -->
            <div v-else-if="recognitionError" class="result-error">
              <el-alert
                title="识别失败"
                :description="recognitionError"
                type="error"
                show-icon
                :closable="false"
              />
              
              <div class="error-tips">
                <h4>识别建议:</h4>
                <ul>
                  <li>确保图片清晰，二维码完整</li>
                  <li>避免图片模糊或光线过暗</li>
                  <li>尝试调整图片角度</li>
                  <li>确保二维码占据图片的主要部分</li>
                </ul>
              </div>
            </div>
            
            <!-- 默认状态 -->
            <el-empty v-else description="请上传包含二维码的图片">
              <el-icon size="64" color="#e4e7ed"><Picture /></el-icon>
            </el-empty>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 识别历史 -->
    <el-card v-if="recognitionHistory.length > 0" class="history-card" shadow="hover">
      <template #header>
        <div class="card-header">
          <span>识别历史</span>
          <el-button type="text" @click="clearHistory">
            <el-icon><Delete /></el-icon>
            清空记录
          </el-button>
        </div>
      </template>
      
      <el-table :data="recognitionHistory" stripe>
        <el-table-column prop="timestamp" label="时间" width="160" />
        <el-table-column label="类型" width="100">
          <template #default="{ row }">
            <el-tag :type="getContentType(row.content)" size="small">
              {{ getContentTypeText(row.content) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="content" label="内容" min-width="200">
          <template #default="{ row }">
            <div class="content-preview">
              {{ row.content.length > 50 ? row.content.substring(0, 50) + '...' : row.content }}
            </div>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150">
          <template #default="{ row, $index }">
            <el-button type="text" size="small" @click="copyContent(row.content)">
              复制
            </el-button>
            <el-button type="text" size="small" @click="viewDetail(row)">
              查看
            </el-button>
            <el-button type="text" size="small" @click="removeFromHistory($index)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 详情对话框 -->
    <el-dialog v-model="detailDialogVisible" title="识别详情" width="60%">
      <div v-if="currentDetail">
        <el-descriptions :column="1" border>
          <el-descriptions-item label="识别时间">
            {{ currentDetail.timestamp }}
          </el-descriptions-item>
          <el-descriptions-item label="内容类型">
            <el-tag :type="getContentType(currentDetail.content)">
              {{ getContentTypeText(currentDetail.content) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="完整内容">
            <div class="detail-content">
              {{ currentDetail.content }}
            </div>
          </el-descriptions-item>
        </el-descriptions>
      </div>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="detailDialogVisible = false">关闭</el-button>
          <el-button type="primary" @click="copyContent(currentDetail?.content)">
            复制内容
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Picture,
  Upload,
  Search,
  Camera,
  DataLine,
  DocumentCopy,
  Link,
  Phone,
  Delete
} from '@element-plus/icons-vue'
import { qrApi } from '@/api/qr'

// 响应式数据
const recognizing = ref(false)
const uploadedImage = ref('')
const recognitionResult = ref(null)
const recognitionError = ref('')
const recognitionHistory = ref<any[]>([])
const parsedContent = ref(null)

// 摄像头相关
const cameraActive = ref(false)
const videoRef = ref<HTMLVideoElement>()
const canvasRef = ref<HTMLCanvasElement>()
const stream = ref<MediaStream | null>(null)

// 对话框
const detailDialogVisible = ref(false)
const currentDetail = ref(null)

// 处理文件变化
const handleFileChange = (file: any) => {
  const reader = new FileReader()
  reader.onload = (e) => {
    uploadedImage.value = e.target?.result as string
    recognitionResult.value = null
    recognitionError.value = ''
  }
  reader.readAsDataURL(file.raw)
}

// 清除图片
const clearImage = () => {
  uploadedImage.value = ''
  recognitionResult.value = null
  recognitionError.value = ''
}

// 识别二维码
const handleRecognize = async () => {
  if (!uploadedImage.value) {
    ElMessage.warning('请先上传图片')
    return
  }
  
  recognizing.value = true
  recognitionError.value = ''
  
  try {
    // 将base64转换为File对象
    const response = await fetch(uploadedImage.value)
    const blob = await response.blob()
    const file = new File([blob], 'qr-image.jpg', { type: 'image/jpeg' })
    
    const formData = new FormData()
    formData.append('image', file)
    
    const result = await qrApi.recognize(formData)
    
    recognitionResult.value = {
      content: result.data.content,
      timestamp: new Date().toLocaleString('zh-CN')
    }
    
    // 解析内容
    parsedContent.value = parseContent(result.data.content)
    
    // 添加到历史记录
    addToHistory(recognitionResult.value)
    
    ElMessage.success('识别成功')
  } catch (error) {
    console.error('识别失败:', error)
    recognitionError.value = error?.response?.data?.detail || '识别失败，请检查图片是否包含有效的二维码'
    recognitionResult.value = null
  } finally {
    recognizing.value = false
  }
}

// 打开摄像头
const openCamera = async () => {
  try {
    stream.value = await navigator.mediaDevices.getUserMedia({ 
      video: { 
        width: { ideal: 1280 }, 
        height: { ideal: 720 } 
      } 
    })
    
    if (videoRef.value) {
      videoRef.value.srcObject = stream.value
      cameraActive.value = true
    }
  } catch (error) {
    console.error('打开摄像头失败:', error)
    ElMessage.error('无法访问摄像头，请检查权限设置')
  }
}

// 关闭摄像头
const closeCamera = () => {
  if (stream.value) {
    stream.value.getTracks().forEach(track => track.stop())
    stream.value = null
  }
  cameraActive.value = false
}

// 拍照
const capturePhoto = () => {
  if (!videoRef.value || !canvasRef.value) return
  
  const video = videoRef.value
  const canvas = canvasRef.value
  const context = canvas.getContext('2d')
  
  canvas.width = video.videoWidth
  canvas.height = video.videoHeight
  
  context?.drawImage(video, 0, 0)
  
  uploadedImage.value = canvas.toDataURL('image/jpeg')
  closeCamera()
  
  ElMessage.success('拍照成功，请点击识别按钮')
}

// 判断内容类型
const getContentType = (content: string) => {
  if (isUrl(content)) return 'primary'
  if (isPhone(content)) return 'success'
  if (isEmail(content)) return 'warning'
  if (isWifi(content)) return 'info'
  return ''
}

// 获取内容类型文本
const getContentTypeText = (content: string) => {
  if (isUrl(content)) return '网址'
  if (isPhone(content)) return '电话'
  if (isEmail(content)) return '邮箱'
  if (isWifi(content)) return 'WiFi'
  if (isVCard(content)) return '联系人'
  return '文本'
}

// 判断是否为URL
const isUrl = (content: string) => {
  return /^https?:\/\//.test(content)
}

// 判断是否为电话
const isPhone = (content: string) => {
  return /^(tel:|TEL:)?\+?[\d\s\-\(\)]+$/.test(content)
}

// 判断是否为邮箱
const isEmail = (content: string) => {
  return /^mailto:|@/.test(content)
}

// 判断是否为WiFi
const isWifi = (content: string) => {
  return content.startsWith('WIFI:')
}

// 判断是否为联系人
const isVCard = (content: string) => {
  return content.includes('BEGIN:VCARD')
}

// 解析内容
const parseContent = (content: string) => {
  if (isWifi(content)) {
    return parseWifi(content)
  }
  if (isVCard(content)) {
    return parseVCard(content)
  }
  return null
}

// 解析WiFi信息
const parseWifi = (content: string) => {
  const match = content.match(/WIFI:T:([^;]*);S:([^;]*);P:([^;]*);/)
  if (match) {
    return {
      type: 'wifi',
      security: match[1],
      ssid: match[2],
      password: match[3]
    }
  }
  return null
}

// 解析联系人信息
const parseVCard = (content: string) => {
  const lines = content.split('\n')
  const contact: any = { type: 'contact' }
  
  lines.forEach(line => {
    if (line.startsWith('FN:')) {
      contact.name = line.substring(3)
    } else if (line.startsWith('TEL:')) {
      contact.phone = line.substring(4)
    } else if (line.startsWith('EMAIL:')) {
      contact.email = line.substring(6)
    } else if (line.startsWith('ORG:')) {
      contact.org = line.substring(4)
    }
  })
  
  return contact
}

// 获取内容组件
const getContentComponent = () => {
  if (!parsedContent.value) return null
  
  if (parsedContent.value.type === 'wifi') {
    return defineComponent({
      props: ['content'],
      template: `
        <el-descriptions :column="2" size="small" border>
          <el-descriptions-item label="网络名称">{{ content.ssid }}</el-descriptions-item>
          <el-descriptions-item label="加密类型">{{ content.security }}</el-descriptions-item>
          <el-descriptions-item label="密码" :span="2">{{ content.password }}</el-descriptions-item>
        </el-descriptions>
      `
    })
  }
  
  if (parsedContent.value.type === 'contact') {
    return defineComponent({
      props: ['content'],
      template: `
        <el-descriptions :column="2" size="small" border>
          <el-descriptions-item label="姓名">{{ content.name }}</el-descriptions-item>
          <el-descriptions-item label="电话">{{ content.phone }}</el-descriptions-item>
          <el-descriptions-item label="邮箱">{{ content.email }}</el-descriptions-item>
          <el-descriptions-item label="公司">{{ content.org }}</el-descriptions-item>
        </el-descriptions>
      `
    })
  }
  
  return null
}

// 复制内容
const copyContent = async (content?: string) => {
  const textToCopy = content || recognitionResult.value?.content
  if (!textToCopy) return
  
  try {
    await navigator.clipboard.writeText(textToCopy)
    ElMessage.success('内容已复制到剪贴板')
  } catch (error) {
    console.error('复制失败:', error)
    ElMessage.error('复制失败')
  }
}

// 打开网址
const openUrl = () => {
  if (recognitionResult.value?.content) {
    window.open(recognitionResult.value.content, '_blank')
  }
}

// 拨打电话
const callPhone = () => {
  if (recognitionResult.value?.content) {
    const phone = recognitionResult.value.content.replace(/^(tel:|TEL:)/, '')
    window.location.href = `tel:${phone}`
  }
}

// 添加到历史记录
const addToHistory = (result: any) => {
  const history = [...recognitionHistory.value]
  history.unshift(result)
  
  // 只保留最近50条记录
  if (history.length > 50) {
    history.pop()
  }
  
  recognitionHistory.value = history
  localStorage.setItem('qrRecognitionHistory', JSON.stringify(history))
}

// 查看详情
const viewDetail = (item: any) => {
  currentDetail.value = item
  detailDialogVisible.value = true
}

// 从历史记录中移除
const removeFromHistory = (index: number) => {
  recognitionHistory.value.splice(index, 1)
  localStorage.setItem('qrRecognitionHistory', JSON.stringify(recognitionHistory.value))
}

// 清空历史记录
const clearHistory = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要清空所有识别记录吗？',
      '确认清空',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    recognitionHistory.value = []
    localStorage.removeItem('qrRecognitionHistory')
    ElMessage.success('已清空识别记录')
  } catch (error) {
    // 用户取消
  }
}

// 加载历史记录
const loadHistory = () => {
  try {
    const history = localStorage.getItem('qrRecognitionHistory')
    if (history) {
      recognitionHistory.value = JSON.parse(history)
    }
  } catch (error) {
    console.error('加载历史记录失败:', error)
  }
}

// 组件挂载时加载历史记录
onMounted(() => {
  loadHistory()
})

// 组件卸载时关闭摄像头
onUnmounted(() => {
  closeCamera()
})
</script>

<style scoped>
.qr-recognize {
  padding: 0;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.upload-section {
  margin-bottom: 20px;
}

.qr-uploader {
  width: 100%;
}

.upload-content {
  text-align: center;
  padding: 40px 20px;
}

.upload-icon {
  font-size: 48px;
  color: #c0c4cc;
  margin-bottom: 16px;
}

.upload-text p {
  margin: 8px 0;
}

.upload-tip {
  color: #999;
  font-size: 12px;
}

.uploaded-image {
  text-align: center;
  margin-top: 20px;
}

.uploaded-image img {
  max-width: 100%;
  max-height: 300px;
  border-radius: 4px;
  border: 1px solid #e4e7ed;
  margin-bottom: 15px;
}

.image-actions {
  display: flex;
  justify-content: center;
  gap: 10px;
}

.camera-section {
  text-align: center;
}

.camera-container {
  margin-top: 20px;
}

.camera-video {
  width: 100%;
  max-width: 400px;
  height: auto;
  border-radius: 4px;
  border: 1px solid #e4e7ed;
  margin-bottom: 15px;
}

.camera-actions {
  display: flex;
  justify-content: center;
  gap: 10px;
}

.result-content {
  min-height: 400px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.result-success {
  width: 100%;
}

.result-alert {
  margin-bottom: 20px;
}

.result-details {
  margin-bottom: 20px;
}

.content-display {
  word-break: break-all;
  max-height: 200px;
  overflow-y: auto;
  padding: 10px;
  background-color: #f5f7fa;
  border-radius: 4px;
  font-family: monospace;
}

.result-actions {
  display: flex;
  justify-content: center;
  gap: 10px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}

.parsed-content {
  margin-top: 20px;
}

.result-error {
  width: 100%;
}

.error-tips {
  margin-top: 20px;
  padding: 15px;
  background-color: #fdf6ec;
  border-radius: 4px;
}

.error-tips h4 {
  color: #e6a23c;
  margin-bottom: 10px;
}

.error-tips ul {
  color: #666;
  margin: 0;
  padding-left: 20px;
}

.error-tips li {
  margin-bottom: 5px;
}

.history-card {
  margin-top: 20px;
}

.content-preview {
  word-break: break-all;
}

.detail-content {
  word-break: break-all;
  max-height: 300px;
  overflow-y: auto;
  padding: 10px;
  background-color: #f5f7fa;
  border-radius: 4px;
  font-family: monospace;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .qr-recognize .el-col {
    margin-bottom: 20px;
  }
  
  .result-actions .el-button {
    margin: 5px 2px;
    font-size: 12px;
  }
  
  .image-actions .el-button {
    margin: 5px;
  }
  
  .camera-actions .el-button {
    margin: 5px;
  }
}
</style>