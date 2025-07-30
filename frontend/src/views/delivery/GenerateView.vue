<template>
  <div class="generate-delivery">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>生成送达回证</span>
        </div>
      </template>
      
      <el-form
        ref="formRef"
        :model="form"
        :rules="formRules"
        label-width="120px"
        size="large"
      >
        <el-form-item label="快递单号" prop="tracking_number">
          <el-input
            v-model="form.tracking_number"
            placeholder="请输入快递单号"
            clearable
          />
        </el-form-item>
        
        <el-form-item label="文书标题" prop="doc_title">
          <el-input
            v-model="form.doc_title"
            placeholder="例如：送达回证"
            clearable
          />
        </el-form-item>
        
        <el-form-item label="送达人">
          <el-input
            v-model="form.sender"
            placeholder="请输入送达人姓名"
            clearable
          />
        </el-form-item>
        
        <el-form-item label="送达时间">
          <el-input
            v-model="form.send_time"
            placeholder="留空将自动从物流信息获取"
            clearable
          >
            <template #append>
              <el-button @click="getAutoTime">自动获取</el-button>
            </template>
          </el-input>
          <div class="form-tip">
            提示：留空将自动从物流数据中提取快递寄出时间
          </div>
        </el-form-item>
        
        <el-form-item label="送达地点">
          <el-input
            v-model="form.send_location"
            placeholder="请输入送达地点"
            clearable
          />
        </el-form-item>
        
        <el-form-item label="受送达人">
          <el-input
            v-model="form.receiver"
            placeholder="请输入受送达人姓名"
            clearable
          />
        </el-form-item>
        
        <el-form-item>
          <el-button
            type="primary"
            :loading="deliveryStore.generating"
            @click="handleGenerate"
          >
            <el-icon><Document /></el-icon>
            生成送达回证
          </el-button>
          
          <el-button @click="resetForm">
            <el-icon><Refresh /></el-icon>
            重置表单
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>
    
    <!-- 生成结果 -->
    <el-card v-if="generateResult" style="margin-top: 20px;">
      <template #header>
        <div class="card-header">
          <span>生成结果</span>
        </div>
      </template>
      
      <el-result
        icon="success"
        title="送达回证生成成功！"
        :sub-title="`文档大小：${formatFileSize(generateResult.file_size)}`"
      >
        <template #extra>
          <el-button type="primary" @click="downloadReceipt">
            <el-icon><Download /></el-icon>
            下载文档
          </el-button>
          
          <el-button @click="viewReceipt">
            <el-icon><View /></el-icon>
            查看详情
          </el-button>
        </template>
      </el-result>
      
      <el-descriptions title="生成信息" :column="2" border>
        <el-descriptions-item label="快递单号">
          {{ generateResult.tracking_number }}
        </el-descriptions-item>
        <el-descriptions-item label="回证ID">
          {{ generateResult.receipt_id }}
        </el-descriptions-item>
        <el-descriptions-item label="文档名称">
          {{ generateResult.doc_filename }}
        </el-descriptions-item>
        <el-descriptions-item label="文件大小">
          {{ formatFileSize(generateResult.file_size) }}
        </el-descriptions-item>
      </el-descriptions>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { Document, Refresh, Download, View } from '@element-plus/icons-vue'
import { useDeliveryStore } from '@/stores/delivery'
import { useTrackingStore } from '@/stores/tracking'
import type { DeliveryReceiptGenerateRequest, DeliveryReceiptGenerateResponse } from '@/types'

const router = useRouter()
const deliveryStore = useDeliveryStore()
const trackingStore = useTrackingStore()

// 表单引用
const formRef = ref<FormInstance>()

// 表单数据
const form = reactive<DeliveryReceiptGenerateRequest>({
  tracking_number: '',
  doc_title: '送达回证',
  sender: '',
  send_time: '',
  send_location: '',
  receiver: ''
})

// 表单验证规则
const formRules: FormRules = {
  tracking_number: [
    { required: true, message: '请输入快递单号', trigger: 'blur' },
    { min: 8, message: '快递单号长度不能少于8位', trigger: 'blur' }
  ],
  doc_title: [
    { required: true, message: '请输入文书标题', trigger: 'blur' }
  ]
}

// 生成结果
const generateResult = ref<DeliveryReceiptGenerateResponse | null>(null)

// 自动获取时间
const getAutoTime = async () => {
  if (!form.tracking_number) {
    ElMessage.warning('请先输入快递单号')
    return
  }
  
  try {
    await trackingStore.getTrackingInfo(form.tracking_number)
    if (trackingStore.trackingInfo) {
      // 这里可以从物流信息中提取时间
      ElMessage.success('将在生成时自动从物流信息获取时间')
      form.send_time = '' // 清空，让后端自动处理
    }
  } catch (error) {
    ElMessage.error('获取物流信息失败')
  }
}

// 生成送达回证
const handleGenerate = async () => {
  if (!formRef.value) return
  
  try {
    await formRef.value.validate()
    
    const response = await deliveryStore.generateReceipt(form)
    
    if (response.success && response.data) {
      generateResult.value = response.data
      ElMessage.success('送达回证生成成功！')
    }
  } catch (error) {
    console.error('Generate receipt failed:', error)
  }
}

// 重置表单
const resetForm = () => {
  if (formRef.value) {
    formRef.value.resetFields()
  }
  generateResult.value = null
}

// 下载回证
const downloadReceipt = async () => {
  if (!generateResult.value) return
  
  try {
    await deliveryStore.downloadReceipt(generateResult.value.tracking_number)
    ElMessage.success('下载开始')
  } catch (error) {
    ElMessage.error('下载失败')
  }
}

// 查看回证详情
const viewReceipt = () => {
  if (generateResult.value) {
    router.push(`/delivery/list`)
  }
}

// 格式化文件大小
const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}
</script>

<style scoped>
.generate-delivery {
  padding: 20px;
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

.el-button + .el-button {
  margin-left: 10px;
}

@media (max-width: 768px) {
  .generate-delivery {
    padding: 10px;
  }
  
  .el-form {
    padding: 0;
  }
}
</style>