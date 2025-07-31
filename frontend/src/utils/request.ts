import axios, { type AxiosInstance, type AxiosResponse, type AxiosError } from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import router from '@/router'

// 创建axios实例
const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
console.log('🚀 API Base URL:', apiBaseUrl)
console.log('🔧 Environment variables:', {
  VITE_API_BASE_URL: import.meta.env.VITE_API_BASE_URL,
  MODE: import.meta.env.MODE,
  DEV: import.meta.env.DEV
})

const service: AxiosInstance = axios.create({
  baseURL: apiBaseUrl,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
service.interceptors.request.use(
  (config) => {
    const authStore = useAuthStore()
    
    // 添加认证token
    if (authStore.token) {
      config.headers.Authorization = `Bearer ${authStore.token}`
    }
    
    // 调试信息
    console.log('📤 Request:', {
      method: config.method?.toUpperCase(),
      url: config.url,
      baseURL: config.baseURL,
      fullURL: `${config.baseURL}${config.url}`,
      headers: config.headers,
      data: config.data
    })
    
    return config
  },
  (error: AxiosError) => {
    console.error('Request error:', error)
    return Promise.reject(error)
  }
)

// 响应拦截器
service.interceptors.response.use(
  (response: AxiosResponse) => {
    const res = response.data
    
    // 如果返回的状态码为非200，则判断为错误
    if (response.status !== 200) {
      ElMessage.error(res.message || '请求失败')
      return Promise.reject(new Error(res.message || '请求失败'))
    }
    
    return res
  },
  (error: AxiosError) => {
    console.error('📥 Response error:', error)
    console.error('📥 Error details:', {
      message: error.message,
      code: error.code,
      config: {
        method: error.config?.method,
        url: error.config?.url,
        baseURL: error.config?.baseURL,
        fullURL: error.config ? `${error.config.baseURL}${error.config.url}` : 'unknown'
      },
      response: error.response ? {
        status: error.response.status,
        statusText: error.response.statusText,
        data: error.response.data,
        headers: error.response.headers
      } : null,
      request: error.request ? 'Request was made but no response received' : null
    })
    
    let message = '网络错误'
    
    if (error.response) {
      const { status, data } = error.response
      
      switch (status) {
        case 400:
          message = (data as any)?.detail || '请求参数错误'
          break
        case 401:
          message = '认证失败，请重新登录'
          // 清除token并跳转到登录页
          const authStore = useAuthStore()
          authStore.logout()
          router.push('/login')
          break
        case 403:
          message = '权限不足'
          break
        case 404:
          message = '请求的资源不存在'
          break
        case 422:
          message = (data as any)?.detail || '数据验证失败'
          break
        case 500:
          message = '服务器内部错误'
          break
        default:
          message = (data as any)?.detail || `请求失败 (${status})`
      }
    } else if (error.code === 'ECONNABORTED') {
      message = '请求超时'
    } else if (error.message) {
      message = error.message
    }
    
    ElMessage.error(message)
    return Promise.reject(error)
  }
)

export default service