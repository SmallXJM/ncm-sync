import { http } from '../request.js'
import { SERVICE_ENDPOINTS } from '../config.js'

/**
 * 认证相关 API 服务
 */

const AUTH = SERVICE_ENDPOINTS.AUTH

/**
 * 开始二维码登录
 */
export const startQRLogin = async () => {
  return http.post(AUTH.QR_START)
}

/**
 * 检查二维码登录状态
 */
export const checkQRLogin = async (qrKey) => {
  return http.post(AUTH.QR_CHECK, { qr_key: qrKey })
}

/**
 * Cookie 登录
 */
export const loginWithCookie = async (cookie) => {
  return http.post(AUTH.COOKIE_UPLOAD, { cookie })
}

/**
 * 检查登录状态
 */
export const checkStatus = async () => {
  return http.post(AUTH.STATUS)
}
