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