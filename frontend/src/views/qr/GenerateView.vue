<template>
  <div class="qr-generate">
    <el-row :gutter="20">
      <!-- 输入区域 -->
      <el-col :span="12">
        <el-card class="input-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <el-icon><Grid /></el-icon>
              <span>二维码生成</span>
            </div>
          </template>
          
          <el-form :model="qrForm" :rules="qrRules" ref="qrFormRef" label-width="100px">
            <el-form-item label="内容类型" prop="type">
              <el-select v-model="qrForm.type" placeholder="请选择内容类型" @change="handleTypeChange">
                <el-option label="文本" value="text" />
                <el-option label="网址" value="url" />
                <el-option label="WiFi" value="wifi" />
                <el-option label="联系人" value="contact" />
                <el-option label="短信" value="sms" />
                <el-option label="邮箱" value="email" />
              </el-select>
            </el-form-item>

            <!-- 文本类型 -->
            <template v-if="qrForm.type === 'text'">
              <el-form-item label="文本内容" prop="content">
                <el-input
                  v-model="qrForm.content"
                  type="textarea"
                  :rows="4"
                  placeholder="请输入要生成二维码的文本内容"
                  maxlength="500"
                  show-word-limit
                />
              </el-form-item>
            </template>

            <!-- 网址类型 -->
            <template v-if="qrForm.type === 'url'">
              <el-form-item label="网址" prop="content">
                <el-input
                  v-model="qrForm.content"
                  placeholder="请输入网址，如: https://www.example.com"
                />
              </el-form-item>
            </template>

            <!-- WiFi类型 -->
            <template v-if="qrForm.type === 'wifi'">
              <el-form-item label="网络名称" prop="wifiSsid">
                <el-input v-model="qrForm.wifiSsid" placeholder="WiFi网络名称(SSID)" />
              </el-form-item>
              <el-form-item label="密码" prop="wifiPassword">
                <el-input v-model="qrForm.wifiPassword" type="password" placeholder="WiFi密码" show-password />
              </el-form-item>
              <el-form-item label="加密类型" prop="wifiSecurity">
                <el-select v-model="qrForm.wifiSecurity" placeholder="选择加密类型">
                  <el-option label="WPA/WPA2" value="WPA" />
                  <el-option label="WEP" value="WEP" />
                  <el-option label="无密码" value="nopass" />
                </el-select>
              </el-form-item>
            </template>

            <!-- 联系人类型 -->
            <template v-if="qrForm.type === 'contact'">
              <el-form-item label="姓名" prop="contactName">
                <el-input v-model="qrForm.contactName" placeholder="联系人姓名" />
              </el-form-item>
              <el-form-item label="电话" prop="contactPhone">
                <el-input v-model="qrForm.contactPhone" placeholder="联系人电话" />
              </el-form-item>
              <el-form-item label="邮箱" prop="contactEmail">
                <el-input v-model="qrForm.contactEmail" placeholder="联系人邮箱" />
              </el-form-item>
              <el-form-item label="公司" prop="contactOrg">
                <el-input v-model="qrForm.contactOrg" placeholder="公司/组织" />
              </el-form-item>
            </template>

            <!-- 短信类型 -->
            <template v-if="qrForm.type === 'sms'">
              <el-form-item label="手机号" prop="smsPhone">
                <el-input v-model="qrForm.smsPhone" placeholder="接收短信的手机号" />
              </el-form-item>
              <el-form-item label="短信内容" prop="smsMessage">
                <el-input
                  v-model="qrForm.smsMessage"
                  type="textarea"
                  :rows="3"
                  placeholder="短信内容"
                />
              </el-form-item>
            </template>

            <!-- 邮箱类型 -->
            <template v-if="qrForm.type === 'email'">
              <el-form-item label="邮箱地址" prop="emailTo">
                <el-input v-model="qrForm.emailTo" placeholder="收件人邮箱" />
              </el-form-item>
              <el-form-item label="主题" prop="emailSubject">
                <el-input v-model="qrForm.emailSubject" placeholder="邮件主题" />
              </el-form-item>
              <el-form-item label="邮件内容" prop="emailBody">
                <el-input
                  v-model="qrForm.emailBody"
                  type="textarea"
                  :rows="3"
                  placeholder="邮件内容"
                />
              </el-form-item>
            </template>

            <!-- 高级设置 -->
            <el-divider content-position="left">高级设置</el-divider>
            
            <el-form-item label="尺寸大小">
              <el-slider
                v-model="qrForm.size"
                :min="100"
                :max="500"
                :step="10"
                show-stops
                show-input
              />
            </el-form-item>
            
            <el-form-item label="容错级别">
              <el-select v-model="qrForm.errorLevel" placeholder="选择容错级别">
                <el-option label="低 (L) ~7%" value="L" />
                <el-option label="中 (M) ~15%" value="M" />
                <el-option label="四分位 (Q) ~25%" value="Q" />
                <el-option label="高 (H) ~30%" value="H" />
              </el-select>
            </el-form-item>

            <el-form-item label="前景色">
              <el-color-picker v-model="qrForm.foregroundColor" />
            </el-form-item>

            <el-form-item label="背景色">
              <el-color-picker v-model="qrForm.backgroundColor" />
            </el-form-item>

            <el-form-item>
              <el-button type="primary" :loading="loading" @click="handleGenerate">
                <el-icon><Magic /></el-icon>
                生成二维码
              </el-button>
              <el-button @click="handleReset">重置</el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>

      <!-- 预览区域 -->
      <el-col :span="12">
        <el-card class="preview-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <el-icon><View /></el-icon>
              <span>二维码预览</span>
            </div>
          </template>
          
          <div class="preview-content">
            <div v-if="qrImageUrl" class="qr-preview">
              <img :src="qrImageUrl" :alt="qrForm.content" class="qr-image" />
              
              <div class="preview-info">
                <el-descriptions :column="2" size="small" border>
                  <el-descriptions-item label="类型">
                    {{ getTypeText(qrForm.type) }}
                  </el-descriptions-item>
                  <el-descriptions-item label="尺寸">
                    {{ qrForm.size }}x{{ qrForm.size }}px
                  </el-descriptions-item>
                  <el-descriptions-item label="容错级别">
                    {{ qrForm.errorLevel }}
                  </el-descriptions-item>
                  <el-descriptions-item label="文件大小">
                    {{ qrFileSize }}
                  </el-descriptions-item>
                </el-descriptions>
              </div>
              
              <div class="preview-actions">
                <el-button type="success" :icon="Download" @click="handleDownload">
                  下载PNG
                </el-button>
                <el-button type="primary" :icon="Download" @click="handleDownloadSVG">
                  下载SVG
                </el-button>
                <el-button type="warning" :icon="Share" @click="handleCopyLink">
                  复制链接
                </el-button>
              </div>
            </div>
            
            <el-empty v-else description="请填写内容并生成二维码">
              <el-icon size="64" color="#e4e7ed"><Grid /></el-icon>
            </el-empty>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 历史记录 -->
    <el-card v-if="qrHistory.length > 0" class="history-card" shadow="hover">
      <template #header>
        <div class="card-header">
          <span>生成历史</span>
          <el-button type="text" @click="clearHistory">
            <el-icon><Delete /></el-icon>
            清空记录
          </el-button>
        </div>
      </template>
      
      <div class="history-grid">
        <div
          v-for="(item, index) in qrHistory"
          :key="index"
          class="history-item"
          @click="loadFromHistory(item)"
        >
          <img :src="item.imageUrl" :alt="item.content" class="history-qr" />
          <div class="history-info">
            <div class="history-type">{{ getTypeText(item.type) }}</div>
            <div class="history-content">{{ item.content.substring(0, 20) }}...</div>
            <div class="history-time">{{ formatDate(item.createdAt) }}</div>
          </div>
          <el-button
            type="danger"
            size="small"
            circle
            class="history-delete"
            @click.stop="removeFromHistory(index)"
          >
            <el-icon><Close /></el-icon>
          </el-button>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import {
  Grid,
  View,
  Magic,
  Download,
  Share,
  Delete,
  Close
} from '@element-plus/icons-vue'
import { qrApi } from '@/api/qr'

