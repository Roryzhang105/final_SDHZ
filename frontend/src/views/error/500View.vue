<template>
  <div class="error-container">
    <div class="error-content">
      <div class="error-illustration">
        <el-icon class="error-icon">
          <CircleCloseFilled />
        </el-icon>
        <div class="error-code">500</div>
      </div>
      
      <div class="error-info">
        <h1 class="error-title">服务器错误</h1>
        <p class="error-description">
          抱歉，服务器遇到了一个错误，无法完成您的请求。
        </p>
        <p class="error-suggestion">
          请稍后再试，或者联系系统管理员。如果问题持续存在，请提供以下错误信息。
        </p>
        
        <!-- 错误详情 -->
        <div v-if="errorDetails" class="error-details">
          <el-collapse>
            <el-collapse-item title="错误详情" name="details">
              <div class="error-detail-content">
                <p><strong>时间:</strong> {{ errorDetails.timestamp }}</p>
                <p><strong>请求ID:</strong> {{ errorDetails.requestId }}</p>
                <p v-if="errorDetails.message"><strong>错误信息:</strong> {{ errorDetails.message }}</p>
                <p v-if="errorDetails.code"><strong>错误代码:</strong> {{ errorDetails.code }}</p>
              </div>
            </el-collapse-item>
          </el-collapse>
        </div>
        
        <div class="error-actions">
          <el-button type="primary" size="large" @click="refreshPage">
            <el-icon><Refresh /></el-icon>
            刷新页面
          </el-button>
          <el-button size="large" @click="goHome">
            <el-icon><House /></el-icon>
            返回首页
          </el-button>
          <el-button type="success" size="large" @click="reportError">
            <el-icon><ChatDotRound /></el-icon>
            报告问题
          </el-button>
        </div>
      </div>
    </div>
    
    <!-- 解决方案建议 -->
    <div class="solutions">
      <h3>可能的解决方案</h3>
      <div class="solutions-list">
        <div class="solution-item">
          <el-icon class="solution-icon"><Refresh /></el-icon>
          <div class="solution-content">
            <h4>刷新页面</h4>
            <p>这可能是一个临时的服务器问题，刷新页面可能会解决问题。</p>
          </div>
        </div>
        
        <div class="solution-item">
          <el-icon class="solution-icon"><Clock /></el-icon>
          <div class="solution-content">
            <h4>稍后重试</h4>
            <p>如果是服务器维护或高负载，请等待几分钟后再试。</p>
          </div>
        </div>
        
        <div class="solution-item">
          <el-icon class="solution-icon"><Connection /></el-icon>
          <div class="solution-content">
            <h4>检查网络连接</h4>
            <p>请确认您的网络连接正常，并且可以访问其他网站。</p>
          </div>
        </div>
        
        <div class="solution-item">
          <el-icon class="solution-icon"><Service /></el-icon>
          <div class="solution-content">
            <h4>联系技术支持</h4>
            <p>如果问题持续存在，请通过邮件或电话联系我们的技术支持团队。</p>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 联系信息 -->
    <div class="contact-info">
      <h3>需要帮助？</h3>
      <div class="contact-methods">
        <div class="contact-item">
          <el-icon><Message /></el-icon>
          <span>support@example.com</span>
        </div>
        <div class="contact-item">
          <el-icon><Phone /></el-icon>
          <span>400-xxx-xxxx</span>
        </div>
        <div class="contact-item">
          <el-icon><Clock /></el-icon>
          <span>工作时间: 9:00-18:00</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  CircleCloseFilled,
  Refresh,
  House,
  ChatDotRound,
  Clock,
  Connection,
  Service,
  Message,
  Phone
} from '@element-plus/icons-vue'

const router = useRouter()

// 错误详情
const errorDetails = ref({
  timestamp: new Date().toLocaleString('zh-CN'),
  requestId: generateRequestId(),
  message: '',
  code: 'INTERNAL_SERVER_ERROR'
})

// 生成请求ID
function generateRequestId() {
  return 'REQ-' + Date.now() + '-' + Math.random().toString(36).substr(2, 9).toUpperCase()
}

// 刷新页面
const refreshPage = () => {
  window.location.reload()
}

// 返回首页
const goHome = () => {
  router.push('/dashboard')
}

// 报告错误
const reportError = () => {
  // 这里可以实现错误报告功能
  // 比如打开邮件客户端或者显示反馈表单
  const subject = encodeURIComponent('服务器错误报告 - ' + errorDetails.value.requestId)
  const body = encodeURIComponent(`
错误详情:
- 时间: ${errorDetails.value.timestamp}
- 请求ID: ${errorDetails.value.requestId}
- 错误代码: ${errorDetails.value.code}
- 页面URL: ${window.location.href}
- 用户代理: ${navigator.userAgent}

请描述您在遇到这个错误之前的操作步骤:


`)
  
  const mailtoUrl = `mailto:support@example.com?subject=${subject}&body=${body}`
  window.location.href = mailtoUrl
  
  ElMessage.info('已为您打开邮件客户端，请发送错误报告')
}

