import { API_CONFIG } from './config.js'

/**
 * HTTP 请求工具类
 */
class HttpClient {
  constructor() {
    this.baseURL = API_CONFIG.BASE_URL
    this.timeout = API_CONFIG.TIMEOUT
    this.defaultHeaders = API_CONFIG.DEFAULT_HEADERS
  }

  /**
   * 通用请求方法
   */
  async request(url, options = {}) {
    const config = {
      method: 'GET',
      headers: { ...this.defaultHeaders },
      ...options
    }

    // 处理请求体
    if (config.body && typeof config.body === 'object') {
      config.body = JSON.stringify(config.body)
    }

    // 创建完整 URL
    const fullUrl = url.startsWith('http') ? url : `${this.baseURL}${url}`

    try {
      // 添加超时控制
      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), this.timeout)

      const response = await fetch(fullUrl, {
        ...config,
        signal: controller.signal
      })

      clearTimeout(timeoutId)

      // 检查响应状态
      if (!response.ok) {
        throw new Error(`HTTP Error: ${response.status} ${response.statusText}`)
      }

      // 解析 JSON 响应
      const data = await response.json()
      
      return {
        success: true,
        data,
        status: response.status,
        headers: response.headers
      }
    } catch (error) {
      console.error('Request failed:', error)
      
      return {
        success: false,
        error: error.message,
        status: error.name === 'AbortError' ? 408 : 0
      }
    }
  }

  /**
   * GET 请求
   */
  async get(url, params = {}) {
    const searchParams = new URLSearchParams()
    Object.entries(params).forEach(([key, value]) => {
      if (value !== null && value !== undefined && value !== '') {
        searchParams.append(key, value)
      }
    })
    
    const queryString = searchParams.toString()
    const fullUrl = queryString ? `${url}?${queryString}` : url
    
    return this.request(fullUrl, { method: 'GET' })
  }

  /**
   * POST 请求
   */
  async post(url, data = {}) {
    return this.request(url, {
      method: 'POST',
      body: data
    })
  }

  /**
   * PUT 请求
   */
  async put(url, data = {}) {
    return this.request(url, {
      method: 'PUT',
      body: data
    })
  }

  /**
   * DELETE 请求
   */
  async delete(url) {
    return this.request(url, { method: 'DELETE' })
  }
}

// 创建全局实例
export const http = new HttpClient()

// 导出请求方法的简化版本
export const get = (url, params) => http.get(url, params)
export const post = (url, data) => http.post(url, data)
export const put = (url, data) => http.put(url, data)
export const del = (url) => http.delete(url)