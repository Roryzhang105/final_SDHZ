import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi } from '@/api'
import type { User, LoginRequest, RegisterRequest } from '@/types'

export const useAuthStore = defineStore('auth', () => {
  // 状态
  const token = ref<string>('')
  const user = ref<User | null>(null)
  const loading = ref(false)

  // 计算属性
  const isAuthenticated = computed(() => !!token.value)
  const userInfo = computed(() => user.value)
  const isAdmin = computed(() => user.value?.is_superuser || false)

  // 检查token是否可能过期（简单的时间戳检查）
  const isTokenExpired = (tokenString?: string): boolean => {
    if (!tokenString) return true
    
    try {
      // 解析JWT token的payload部分
      const payload = JSON.parse(atob(tokenString.split('.')[1]))
      const currentTime = Math.floor(Date.now() / 1000)
      
      // 如果token有exp字段，检查是否过期
      if (payload.exp) {
        return payload.exp < currentTime
      }
      
      // 如果没有exp字段，假设token有效
      return false
    } catch (error) {
      console.error('Failed to parse token:', error)
      return true
    }
  }

  // 验证token有效性
  const validateToken = async (): Promise<boolean> => {
    if (!token.value) return false
    
    // 首先检查token是否在客户端看起来已过期
    if (isTokenExpired(token.value)) {
      console.log('Token appears to be expired')
      return false
    }
    
    try {
      // 尝试获取当前用户信息来验证token
      await getCurrentUser()
      return true
    } catch (error) {
      console.error('Token validation failed:', error)
      return false
    }
  }

  // 初始化：从本地存储恢复状态
  const initializeAuth = async () => {
    const storedToken = localStorage.getItem('token')
    const storedUser = localStorage.getItem('user')
    
    console.log('Initializing auth:', { storedToken: !!storedToken, storedUser: !!storedUser })
    
    if (storedToken) {
      // 检查存储的token是否可能过期
      if (isTokenExpired(storedToken)) {
        console.log('Stored token is expired, clearing auth state')
        localStorage.removeItem('token')
        localStorage.removeItem('user')
        return
      }
      
      token.value = storedToken
    }
    
    if (storedUser) {
      try {
        user.value = JSON.parse(storedUser)
        console.log('Restored user from localStorage:', user.value)
      } catch (error) {
        console.error('Failed to parse stored user data:', error)
        localStorage.removeItem('user')
      }
    }
    
    // 如果有token但没有用户信息，尝试获取用户信息验证token
    if (token.value && !user.value) {
      console.log('Have token but no user, validating token...')
      const isValid = await validateToken()
      if (!isValid) {
        console.log('Token validation failed, clearing auth state')
        token.value = ''
        localStorage.removeItem('token')
        localStorage.removeItem('user')
      }
    }
  }

  // 登录
  const login = async (loginData: LoginRequest) => {
    loading.value = true
    try {
      const response = await authApi.login(loginData)
      
      if (response.success && response.data) {
        token.value = response.data.access_token
        user.value = response.data.user
        
        // 保存到本地存储
        localStorage.setItem('token', response.data.access_token)
        localStorage.setItem('user', JSON.stringify(response.data.user))
        
        return response
      }
      
      throw new Error(response.message || '登录失败')
    } catch (error) {
      console.error('Login error:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  // 注册
  const register = async (registerData: RegisterRequest) => {
    loading.value = true
    try {
      const response = await authApi.register(registerData)
      return response
    } catch (error) {
      console.error('Register error:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  // 获取当前用户信息
  const getCurrentUser = async () => {
    try {
      const response = await authApi.getCurrentUser()
      if (response.success && response.data) {
        user.value = response.data
        localStorage.setItem('user', JSON.stringify(response.data))
      }
      return response
    } catch (error) {
      console.error('Get current user error:', error)
      throw error
    }
  }

  // 退出登录
  const logout = async () => {
    try {
      await authApi.logout()
    } catch (error) {
      console.error('Logout error:', error)
    } finally {
      // 清除状态和本地存储
      token.value = ''
      user.value = null
      localStorage.removeItem('token')
      localStorage.removeItem('user')
    }
  }

  // 刷新token
  const refreshToken = async () => {
    try {
      const response = await authApi.refreshToken()
      if (response.success && response.data) {
        token.value = response.data.access_token
        localStorage.setItem('token', response.data.access_token)
      }
      return response
    } catch (error) {
      console.error('Refresh token error:', error)
      // 刷新失败，清除认证状态
      logout()
      throw error
    }
  }

  return {
    // 状态
    token,
    user,
    loading,
    
    // 计算属性
    isAuthenticated,
    userInfo,
    isAdmin,
    
    // 方法
    initializeAuth,
    validateToken,
    isTokenExpired,
    login,
    register,
    getCurrentUser,
    logout,
    refreshToken
  }
}, {
  persist: false // 不使用pinia-plugin-persistedstate，手动处理持久化
})