// 组件挂载时的初始化
onMounted(() => {
  // 可以从路由参数或其他地方获取具体的错误信息
  const urlParams = new URLSearchParams(window.location.search)
  const errorMessage = urlParams.get('message')
  const errorCode = urlParams.get('code')
  
  if (errorMessage) {
    errorDetails.value.message = errorMessage
  }
  if (errorCode) {
    errorDetails.value.code = errorCode
  }
})
</script>

<style scoped>
.error-container {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: flex-start;
  background: linear-gradient(135deg, #f56565 0%, #e53e3e 100%);
  padding: 20px;
  overflow-y: auto;
}

.error-content {
  background: white;
  border-radius: 12px;
  padding: 60px 40px;
  text-align: center;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  margin-bottom: 30px;
  max-width: 600px;
  width: 100%;
}

.error-illustration {
  margin-bottom: 40px;
}

.error-icon {
  font-size: 80px;
  color: #f56c6c;
  margin-bottom: 20px;
}

.error-code {
  font-size: 120px;
  font-weight: 900;
  color: #e53e3e;
  line-height: 1;
  margin-bottom: 20px;
  text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.1);
}

.error-info {
  color: #333;
}

.error-title {
  font-size: 32px;
  font-weight: 600;
  margin: 0 0 20px 0;
  color: #303133;
}

.error-description {
  font-size: 16px;
  color: #606266;
  margin: 0 0 10px 0;
  line-height: 1.6;
}

.error-suggestion {
  font-size: 14px;
  color: #909399;
  margin: 0 0 30px 0;
  line-height: 1.6;
}

.error-details {
  margin: 20px 0 30px 0;
  text-align: left;
}

.error-detail-content {
  background: #f8f9fa;
  padding: 15px;
  border-radius: 4px;
  font-family: monospace;
  font-size: 13px;
  line-height: 1.5;
}

.error-detail-content p {
  margin: 5px 0;
  word-break: break-all;
}

.error-actions {
  display: flex;
  justify-content: center;
  gap: 15px;
  flex-wrap: wrap;
}

.solutions {
  background: white;
  border-radius: 12px;
  padding: 30px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  max-width: 800px;
  width: 100%;
  margin-bottom: 30px;
}

.solutions h3 {
  text-align: center;
  margin: 0 0 25px 0;
  color: #303133;
  font-size: 20px;
  font-weight: 600;
}

.solutions-list {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 20px;
}

.solution-item {
  display: flex;
  align-items: flex-start;
  padding: 20px;
  background: #f8f9fa;
  border-radius: 8px;
  border-left: 4px solid #409eff;
}

.solution-icon {
  font-size: 24px;
  color: #409eff;
  margin-right: 15px;
  margin-top: 5px;
  flex-shrink: 0;
}

.solution-content h4 {
  margin: 0 0 8px 0;
  color: #303133;
  font-size: 16px;
  font-weight: 600;
}

.solution-content p {
  margin: 0;
  color: #606266;
  font-size: 14px;
  line-height: 1.5;
}

.contact-info {
  background: white;
  border-radius: 12px;
  padding: 30px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  max-width: 600px;
  width: 100%;
  text-align: center;
}

.contact-info h3 {
  margin: 0 0 25px 0;
  color: #303133;
  font-size: 20px;
  font-weight: 600;
}

.contact-methods {
  display: flex;
  justify-content: center;
  gap: 30px;
  flex-wrap: wrap;
}

.contact-item {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #606266;
  font-size: 14px;
}

.contact-item .el-icon {
  color: #409eff;
  font-size: 16px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .error-container {
    padding: 15px;
  }
  
  .error-content {
    padding: 40px 20px;
  }
  
  .error-code {
    font-size: 80px;
  }
  
  .error-title {
    font-size: 24px;
  }
  
  .error-actions {
    flex-direction: column;
    align-items: center;
  }
  
  .error-actions .el-button {
    width: 200px;
  }
  
  .solutions {
    padding: 20px;
  }
  
  .solutions-list {
    grid-template-columns: 1fr;
    gap: 15px;
  }
  
  .solution-item {
    padding: 15px;
  }
  
  .contact-info {
    padding: 20px;
  }
  
  .contact-methods {
    flex-direction: column;
    gap: 15px;
  }
}

@media (max-width: 480px) {
  .error-code {
    font-size: 60px;
  }
  
  .error-title {
    font-size: 20px;
  }
  
  .solution-item {
    flex-direction: column;
    text-align: center;
  }
  
  .solution-icon {
    margin: 0 0 10px 0;
  }
}
</style>