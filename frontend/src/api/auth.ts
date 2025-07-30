import request from '@/utils/request'
import type { 
  LoginRequest, 
  LoginResponse, 
  RegisterRequest, 
  ApiResponse,
  User
} from '@/types'

export const authApi = {
  // 用户登录
  login(data: LoginRequest): Promise<ApiResponse<LoginResponse>> {
    return request.post('/api/v1/auth/login', data)
  },

  // 用户注册
  register(data: RegisterRequest): Promise<ApiResponse<User>> {
    return request.post('/api/v1/auth/register', data)
  },

  // 获取当前用户信息
  getCurrentUser(): Promise<ApiResponse<User>> {
    return request.get('/api/v1/auth/me')
  },

  // 刷新token
  refreshToken(): Promise<ApiResponse<LoginResponse>> {
    return request.post('/api/v1/auth/refresh')
  },

  // 退出登录
  logout(): Promise<ApiResponse> {
    return request.post('/api/v1/auth/logout')
  }
}