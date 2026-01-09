import { API_CONFIG } from './config'

export type ApiSuccess<T> = {
  success: true
  data: T
  status: number
  headers: Headers
}

export type ApiFailure = {
  success: false
  error: string
  status: number
}

export type ApiResult<T> = ApiSuccess<T> | ApiFailure

export interface ApiEnvelope<T> {
  code: number
  message?: string
  data?: T
}

export interface RequestOptions {
  method?: string
  headers?: HeadersInit
  body?: unknown
  signal?: AbortSignal | null
}

function headersToRecord(headers?: HeadersInit): Record<string, string> {
  if (!headers) return {}
  if (headers instanceof Headers) {
    const result: Record<string, string> = {}
    headers.forEach((value, key) => {
      result[key] = value
    })
    return result
  }
  if (Array.isArray(headers)) {
    return Object.fromEntries(headers.map(([k, v]) => [k, String(v)]))
  }
  return Object.fromEntries(Object.entries(headers).map(([k, v]) => [k, String(v)]))
}

class HttpClient {
  private baseURL: string
  private timeout: number
  private defaultHeaders: Record<string, string>

  constructor() {
    this.baseURL = API_CONFIG.BASE_URL
    this.timeout = API_CONFIG.TIMEOUT
    this.defaultHeaders = API_CONFIG.DEFAULT_HEADERS
  }

  async request<T>(url: string, options: RequestOptions = {}): Promise<ApiResult<T>> {
    const headers = {
      ...this.defaultHeaders,
      ...headersToRecord(options.headers),
    }

    const config: RequestInit & { body?: BodyInit | null } = {
      method: options.method ?? 'GET',
      headers,
      signal: options.signal ?? undefined,
    }

    if (options.body !== undefined) {
      if (typeof options.body === 'string' || options.body instanceof FormData) {
        config.body = options.body as unknown as BodyInit
      } else if (options.body instanceof Blob || options.body instanceof ArrayBuffer) {
        config.body = options.body as unknown as BodyInit
      } else {
        config.body = JSON.stringify(options.body)
      }
    }

    const fullUrl = url.startsWith('http') ? url : `${this.baseURL}${url}`

    try {
      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), this.timeout)

      const response = await fetch(fullUrl, {
        ...config,
        signal: config.signal ?? controller.signal,
      })

      clearTimeout(timeoutId)

      if (!response.ok) {
        throw new Error(`HTTP Error: ${response.status} ${response.statusText}`)
      }

      const data = (await response.json()) as T

      return {
        success: true,
        data,
        status: response.status,
        headers: response.headers,
      }
    } catch (error: unknown) {
      const err = error instanceof Error ? error : new Error(String(error))
      const status =
        (error as { name?: string } | null)?.name === 'AbortError' ? 408 : 0

      return {
        success: false,
        error: err.message,
        status,
      }
    }
  }

  async get<T>(url: string, params: Record<string, unknown> = {}): Promise<ApiResult<T>> {
    const searchParams = new URLSearchParams()
    Object.entries(params).forEach(([key, value]) => {
      if (value !== null && value !== undefined && value !== '') {
        searchParams.append(key, String(value))
      }
    })

    const queryString = searchParams.toString()
    const fullUrl = queryString ? `${url}?${queryString}` : url

    return this.request<T>(fullUrl, { method: 'GET' })
  }

  async post<T>(url: string, data: unknown = {}): Promise<ApiResult<T>> {
    return this.request<T>(url, {
      method: 'POST',
      body: data,
    })
  }

  async put<T>(url: string, data: unknown = {}): Promise<ApiResult<T>> {
    return this.request<T>(url, {
      method: 'PUT',
      body: data,
    })
  }

  async delete<T>(url: string): Promise<ApiResult<T>> {
    return this.request<T>(url, { method: 'DELETE' })
  }
}

export const http = new HttpClient()

export const get = <T>(url: string, params?: Record<string, unknown>) => http.get<T>(url, params)
export const post = <T>(url: string, data?: unknown) => http.post<T>(url, data)
export const put = <T>(url: string, data?: unknown) => http.put<T>(url, data)
export const del = <T>(url: string) => http.delete<T>(url)