// 响应式数据
const loading = ref(false)
const qrImageUrl = ref('')
const qrFileSize = ref('')
const qrHistory = ref<any[]>([])

// 表单引用
const qrFormRef = ref<FormInstance>()

// 表单数据
const qrForm = reactive({
  type: 'text',
  content: '',
  size: 200,
  errorLevel: 'M',
  foregroundColor: '#000000',
  backgroundColor: '#ffffff',
  // WiFi相关字段
  wifiSsid: '',
  wifiPassword: '',
  wifiSecurity: 'WPA',
  // 联系人相关字段
  contactName: '',
  contactPhone: '',
  contactEmail: '',
  contactOrg: '',
  // 短信相关字段
  smsPhone: '',
  smsMessage: '',
  // 邮箱相关字段
  emailTo: '',
  emailSubject: '',
  emailBody: ''
})

// 表单验证规则
const qrRules: FormRules = {
  type: [
    { required: true, message: '请选择内容类型', trigger: 'change' }
  ],
  content: [
    { required: true, message: '请输入内容', trigger: 'blur' }
  ],
  wifiSsid: [
    { required: true, message: '请输入WiFi网络名称', trigger: 'blur' }
  ],
  contactName: [
    { required: true, message: '请输入联系人姓名', trigger: 'blur' }
  ],
  smsPhone: [
    { required: true, message: '请输入手机号', trigger: 'blur' },
    { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号', trigger: 'blur' }
  ],
  emailTo: [
    { required: true, message: '请输入邮箱地址', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱地址', trigger: 'blur' }
  ]
}

// 获取类型文本
const getTypeText = (type: string) => {
  const typeMap = {
    text: '文本',
    url: '网址',
    wifi: 'WiFi',
    contact: '联系人',
    sms: '短信',
    email: '邮箱'
  }
  return typeMap[type] || '未知'
}

// 构建二维码内容
const buildQRContent = () => {
  switch (qrForm.type) {
    case 'text':
      return qrForm.content
    case 'url':
      return qrForm.content.startsWith('http') ? qrForm.content : `https://${qrForm.content}`
    case 'wifi':
      return `WIFI:T:${qrForm.wifiSecurity};S:${qrForm.wifiSsid};P:${qrForm.wifiPassword};;`
    case 'contact':
      return `BEGIN:VCARD\nVERSION:3.0\nFN:${qrForm.contactName}\nTEL:${qrForm.contactPhone}\nEMAIL:${qrForm.contactEmail}\nORG:${qrForm.contactOrg}\nEND:VCARD`
    case 'sms':
      return `SMS:${qrForm.smsPhone}:${qrForm.smsMessage}`
    case 'email':
      return `mailto:${qrForm.emailTo}?subject=${encodeURIComponent(qrForm.emailSubject)}&body=${encodeURIComponent(qrForm.emailBody)}`
    default:
      return qrForm.content
  }
}

// 处理类型变化
const handleTypeChange = () => {
  // 清空相关字段
  Object.keys(qrForm).forEach(key => {
    if (key.startsWith('wifi') || key.startsWith('contact') || key.startsWith('sms') || key.startsWith('email')) {
      qrForm[key] = ''
    }
  })
  qrForm.content = ''
  qrImageUrl.value = ''
}

// 处理生成二维码
const handleGenerate = async () => {
  if (!qrFormRef.value) return
  
  try {
    await qrFormRef.value.validate()
    
    loading.value = true
    
    const content = buildQRContent()
    const params = {
      content,
      size: qrForm.size,
      error_correction: qrForm.errorLevel,
      foreground_color: qrForm.foregroundColor,
      background_color: qrForm.backgroundColor
    }
    
    const response = await qrApi.generate(params)
    qrImageUrl.value = response.data.image_url
    qrFileSize.value = response.data.file_size || '未知'
    
    // 添加到历史记录
    addToHistory({
      type: qrForm.type,
      content: content,
      imageUrl: qrImageUrl.value,
      createdAt: new Date().toISOString(),
      params: { ...params }
    })
    
    ElMessage.success('二维码生成成功')
  } catch (error) {
    console.error('生成二维码失败:', error)
    ElMessage.error('生成二维码失败')
  } finally {
    loading.value = false
  }
}

// 处理下载PNG
const handleDownload = () => {
  if (!qrImageUrl.value) return
  
  const link = document.createElement('a')
  link.href = qrImageUrl.value
  link.download = `qrcode_${Date.now()}.png`
  link.click()
  
  ElMessage.success('下载成功')
}

// 处理下载SVG
const handleDownloadSVG = async () => {
  try {
    const content = buildQRContent()
    const params = {
      content,
      size: qrForm.size,
      error_correction: qrForm.errorLevel,
      foreground_color: qrForm.foregroundColor,
      background_color: qrForm.backgroundColor,
      format: 'svg'
    }
    
    const response = await qrApi.generate(params)
    
    const blob = new Blob([response.data], { type: 'image/svg+xml' })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `qrcode_${Date.now()}.svg`
    link.click()
    window.URL.revokeObjectURL(url)
    
    ElMessage.success('SVG下载成功')
  } catch (error) {
    console.error('下载SVG失败:', error)
    ElMessage.error('下载SVG失败')
  }
}

// 处理复制链接
const handleCopyLink = async () => {
  if (!qrImageUrl.value) return
  
  try {
    await navigator.clipboard.writeText(qrImageUrl.value)
    ElMessage.success('链接已复制到剪贴板')
  } catch (error) {
    console.error('复制失败:', error)
    ElMessage.error('复制失败')
  }
}

// 处理重置
const handleReset = () => {
  qrFormRef.value?.resetFields()
  qrImageUrl.value = ''
  qrFileSize.value = ''
}

// 添加到历史记录
const addToHistory = (item: any) => {
  const history = [...qrHistory.value]
  history.unshift(item)
  
  // 只保留最近20条记录
  if (history.length > 20) {
    history.pop()
  }
  
  qrHistory.value = history
  localStorage.setItem('qrGenerateHistory', JSON.stringify(history))
}

// 从历史记录加载
const loadFromHistory = (item: any) => {
  qrForm.type = item.type
  qrForm.content = item.content
  qrImageUrl.value = item.imageUrl
  
  if (item.params) {
    qrForm.size = item.params.size || 200
    qrForm.errorLevel = item.params.error_correction || 'M'
    qrForm.foregroundColor = item.params.foreground_color || '#000000'
    qrForm.backgroundColor = item.params.background_color || '#ffffff'
  }
}

// 从历史记录中移除
const removeFromHistory = (index: number) => {
  qrHistory.value.splice(index, 1)
  localStorage.setItem('qrGenerateHistory', JSON.stringify(qrHistory.value))
}

// 清空历史记录
const clearHistory = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要清空所有生成记录吗？',
      '确认清空',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    qrHistory.value = []
    localStorage.removeItem('qrGenerateHistory')
    ElMessage.success('已清空生成记录')
  } catch (error) {
    // 用户取消
  }
}

