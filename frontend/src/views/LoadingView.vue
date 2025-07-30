<template>
  <div class="loading-container">
    <div class="loading-content">
      <el-icon class="loading-icon" size="48">
        <Loading />
      </el-icon>
      <p class="loading-text">正在加载...</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Loading } from '@element-plus/icons-vue'
</script>

<style scoped>
.loading-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  background-color: #f5f7fa;
}

.loading-content {
  text-align: center;
}

.loading-icon {
  color: #409eff;
  animation: rotate 2s linear infinite;
}

.loading-text {
  margin-top: 16px;
  color: #606266;
  font-size: 14px;
}

@keyframes rotate {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}
</style>