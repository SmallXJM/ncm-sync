
import { http, type ApiEnvelope, type ApiResult } from '../request'

export interface LoginParams {
  username: string
  password: string // SHA256 hash
}

export interface LoginResponse {
  token: string
}

export interface AuthConfig {
  enabled: boolean
}

export const getAuthConfig = async (): Promise<ApiResult<ApiEnvelope<AuthConfig>>> =>
  http.get<ApiEnvelope<AuthConfig>>('/api/auth/config')

export const login = async (params: LoginParams): Promise<ApiResult<ApiEnvelope<LoginResponse>>> =>
  http.post<ApiEnvelope<LoginResponse>>('/api/auth/login', params)

export const checkAuth = async (): Promise<ApiResult<ApiEnvelope<unknown>>> =>
  http.get<ApiEnvelope<unknown>>('/api/auth/check')
