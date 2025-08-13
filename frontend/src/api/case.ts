import request from '@/utils/request'

// 案件相关类型定义
export interface CaseInfo {
  id: number
  case_number: string
  applicant: string
  respondent: string
  third_party?: string | null
  applicant_address: string
  respondent_address: string
  third_party_address?: string | null
  closure_date?: string | null
  status: string
  created_at: string
  updated_at: string
}

export interface CaseListParams {
  page: number
  size: number
  status?: string
}

export interface CaseSearchParams {
  q: string
  page: number
  size: number
}

export interface CaseListResponse {
  success: boolean
  message: string
  data: {
    cases: CaseInfo[]
    pagination: {
      page: number
      size: number
      total: number
      pages: number
    }
  }
}

export interface CaseImportResult {
  total_rows: number
  imported: number
  updated: number
  errors: string[]
  success_rate: number
}

export interface CaseImportResponse {
  success: boolean
  message: string
  data: CaseImportResult
}

export interface CaseStatsResponse {
  success: boolean
  message: string
  data: {
    total_cases: number
    this_month_cases: number
    closed_cases: number
    active_cases: number
    status_distribution: Record<string, number>
  }
}

export interface ApiResponse<T = any> {
  success: boolean
  message: string
  data: T
}

// 导入Excel文件
export const importCases = (file: File): Promise<CaseImportResponse> => {
  const formData = new FormData()
  formData.append('file', file)
  
  return request.post('/api/v1/cases/import', formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    },
    timeout: 120000 // Excel导入可能需要较长时间
  })
}

// 获取案件列表
export const getCaseList = (params: CaseListParams): Promise<CaseListResponse> => {
  return request.get('/api/v1/cases', { params })
}

// 搜索案件
export const searchCases = (params: CaseSearchParams): Promise<CaseListResponse> => {
  return request.get('/api/v1/cases/search', { params })
}

// 根据案号获取案件
export const getCaseByNumber = (caseNumber: string): Promise<ApiResponse<CaseInfo>> => {
  return request.get(`/api/v1/cases/${caseNumber}`)
}

// 创建案件
export const createCase = (data: Omit<CaseInfo, 'id' | 'created_at' | 'updated_at'>): Promise<ApiResponse<CaseInfo>> => {
  return request.post('/api/v1/cases', data)
}

// 更新案件
export const updateCase = (id: number, data: Partial<Omit<CaseInfo, 'id' | 'created_at' | 'updated_at'>>): Promise<ApiResponse<CaseInfo>> => {
  return request.put(`/api/v1/cases/${id}`, data)
}

// 删除案件
export const deleteCase = (id: number): Promise<ApiResponse<{ deleted_case_id: number }>> => {
  return request.delete(`/api/v1/cases/${id}`)
}

// 获取案件统计信息
export const getCaseStats = (): Promise<CaseStatsResponse> => {
  return request.get('/api/v1/cases/stats/summary')
}