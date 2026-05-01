import axios from 'axios'
import { ElMessage } from 'element-plus'
import router from '@/router'

let isRefreshing = false
let failedQueue = []

const processQueue = (error, token = null) => {
  failedQueue.forEach(prom => {
    if (error) {
      prom.reject(error)
    } else {
      prom.resolve(token)
    }
  })
  failedQueue = []
}

const api = axios.create({
  baseURL: '/api',
  timeout: 60000,
  headers: {
    'Content-Type': 'application/json'
  }
})

api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

api.interceptors.response.use(
  (response) => {
    return response
  },
  async (error) => {
    const originalRequest = error.config

    if (error.response) {
      switch (error.response.status) {
        case 401:
          if (!originalRequest._retry) {
            if (isRefreshing) {
              return new Promise((resolve, reject) => {
                failedQueue.push({ resolve, reject })
              }).then(token => {
                originalRequest.headers.Authorization = `Bearer ${token}`
                return api(originalRequest)
              }).catch(err => {
                return Promise.reject(err)
              })
            }

            originalRequest._retry = true
            isRefreshing = true

            const refreshToken = localStorage.getItem('refreshToken')
            
            if (refreshToken) {
              try {
                const response = await api.post('/auth/refresh', {
                  refresh_token: refreshToken
                })
                
                const newToken = response.data.access_token
                localStorage.setItem('token', newToken)
                
                processQueue(null, newToken)
                
                originalRequest.headers.Authorization = `Bearer ${newToken}`
                return api(originalRequest)
              } catch (refreshError) {
                processQueue(refreshError, null)
                ElMessage.error('登录已过期，请重新登录')
                clearAuthData()
                router.push('/login')
                return Promise.reject(refreshError)
              } finally {
                isRefreshing = false
              }
            } else {
              ElMessage.error('登录已过期，请重新登录')
              clearAuthData()
              router.push('/login')
            }
          }
          break
        case 403:
          ElMessage.error('没有权限执行此操作')
          break
        case 404:
          ElMessage.error('请求的资源不存在')
          break
        case 500:
          ElMessage.error('服务器内部错误')
          break
        default:
          if (error.response.data && error.response.data.detail) {
            ElMessage.error(error.response.data.detail)
          } else {
            ElMessage.error('请求失败')
          }
      }
    } else {
      ElMessage.error('网络连接失败，请检查网络')
    }
    return Promise.reject(error)
  }
)

function clearAuthData() {
  localStorage.removeItem('token')
  localStorage.removeItem('refreshToken')
  localStorage.removeItem('user')
}

export default api
