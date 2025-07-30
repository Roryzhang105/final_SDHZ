// API响应基础类型
export interface ApiResponse<T = any> {
  success: boolean
  message: string
  data?: T
  error?: string
}

// 分页响应类型
export interface PaginatedResponse<T> {
  success: boolean
  message: string
  data: {
    items: T[]
    total: number
    page: number
    per_page: number
    pages: number
  }
}

// 用户相关类型
export interface User {
  id: number
  username: string
  email: string
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface LoginRequest {
  username: string
  password: string
}

export interface LoginResponse {
  access_token: string
  token_type: string
  user: User
}

export interface RegisterRequest {
  username: string
  email: string
  password: string
}

// 送达回证相关类型
export interface DeliveryReceipt {
  id: number
  tracking_number: string
  doc_title: string
  sender?: string
  send_time?: string
  send_location?: string
  receiver?: string
  status: string
  qr_code_path?: string
  barcode_path?: string
  receipt_file_path?: string
  tracking_screenshot_path?: string
  delivery_receipt_doc_path?: string
  created_at: string
  updated_at: string
}

export interface DeliveryReceiptGenerateRequest {
  tracking_number: string
  doc_title?: string
  sender?: string
  send_time?: string
  send_location?: string
  receiver?: string
}

export interface DeliveryReceiptGenerateResponse {
  tracking_number: string
  receipt_id: number
  doc_filename: string
  file_size: number
  download_url: string
}

// 物流跟踪相关类型
export interface TrackingInfo {
  id: number
  tracking_number: string
  company_code: string
  current_status: string
  is_signed: boolean
  sign_time?: string
  last_update: string
  traces: TrackingTrace[]
}

export interface TrackingTrace {
  time: string
  context: string
  ftime: string
  areaCode?: string
  areaName?: string
  status: string
}

// 二维码相关类型
export interface QRCodeGenerateRequest {
  data: string
  size?: number
  format?: 'png' | 'jpeg' | 'svg'
  error_correction?: 'L' | 'M' | 'Q' | 'H'
}

export interface QRCodeGenerateResponse {
  qr_code_path: string
  qr_code_filename: string
  file_size: number
  download_url: string
}

export interface QRCodeRecognizeResponse {
  success: boolean
  results: Array<{
    data: string
    type: string
    confidence: number
    bbox?: number[]
  }>
  image_path: string
  processing_time: number
}

// 文件上传相关类型
export interface FileUploadResponse {
  success: boolean
  message: string
  data: {
    file_id: string
    filename: string
    file_path: string
    file_size: number
    content_type: string
    download_url: string
  }
}

// 错误类型
export interface ApiError {
  detail: string
  status_code?: number
}