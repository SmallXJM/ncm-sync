import { http, type ApiEnvelope, type ApiResult } from '../../request'

export interface LoginQrCheckParams {
  key: string
}

export interface LoginQrCreateParams {
  key: string
  qrimg: boolean
  platform: string
}

export const getLoginStatus = async (): Promise<ApiResult<ApiEnvelope<unknown>>> =>
  http.post<ApiEnvelope<unknown>>('/api/login/status', {})

export const getLoginQrKey = async (): Promise<ApiResult<ApiEnvelope<unknown>>> =>
  http.post<ApiEnvelope<unknown>>('/api/login/qr/key', {})

export const getLoginQrCheck = async (key: string): Promise<ApiResult<ApiEnvelope<unknown>>> =>
  http.post<ApiEnvelope<unknown>>('/api/login/qr/check', { key } satisfies LoginQrCheckParams)

export const getLoginQrCreate = async (
  params: LoginQrCreateParams,
): Promise<ApiResult<ApiEnvelope<unknown>>> =>
  http.post<ApiEnvelope<unknown>>('/api/login/qr/create', params)