// 格式化日期
const formatDate = (dateStr: string) => {
  try {
    const date = new Date(dateStr)
    return date.toLocaleString('zh-CN')
  } catch (error) {
    return dateStr
  }
}

// 加载历史记录
const loadHistory = () => {
  try {
    const history = localStorage.getItem('qrGenerateHistory')
    if (history) {
      qrHistory.value = JSON.parse(history)
    }
  } catch (error) {
    console.error('加载历史记录失败:', error)
  }
}

// 组件挂载时加载历史记录
onMounted(() => {
  loadHistory()
})
</script>

<style scoped>
.qr-generate {
  padding: 0;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.card-header span {
  font-weight: 600;
}

.input-card,
.preview-card {
  height: fit-content;
}

.preview-content {
  text-align: center;
  min-height: 400px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.qr-preview {
  width: 100%;
}

.qr-image {
  max-width: 300px;
  max-height: 300px;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  margin-bottom: 20px;
}

.preview-info {
  margin-bottom: 20px;
}

.preview-actions {
  display: flex;
  justify-content: center;
  gap: 10px;
  flex-wrap: wrap;
}

.history-card {
  margin-top: 20px;
}

.history-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 15px;
}

.history-item {
  position: relative;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  padding: 10px;
  cursor: pointer;
  transition: all 0.3s;
}

.history-item:hover {
  border-color: #409eff;
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.15);
}

.history-qr {
  width: 80px;
  height: 80px;
  border-radius: 4px;
  margin-bottom: 8px;
}

.history-info {
  text-align: left;
}

.history-type {
  font-weight: 600;
  color: #333;
  margin-bottom: 4px;
}

.history-content {
  color: #666;
  font-size: 12px;
  margin-bottom: 4px;
}

.history-time {
  color: #999;
  font-size: 11px;
}

.history-delete {
  position: absolute;
  top: 5px;
  right: 5px;
  width: 20px;
  height: 20px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .qr-generate .el-col {
    margin-bottom: 20px;
  }
  
  .preview-actions .el-button {
    margin: 5px 2px;
    font-size: 12px;
  }
  
  .history-grid {
    grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
    gap: 10px;
  }
}
</style>