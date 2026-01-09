import { http, type ApiEnvelope, type ApiResult } from '../request'
import { SERVICE_ENDPOINTS } from '../config'

const USER = SERVICE_ENDPOINTS.USER

export interface Account {
  account_id: string
  nickname?: string
  avatar_url?: string
  status: 'active' | 'disabled' | 'banned' | string
}

export interface Session {
  session_id: string
  login_type?: string
  nickname?: string
  avatar_url?: string
  last_selected_at?: string
  is_current?: boolean
  is_valid?: boolean
  account?: Account
}

export interface CurrentUserData {
  account: Account
  session: Session
}

export interface SessionsListData {
  sessions: Session[]
  current_session_id: string
}

export const getCurrentUser = async (): Promise<ApiResult<ApiEnvelope<CurrentUserData>>> => {
  return http.get<ApiEnvelope<CurrentUserData>>(USER.CURRENT)
}

export const getUserList = async (params: Record<string, unknown> = {}): Promise<ApiResult<ApiEnvelope<unknown>>> => {
  return http.get<ApiEnvelope<unknown>>(USER.LIST, params)
}

export const switchSession = async (sessionId: string): Promise<ApiResult<ApiEnvelope<unknown>>> => {
  return http.post<ApiEnvelope<unknown>>(USER.SWITCH, { session_id: sessionId })
}

export const getSessionsList = async (): Promise<ApiResult<ApiEnvelope<SessionsListData>>> => {
  return http.get<ApiEnvelope<SessionsListData>>(USER.SESSIONS_LIST)
}

export const invalidateSession = async (sessionId: string): Promise<ApiResult<ApiEnvelope<unknown>>> => {
  return http.post<ApiEnvelope<unknown>>(USER.SESSION_INVALIDATE, { session_id: sessionId })
}

