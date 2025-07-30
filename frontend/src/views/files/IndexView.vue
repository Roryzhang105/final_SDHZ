<template>
  <div class="files-view">
    <el-card class="filter-card" shadow="hover">
      <template #header>
        <div class="card-header">
          <span>文件管理</span>
          <div class="header-actions">
            <el-upload
              :action="uploadUrl"
              :headers="uploadHeaders"
              :show-file-list="false"
              :before-upload="beforeUpload"
              :on-success="handleUploadSuccess"
              :on-error="handleUploadError"
              multiple
            >
              <el-button type="primary" :icon="Upload">
                上传文件
              </el-button>
            </el-upload>
            <el-button type="danger" :icon="Delete" :disabled="selectedFiles.length === 0" @click="handleBatchDelete">
              批量删除
            </el-button>
          </div>
        </div>
      </template>
      
      <el-form :inline="true" :model="filterForm" class="filter-form">
        <el-form-item label="文件名">
          <el-input 
            v-model="filterForm.filename" 
            placeholder="请输入文件名"
            clearable
            @keyup.enter="handleSearch"
          />
        </el-form-item>
        <el-form-item label="文件类型">
          <el-select v-model="filterForm.fileType" placeholder="请选择文件类型" clearable>
            <el-option label="图片" value="image" />
            <el-option label="文档" value="document" />
            <el-option label="压缩包" value="archive" />
            <el-option label="其他" value="other" />
          </el-select>
        </el-form-item>
        <el-form-item label="上传时间">
          <el-date-picker
            v-model="filterForm.dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :icon="Search" @click="handleSearch">搜索</el-button>
          <el-button :icon="Refresh" @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card class="table-card" shadow="hover">
      <el-table
        :data="tableData"
        :loading="loading"
        stripe
        border
        style="width: 100%"
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="55" />
        <el-table-column label="文件预览" width="100">
          <template #default="{ row }">
            <div class="file-preview">
              <el-image
                v-if="isImage(row.filename)"
                :src="row.file_url"
                :preview-src-list="[row.file_url]"
                fit="cover"
                class="preview-image"
                :lazy="true"
              />
              <el-icon v-else class="file-icon" :color="getFileTypeColor(row.filename)">
                <component :is="getFileTypeIcon(row.filename)" />
              </el-icon>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="filename" label="文件名" min-width="200">
          <template #default="{ row }">
            <div class="filename-cell">
              <span class="filename" :title="row.filename">{{ row.filename }}</span>
              <el-tag size="small" :type="getFileTypeTagType(row.filename)">
                {{ getFileExtension(row.filename) }}
              </el-tag>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="file_size" label="文件大小" width="120">
          <template #default="{ row }">
            {{ formatFileSize(row.file_size) }}
          </template>
        </el-table-column>
        <el-table-column prop="file_type" label="文件类型" width="100">
          <template #default="{ row }">
            <el-tag :type="getFileTypeTagType(row.filename)" size="small">
              {{ getFileTypeText(row.filename) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="upload_time" label="上传时间" width="160" />
        <el-table-column label="操作" width="250" fixed="right">
          <template #default="{ row }">
            <el-button
              type="primary"
              size="small"
              :icon="View"
              @click="handlePreview(row)"
            >
              预览
            </el-button>
            <el-button
              type="success"
              size="small"
              :icon="Download"
              @click="handleDownload(row)"
            >
              下载
            </el-button>
            <el-button
              type="warning"
              size="small"
              :icon="Edit"
              @click="handleRename(row)"
            >
              重命名
            </el-button>
            <el-button
              type="danger"
              size="small"
              :icon="Delete"
              @click="handleDelete(row)"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-container">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.size"
          :page-sizes="[10, 20, 50, 100]"
          :total="pagination.total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>

    <!-- 文件预览对话框 -->
    <el-dialog
      v-model="previewDialogVisible"
      :title="previewFile?.filename"
      width="80%"
      :before-close="handleClosePreview"
    >
      <div v-if="previewFile" class="preview-content">
        <!-- 图片预览 -->
        <div v-if="isImage(previewFile.filename)" class="image-preview">
          <el-image
            :src="previewFile.file_url"
            fit="contain"
            style="width: 100%; max-height: 600px;"
          />
        </div>
        
        <!-- 文本文件预览 -->
        <div v-else-if="isText(previewFile.filename)" class="text-preview">
          <el-input
            v-model="fileContent"
            type="textarea"
            :rows="20"
            readonly
            placeholder="正在加载文件内容..."
          />
        </div>
        
        <!-- 其他文件类型 -->
        <div v-else class="other-preview">
          <el-empty description="该文件类型不支持预览">
            <el-button type="primary" @click="handleDownload(previewFile)">
              下载文件
            </el-button>
          </el-empty>
        </div>
      </div>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="previewDialogVisible = false">关闭</el-button>
          <el-button type="primary" @click="handleDownload(previewFile)">
            下载文件
          </el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 重命名对话框 -->
    <el-dialog v-model="renameDialogVisible" title="重命名文件" width="400px">
      <el-form :model="renameForm" :rules="renameRules" ref="renameFormRef">
        <el-form-item label="文件名" prop="newName">
          <el-input v-model="renameForm.newName" placeholder="请输入新的文件名" />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="renameDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="handleConfirmRename">确定</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import {
  Upload,
  Delete,
  Search,
  Refresh,
  View,
  Download,
  Edit,
  Document,
  Picture,
  Folder,
  VideoPlay,
  Headphone
} from '@element-plus/icons-vue'
import { filesApi } from '@/api/files'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()

// 响应式数据
const loading = ref(false)
const tableData = ref([])
const selectedFiles = ref([])
const previewDialogVisible = ref(false)
const renameDialogVisible = ref(false)
const previewFile = ref(null)
const fileContent = ref('')

// 筛选表单
const filterForm = reactive({
  filename: '',
  fileType: '',
  dateRange: []
})

// 分页配置
const pagination = reactive({
  page: 1,
  size: 20,
  total: 0
})

// 重命名表单
const renameFormRef = ref<FormInstance>()
const renameForm = reactive({
  newName: '',
  currentFile: null
})

const renameRules: FormRules = {
  newName: [
    { required: true, message: '请输入文件名', trigger: 'blur' },
    { min: 1, max: 255, message: '文件名长度在 1 到 255 个字符', trigger: 'blur' }
  ]
}

// 上传配置
const uploadUrl = computed(() => `${import.meta.env.VITE_API_BASE_URL}/files/upload`)
const uploadHeaders = computed(() => ({
  'Authorization': `Bearer ${authStore.token}`
}))

// 获取文件列表
const fetchFiles = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      size: pagination.size,
      filename: filterForm.filename,
      file_type: filterForm.fileType,
      start_date: filterForm.dateRange?.[0],
      end_date: filterForm.dateRange?.[1]
    }
    
    const response = await filesApi.getList(params)
    tableData.value = response.data.items
    pagination.total = response.data.total
  } catch (error) {
    console.error('获取文件列表失败:', error)
    ElMessage.error('获取文件列表失败')
  } finally {
    loading.value = false
  }
}

