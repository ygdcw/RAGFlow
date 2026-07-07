import axios from 'axios'

const request = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
})

// 请求拦截器：自动带 token
request.interceptors.request.use((config) => {
  const stored = localStorage.getItem('user')
  if (stored) {
    const user: User = JSON.parse(stored)
    config.headers.Authorization = `Bearer ${user.token}`
  }
  return config
})

// 响应拦截器
request.interceptors.response.use(
  (response) => {
    const { code, data, message } = response.data
    if (code === 200) return data
    return Promise.reject(new Error(message || '请求失败'))
  },
(error) => {
    if (error.response?.status === 401) {
      const url = error.config?.url || ''
      // 登录接口返回 401 → 返回友好错误提示，不跳转
      if (url.includes('/auth/login')) {
        return Promise.reject(new Error('用户名或密码错误'))
      }
      // /auth/me 返回 401 → 清除登录状态并跳转
      if (url.includes('/auth/me')) {
        localStorage.removeItem('user')
        if (window.location.pathname !== '/login') {
          window.location.href = '/login'
        }
        return Promise.reject(new Error('登录已过期'))
      }
    }
    if (error.response?.status === 413) {
      return Promise.reject(new Error('文件过大'))
    }
    if (error.code === 'ERR_NETWORK') {
      return Promise.reject(new Error('网络连接失败'))
    }
    return Promise.reject(error)
  }
)

export default request