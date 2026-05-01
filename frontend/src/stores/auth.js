import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/utils/api'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('token') || null)
  const refreshToken = ref(localStorage.getItem('refreshToken') || null)
  const user = ref(JSON.parse(localStorage.getItem('user') || 'null'))

  const isAuthenticated = computed(() => !!token.value)
  const username = computed(() => user.value?.username || '')
  const isAdmin = computed(() => user.value?.role === 'admin')
  const userRole = computed(() => user.value?.role || 'user')

  async function login(username, password) {
    const formData = new FormData()
    formData.append('username', username)
    formData.append('password', password)
    
    const response = await api.post('/auth/login', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    
    token.value = response.data.access_token
    localStorage.setItem('token', response.data.access_token)
    
    if (response.data.refresh_token) {
      refreshToken.value = response.data.refresh_token
      localStorage.setItem('refreshToken', response.data.refresh_token)
    }
    
    await fetchUserInfo()
    
    return response.data
  }

  async function register(userData) {
    const response = await api.post('/auth/register', userData)
    return response.data
  }

  async function refreshAccessToken() {
    if (!refreshToken.value) {
      throw new Error('No refresh token available')
    }
    
    try {
      const response = await api.post('/auth/refresh', {
        refresh_token: refreshToken.value
      })
      
      token.value = response.data.access_token
      localStorage.setItem('token', response.data.access_token)
      
      return response.data
    } catch (error) {
      logout()
      throw error
    }
  }

  async function fetchUserInfo() {
    try {
      const response = await api.get('/auth/me')
      user.value = response.data
      localStorage.setItem('user', JSON.stringify(response.data))
    } catch (error) {
      console.error('获取用户信息失败:', error)
    }
  }

  async function changePassword(oldPassword, newPassword) {
    const response = await api.post('/auth/change-password', {
      old_password: oldPassword,
      new_password: newPassword
    })
    return response.data
  }

  async function updateUser(userData) {
    const response = await api.put('/auth/me', userData)
    user.value = response.data
    localStorage.setItem('user', JSON.stringify(response.data))
    return response.data
  }

  function logout() {
    token.value = null
    refreshToken.value = null
    user.value = null
    localStorage.removeItem('token')
    localStorage.removeItem('refreshToken')
    localStorage.removeItem('user')
  }

  return {
    token,
    refreshToken,
    user,
    isAuthenticated,
    username,
    isAdmin,
    userRole,
    login,
    register,
    refreshAccessToken,
    fetchUserInfo,
    changePassword,
    updateUser,
    logout
  }
})
