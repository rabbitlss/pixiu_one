import axios, { 
  AxiosInstance, 
  AxiosRequestConfig, 
  AxiosResponse, 
  AxiosError 
} from 'axios'
import { message } from 'antd'
import type { ApiResponse, ApiError } from '@/types/api'

// 创建 axios 实例
const createRequest = (): AxiosInstance => {
  const instance = axios.create({
    baseURL: import.meta.env.VITE_API_BASE_URL,
    timeout: 30000,
    headers: {
      'Content-Type': 'application/json',
    },
  })

  // 请求拦截器
  instance.interceptors.request.use(
    (config) => {
      // 添加 token（如果存在）
      const token = localStorage.getItem('token')
      if (token) {
        config.headers.Authorization = `Bearer ${token}`
      }

      // 添加请求 ID 用于追踪
      config.headers['X-Request-ID'] = generateRequestId()

      return config
    },
    (error: AxiosError) => {
      // Request error: error
      return Promise.reject(error)
    }
  )

  // 响应拦截器
  instance.interceptors.response.use(
    (response: AxiosResponse) => {
      const { data } = response

      // 处理直接返回数据的情况（如认证接口）
      if (!Object.prototype.hasOwnProperty.call(data, 'success')) {
        return response
      }

      // 检查业务状态码
      if (data.success === false) {
        const error: ApiError = {
          message: data.message || '请求失败',
          code: data.code,
        }
        handleBusinessError(error)
        return Promise.reject(error)
      }

      return response
    },
    (error: AxiosError<ApiResponse>) => {
      handleHttpError(error)
      return Promise.reject(error)
    }
  )

  return instance
}

// 生成请求 ID
const generateRequestId = (): string => {
  return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
}

// 处理 HTTP 错误
const handleHttpError = (error: AxiosError<ApiResponse>) => {
  const { response, code, message: errorMessage } = error

  if (code === 'ECONNABORTED') {
    message.error('请求超时，请检查网络连接')
    return
  }

  if (!response) {
    message.error('网络连接失败，请检查网络设置')
    return
  }

  const { status, data } = response

  switch (status) {
    case 400:
      message.error(data?.message || '请求参数错误')
      break
    case 401:
      message.error('登录已过期，请重新登录')
      // 清除本地 token 和用户信息
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      // 跳转到登录页面
      window.location.href = '/login'
      break
    case 403:
      message.error('没有权限访问该资源')
      break
    case 404:
      message.error('请求的资源不存在')
      break
    case 422:
      message.error(data?.message || '数据验证失败')
      break
    case 429:
      message.error('请求过于频繁，请稍后再试')
      break
    case 500:
      message.error('服务器内部错误')
      break
    case 502:
      message.error('网关错误')
      break
    case 503:
      message.error('服务暂时不可用')
      break
    default:
      message.error(data?.message || errorMessage || '请求失败')
  }
}

// 处理业务错误
const handleBusinessError = (error: ApiError) => {
  message.error(error.message)
}

// 创建请求实例
const request = createRequest()

// 导出请求方法
export const get = <T = any>(
  url: string, 
  config?: AxiosRequestConfig
): Promise<ApiResponse<T>> => {
  return request.get(url, config).then(res => res.data)
}

export const post = <T = any>(
  url: string, 
  data?: any, 
  config?: AxiosRequestConfig
): Promise<T> => {
  return request.post(url, data, config).then(res => res.data)
}

export const put = <T = any>(
  url: string, 
  data?: any, 
  config?: AxiosRequestConfig
): Promise<ApiResponse<T>> => {
  return request.put(url, data, config).then(res => res.data)
}

export const patch = <T = any>(
  url: string, 
  data?: any, 
  config?: AxiosRequestConfig
): Promise<ApiResponse<T>> => {
  return request.patch(url, data, config).then(res => res.data)
}

export const del = <T = any>(
  url: string, 
  config?: AxiosRequestConfig
): Promise<ApiResponse<T>> => {
  return request.delete(url, config).then(res => res.data)
}

export default request