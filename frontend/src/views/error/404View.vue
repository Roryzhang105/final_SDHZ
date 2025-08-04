<template>
  <div class="error-container">
    <div class="error-content">
      <div class="error-illustration">
        <el-icon class="error-icon">
          <WarningFilled />
        </el-icon>
        <div class="error-code">404</div>
      </div>
      
      <div class="error-info">
        <h1 class="error-title">页面不存在</h1>
        <p class="error-description">
          抱歉，您访问的页面不存在或已被删除。
        </p>
        <p class="error-suggestion">
          请检查网址是否正确，或者返回首页重新导航。
        </p>
        
        <div class="error-actions">
          <el-button type="primary" size="large" @click="goHome">
            <el-icon><House /></el-icon>
            返回首页
          </el-button>
          <el-button size="large" @click="goBack">
            <el-icon><Back /></el-icon>
            返回上页
          </el-button>
          <el-button type="success" size="large" @click="refreshPage">
            <el-icon><Refresh /></el-icon>
            刷新页面
          </el-button>
        </div>
      </div>
    </div>
    
    <!-- 常用链接 -->
    <div class="quick-links">
      <h3>快速导航</h3>
      <div class="links-grid">
        <router-link to="/dashboard" class="quick-link">
          <el-icon><HomeFilled /></el-icon>
          <span>仪表盘</span>
        </router-link>
        <router-link to="/delivery/generate" class="quick-link">
          <el-icon><Document /></el-icon>
          <span>上传图片</span>
        </router-link>
        <router-link to="/delivery/list" class="quick-link">
          <el-icon><Grid /></el-icon>
          <span>任务列表</span>
        </router-link>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import {
  WarningFilled,
  House,
  Back,
  Refresh,
  HomeFilled,
  Document,
  Grid
} from '@element-plus/icons-vue'

const router = useRouter()

// 返回首页
const goHome = () => {
  router.push('/app/dashboard')
}

// 返回上一页
const goBack = () => {
  window.history.length > 1 ? router.go(-1) : router.push('/dashboard')
}

// 刷新页面
const refreshPage = () => {
  window.location.reload()
}
</script>

<style scoped>
.error-container {
  width: 100vw;
  height: 100vh;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  margin: 0;
  padding: 20px;
  box-sizing: border-box;
}

.error-content {
  background: white;
  border-radius: 12px;
  padding: 60px 40px;
  text-align: center;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  margin-bottom: 40px;
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
  color: #409eff;
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
  margin: 0 0 40px 0;
  line-height: 1.6;
}

.error-actions {
  display: flex;
  justify-content: center;
  gap: 15px;
  flex-wrap: wrap;
}

.quick-links {
  background: white;
  border-radius: 12px;
  padding: 30px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  max-width: 600px;
  width: 100%;
}

.quick-links h3 {
  text-align: center;
  margin: 0 0 25px 0;
  color: #303133;
  font-size: 20px;
  font-weight: 600;
}

.links-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 20px;
}

.quick-link {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 20px 15px;
  background: #f8f9fa;
  border-radius: 8px;
  text-decoration: none;
  color: #606266;
  transition: all 0.3s ease;
  border: 2px solid transparent;
}

.quick-link:hover {
  background: #409eff;
  color: white;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.3);
  border-color: #409eff;
}

.quick-link .el-icon {
  font-size: 28px;
  margin-bottom: 8px;
}

.quick-link span {
  font-size: 14px;
  font-weight: 500;
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
  
  .quick-links {
    padding: 20px;
  }
  
  .links-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 15px;
  }
  
  .quick-link {
    padding: 15px 10px;
  }
  
  .quick-link .el-icon {
    font-size: 24px;
  }
  
  .quick-link span {
    font-size: 12px;
  }
}

@media (max-width: 480px) {
  .error-code {
    font-size: 60px;
  }
  
  .error-title {
    font-size: 20px;
  }
  
  .links-grid {
    grid-template-columns: 1fr;
  }
}
</style>