import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/utils/api'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('token') || null)
  const user = ref(JSON.parse(localStorage.getItem('user') || 'null'))

  const isAuthenticated = computed(() => !!token.value)
  const username = computed(() => user.value?.username || '')

  async function login(username, password) {
    const formData = new FormData()
    formData.append('username', username)
    formData.append('password', password)
    
    const response = await api.post('/auth/login', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    
    token.value = response.data.access_token
    localStorage.setItem('token', response.data.access_token)
    
    await fetchUserInfo()
    
    return response.data
  }

  async function register(userData) {
    const response = await api.post('/auth/register', userData)
    return response.data
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

  function logout() {
    token.value = null
    user.value = null
    localStorage.removeItem('token')
    localStorage.removeItem('user')
  }

  return {
    token,
    user,
    isAuthenticated,
    username,
    login,
    register,
    fetchUserInfo,
    logout
  }
})
