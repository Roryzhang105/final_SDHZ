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

  // 初始化：从本地存储恢复状态
  const initializeAuth = () => {
    const storedToken = localStorage.getItem('token')
    const storedUser = localStorage.getItem('user')
    
    if (storedToken) {
      token.value = storedToken
    }
    
    if (storedUser) {
      try {
        user.value = JSON.parse(storedUser)
      } catch (error) {
        console.error('Failed to parse stored user data:', error)
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
    
    // 方法
    initializeAuth,
    login,
    register,
    getCurrentUser,
    logout,
    refreshToken
  }
}, {
  persist: false // 不使用pinia-plugin-persistedstate，手动处理持久化
})