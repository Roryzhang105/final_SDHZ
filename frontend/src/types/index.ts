// 导出所有类型定义
export * from './api'

// 表格列配置类型
export interface TableColumn {
  prop: string
  label: string
  width?: string | number
  minWidth?: string | number
  fixed?: boolean | 'left' | 'right'
  sortable?: boolean
  formatter?: (row: any, column: any, cellValue: any, index: number) => string
}

// 表单验证规则类型
export interface FormRule {
  required?: boolean
  message?: string
  trigger?: string | string[]
  min?: number
  max?: number
  type?: string
  validator?: (rule: any, value: any, callback: any) => void
}

// 菜单项类型
export interface MenuItem {
  id: string
  title: string
  icon?: string
  path?: string
  children?: MenuItem[]
  hidden?: boolean
}

// 面包屑类型
export interface BreadcrumbItem {
  title: string
  to?: string
}

// 通用选项类型
export interface Option {
  label: string
  value: string | number
  disabled?: boolean
}

// 文件信息类型
export interface FileInfo {
  name: string
  size: number
  type: string
  url?: string
  raw?: File
}

// 加载状态类型
export interface LoadingState {
  loading: boolean
  error: string | null
  data: any
}

// 分页参数类型
export interface PaginationParams {
  page: number
  per_page: number
  total?: number
}

// 搜索参数类型
export interface SearchParams {
  keyword?: string
  status?: string
  date_from?: string
  date_to?: string
}

// 任务状态枚举
export enum TaskStatus {
  PENDING = 'pending',          // 待处理
  RECOGNIZING = 'recognizing',  // 识别中
  TRACKING = 'tracking',        // 查询物流中  
  DELIVERED = 'delivered',      // 已签收
  GENERATING = 'generating',    // 生成文档中
  COMPLETED = 'completed',      // 已完成
  FAILED = 'failed',           // 失败
  RETURNED = 'returned'        // 退签
}

// 任务进度接口
export interface TaskProgress {
  stage: string
  percentage: number
  description: string
  timestamp: string
}

// 任务接口
export interface Task {
  id: number
  task_id: string
  tracking_number?: string
  status: TaskStatus
  created_at: string
  updated_at: string
  completed_at?: string
  
  // 图片相关
  image_url?: string
  image_filename?: string
  image_size?: number
  
  // 识别结果
  qr_result?: string
  qr_code?: string  // 兼容旧字段
  qr_confidence?: number
  
  // 送达回证相关信息
  document_type?: string   // 文书类型（如"申请告知书"）
  case_number?: string     // 案号（如"沪松府复字（2025）第1283号"）
  receiver?: string        // 受送达人
  
  // 物流信息
  tracking_info?: {
    status: string
    location: string
    update_time: string
    timeline?: Array<{
      time: string
      location: string
      description: string
    }>
  }
  tracking_data?: {
    is_signed: boolean
    sign_time?: string
    traces: Array<{
      time: string
      context: string
      ftime: string
      areaCode?: string
      areaName?: string
      status: string
    }>
  }
  delivery_status?: string
  delivery_time?: string
  
  // 回证信息
  doc_title?: string
  sender?: string
  send_location?: string
  receiver?: string
  send_time?: string
  remarks?: string
  
  // 文件路径
  document_url?: string
  screenshot_url?: string
  
  // 错误信息
  error_message?: string
  error_code?: string
  
  // 进度信息
  progress?: TaskProgress[] | number
  current_stage?: string
  progress_percentage?: number
  
  // 扩展元数据
  extra_metadata?: {
    qr_label_url?: string
    [key: string]: any
  }
  
  // API响应属性
  success?: boolean
  message?: string
}

// 任务列表查询参数
export interface TaskListParams {
  page: number
  size: number
  tracking_number?: string
  case_number?: string
  document_type?: string
  receiver?: string
  status?: string
  sort_by?: 'created_asc' | 'created_desc' | 'updated_asc' | 'updated_desc' | 'status_asc' | 'status_desc' | 'case_number_asc' | 'case_number_desc'
  date_from?: string
  date_to?: string
}

// 任务列表响应
export interface TaskListResponse {
  success: boolean
  message?: string
  data: {
    items: Task[]
    total: number
    page: number
    size: number
    pages: number
  }
}

// 任务详情响应
export interface TaskDetailResponse {
  success: boolean
  message?: string
  data: Task
}

// 任务更新数据
export interface TaskUpdateData {
  doc_title?: string
  sender?: string
  send_location?: string
  receiver?: string
  send_time?: string
  remarks?: string
}

// 上传图片响应
export interface UploadImageResponse {
  success: boolean
  message?: string
  data?: {
    task_id: string
    image_url: string
    filename: string
    size: number
  }
}

// 生成回证响应
export interface GenerateReceiptResponse {
  success: boolean
  message?: string
  data?: {
    task_id: string
    document_url: string
    filename: string
    size: number
  }
}

// 任务统计
export interface TaskStats {
  total: number
  completed: number
  pending: number
  failed: number
  processing: number
}

// 活动记录
export interface Activity {
  id: string
  task_id: string
  description: string
  time: string
  type: 'success' | 'info' | 'warning' | 'error'
  details?: any
}

// 文件下载参数
export interface DownloadParams {
  task_id: string
  file_type: 'document' | 'screenshot' | 'image' | 'all'
}

// 批量操作参数
export interface BatchOperationParams {
  task_ids: string[]
  operation: 'delete' | 'retry' | 'download'
}

// 任务筛选器
export interface TaskFilter {
  status: TaskStatus[]
  date_range: [string, string] | null
  keyword: string
}

// 任务排序
export interface TaskSort {
  field: 'created_at' | 'updated_at' | 'status' | 'case_number'
  order: 'asc' | 'desc'
}

// 排序状态
export interface SortState {
  column: string | null
  order: 'asc' | 'desc' | null
}