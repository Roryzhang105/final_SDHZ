<script setup lang="ts">
import { RouterView } from 'vue-router'
</script>

<template>
  <div id="app">
    <RouterView />
  </div>
</template>

<style>
/* 全局样式 */
* {
  box-sizing: border-box;
}

html,
body {
  margin: 0;
  padding: 0;
  height: 100%;
  font-family: 'Helvetica Neue', Helvetica, 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', '微软雅黑', Arial, sans-serif;
}

#app {
  height: 100vh;
  overflow: hidden;
}

/* Element Plus 样式覆盖 */
.el-button + .el-button {
  margin-left: 8px;
}

.el-form-item {
  margin-bottom: 18px;
}

/* 响应式表格 */
@media (max-width: 768px) {
  .el-table {
    font-size: 12px;
  }
  
  .el-table th,
  .el-table td {
    padding: 8px 0;
  }
}

/* 卡片间距 */
.el-card + .el-card {
  margin-top: 20px;
}

/* 自定义滚动条 */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-thumb {
  background-color: #dcdfe6;
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background-color: #c0c4cc;
}

::-webkit-scrollbar-track {
  background-color: #f5f7fa;
}

/* 工具提示样式 */
.tooltip {
  font-size: 12px;
  color: #909399;
}

/* 状态标签样式 */
.status-tag {
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 12px;
}

.status-success {
  background-color: #f0f9ff;
  color: #67c23a;
  border: 1px solid #e1f3d8;
}

.status-warning {
  background-color: #fdf6ec;
  color: #e6a23c;
  border: 1px solid #faecd8;
}

.status-danger {
  background-color: #fef0f0;
  color: #f56c6c;
  border: 1px solid #fde2e2;
}

.status-info {
  background-color: #f4f4f5;
  color: #909399;
  border: 1px solid #e9e9eb;
}
</style>