// 判断是否为图片
const isImage = (filename: string) => {
  const imageExt = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg']
  return imageExt.some(ext => filename.toLowerCase().endsWith(ext))
}

// 判断是否为文本文件
const isText = (filename: string) => {
  const textExt = ['.txt', '.md', '.json', '.xml', '.html', '.css', '.js', '.ts', '.py', '.java', '.cpp', '.c']
  return textExt.some(ext => filename.toLowerCase().endsWith(ext))
}

// 获取文件扩展名
const getFileExtension = (filename: string) => {
  const ext = filename.split('.').pop()
  return ext ? ext.toUpperCase() : 'FILE'
}

// 获取文件类型图标
const getFileTypeIcon = (filename: string) => {
  if (isImage(filename)) return Picture
  if (filename.toLowerCase().includes('.doc') || filename.toLowerCase().includes('.pdf')) return Document
  if (filename.toLowerCase().includes('.mp4') || filename.toLowerCase().includes('.avi')) return VideoPlay
  if (filename.toLowerCase().includes('.mp3') || filename.toLowerCase().includes('.wav')) return Headphone
  return Folder
}

// 获取文件类型颜色
const getFileTypeColor = (filename: string) => {
  if (isImage(filename)) return '#67c23a'
  if (filename.toLowerCase().includes('.doc') || filename.toLowerCase().includes('.pdf')) return '#409eff'
  if (filename.toLowerCase().includes('.mp4') || filename.toLowerCase().includes('.avi')) return '#e6a23c'
  if (filename.toLowerCase().includes('.mp3') || filename.toLowerCase().includes('.wav')) return '#f56c6c'
  return '#909399'
}

// 获取文件类型标签类型
const getFileTypeTagType = (filename: string) => {
  if (isImage(filename)) return 'success'
  if (filename.toLowerCase().includes('.doc') || filename.toLowerCase().includes('.pdf')) return 'primary'
  if (filename.toLowerCase().includes('.mp4') || filename.toLowerCase().includes('.avi')) return 'warning'
  return 'info'
}

// 获取文件类型文本
const getFileTypeText = (filename: string) => {
  if (isImage(filename)) return '图片'
  if (filename.toLowerCase().includes('.doc') || filename.toLowerCase().includes('.pdf')) return '文档'
  if (filename.toLowerCase().includes('.mp4') || filename.toLowerCase().includes('.avi')) return '视频'
  if (filename.toLowerCase().includes('.mp3') || filename.toLowerCase().includes('.wav')) return '音频'
  if (filename.toLowerCase().includes('.zip') || filename.toLowerCase().includes('.rar')) return '压缩包'
  return '其他'
}

// 格式化文件大小
const formatFileSize = (size: number) => {
  if (!size) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB', 'TB']
  let index = 0
  while (size >= 1024 && index < units.length - 1) {
    size /= 1024
    index++
  }
  return `${size.toFixed(1)} ${units[index]}`
}

