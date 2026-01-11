import { http, type ApiEnvelope, type ApiResult } from '../request'
import { NCM_API } from '../config'

const AUTH = NCM_API.USER.AUTH

export type QrLoginStatus = 'idle' | 'waiting_scan' | 'waiting_confirm' | 'success' | 'expired'

export interface StartQrLoginData {
  qr_key: string
  qr_img: string
}

export interface CheckQrLoginData {
  status: QrLoginStatus
  message?: string
}

export const startQRLogin = async (): Promise<ApiResult<ApiEnvelope<StartQrLoginData>>> => {
  return http.post<ApiEnvelope<StartQrLoginData>>(AUTH.QR_START)
}

export const checkQRLogin = async (qrKey: string): Promise<ApiResult<ApiEnvelope<CheckQrLoginData>>> => {
  return http.post<ApiEnvelope<CheckQrLoginData>>(AUTH.QR_CHECK, { qr_key: qrKey })
}

export const loginWithCookie = async (cookie: string): Promise<ApiResult<ApiEnvelope<unknown>>> => {
  return http.post<ApiEnvelope<unknown>>(AUTH.COOKIE_UPLOAD, { cookie })
}

export const checkStatus = async (): Promise<ApiResult<ApiEnvelope<unknown>>> => {
  return http.post<ApiEnvelope<unknown>>(AUTH.STATUS)
}

