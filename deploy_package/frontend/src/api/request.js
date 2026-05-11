import axios from 'axios'
import { ElMessage } from 'element-plus'

const service = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api/v1/system',
  timeout: 10000,
})

service.interceptors.request.use((config) => {
  const token = localStorage.getItem('agv_token')
  if (token) {
    config.headers = config.headers || {}
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

service.interceptors.response.use(
  (response) => {
    const payload = response.data || {}
    if (typeof payload.code === 'number' && payload.code !== 100) {
      ElMessage.error(payload.msg || '请求失败')
      return Promise.reject(new Error(payload.msg || 'Request failed'))
    }
    return Object.prototype.hasOwnProperty.call(payload, 'result') ? payload.result : payload
  },
  (error) => {
    if (error?.response?.status === 401) {
      localStorage.removeItem('agv_token')
      if (window.location.pathname !== '/login') {
        window.location.href = `/login?redirect=${encodeURIComponent(window.location.pathname)}`
      }
    }
    ElMessage.error(error?.message || '网络异常，请稍后重试')
    return Promise.reject(error)
  },
)

export default service