// 处理搜索
const handleSearch = () => {
  pagination.page = 1
  fetchFiles()
}

// 处理重置
const handleReset = () => {
  Object.assign(filterForm, {
    filename: '',
    fileType: '',
    dateRange: []
  })
  pagination.page = 1
  fetchFiles()
}

// 处理选择变化
const handleSelectionChange = (selection: any[]) => {
  selectedFiles.value = selection
}

// 上传前检查
const beforeUpload = (file: any) => {
  const maxSize = 50 * 1024 * 1024 // 50MB
  if (file.size > maxSize) {
    ElMessage.error('文件大小不能超过 50MB')
    return false
  }
  return true
}

// 上传成功
const handleUploadSuccess = (response: any) => {
  ElMessage.success('文件上传成功')
  fetchFiles()
}

// 上传失败
const handleUploadError = (error: any) => {
  console.error('上传失败:', error)
  ElMessage.error('文件上传失败')
}

// 处理预览
const handlePreview = async (row: any) => {
  previewFile.value = row
  previewDialogVisible.value = true
  
  // 如果是文本文件，加载内容
  if (isText(row.filename)) {
    try {
      const response = await filesApi.getContent(row.id)
      fileContent.value = response.data
    } catch (error) {
      console.error('加载文件内容失败:', error)
      fileContent.value = '加载文件内容失败'
    }
  }
}

// 处理下载
const handleDownload = async (row: any) => {
  try {
    const response = await filesApi.download(row.id)
    
    // 创建下载链接
    const blob = new Blob([response.data])
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = row.filename
    link.click()
    window.URL.revokeObjectURL(url)
    
    ElMessage.success('下载成功')
  } catch (error) {
    console.error('下载失败:', error)
    ElMessage.error('下载失败')
  }
}

// 处理重命名
const handleRename = (row: any) => {
  renameForm.newName = row.filename
  renameForm.currentFile = row
  renameDialogVisible.value = true
}

// 确认重命名
const handleConfirmRename = async () => {
  if (!renameFormRef.value) return
  
  try {
    await renameFormRef.value.validate()
    
    await filesApi.rename(renameForm.currentFile.id, { 
      new_name: renameForm.newName 
    })
    
    ElMessage.success('重命名成功')
    renameDialogVisible.value = false
    fetchFiles()
  } catch (error) {
    console.error('重命名失败:', error)
    ElMessage.error('重命名失败')
  }
}

// 处理删除
const handleDelete = async (row: any) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除文件 "${row.filename}" 吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await filesApi.delete(row.id)
    ElMessage.success('删除成功')
    fetchFiles()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除失败:', error)
      ElMessage.error('删除失败')
    }
  }
}

// 处理批量删除
const handleBatchDelete = async () => {
  if (selectedFiles.value.length === 0) {
    ElMessage.warning('请选择要删除的文件')
    return
  }
  
  try {
    await ElMessageBox.confirm(
      `确定要删除选中的 ${selectedFiles.value.length} 个文件吗？`,
      '确认批量删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    const ids = selectedFiles.value.map(file => file.id)
    await filesApi.batchDelete({ ids })
    
    ElMessage.success('批量删除成功')
    selectedFiles.value = []
    fetchFiles()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('批量删除失败:', error)
      ElMessage.error('批量删除失败')
    }
  }
}

// 处理分页大小变化
const handleSizeChange = (size: number) => {
  pagination.size = size
  pagination.page = 1
  fetchFiles()
}

// 处理当前页变化
const handleCurrentChange = (page: number) => {
  pagination.page = page
  fetchFiles()
}

// 关闭预览对话框
const handleClosePreview = () => {
  previewDialogVisible.value = false
  previewFile.value = null
  fileContent.value = ''
}

// 组件挂载时获取数据
onMounted(() => {
  fetchFiles()
})
</script>

<style scoped>
.files-view {
  padding: 0;
}

.filter-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.filter-form {
  margin: 0;
}

.table-card {
  margin-bottom: 20px;
}

.file-preview {
  display: flex;
  align-items: center;
  justify-content: center;
}

.preview-image {
  width: 60px;
  height: 60px;
  border-radius: 4px;
}

.file-icon {
  font-size: 32px;
}

.filename-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.filename {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.pagination-container {
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
}

.preview-content {
  padding: 20px 0;
}

.image-preview {
  text-align: center;
}

.text-preview {
  height: 500px;
}

.other-preview {
  text-align: center;
  padding: 50px 0;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .filter-form .el-form-item {
    margin-bottom: 15px;
  }
  
  .card-header {
    flex-direction: column;
    gap: 15px;
    align-items: stretch;
  }
  
  .header-actions {
    justify-content: center;
  }
  
  .el-table .el-table__cell {
    padding: 8px 4px;
  }
}

/* 上传样式覆盖 */
:deep(.el-upload) {
  display: inline-block;
}

:deep(.el-upload .el-button) {
  margin: 0;
}
</style>