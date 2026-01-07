import { http } from '../request.js'
import { SERVICE_ENDPOINTS } from '../config.js'

/**
 * 用户相关 API 服务
 */

const USER = SERVICE_ENDPOINTS.USER

/**
 * 获取当前用户信息
 */
export const getCurrentUser = async () => {
  return http.get(USER.CURRENT)
}

/**
 * 获取用户列表
 */
export const getUserList = async (params = {}) => {
  return http.get(USER.LIST, params)
}

/**
 * 切换会话
 */
export const switchSession = async (sessionId) => {
  return http.post(USER.SWITCH, { session_id: sessionId })
}

/**
 * 获取会话列表
 */
export const getSessionsList = async () => {
  return http.get(USER.SESSIONS_LIST)
}

/**
 * 使会话失效
 */
export const invalidateSession = async (sessionId) => {
  return http.post(USER.SESSION_INVALIDATE, { session_id: sessionId })
}