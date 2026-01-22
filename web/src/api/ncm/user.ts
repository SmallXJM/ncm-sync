import { http, type ApiEnvelope, type ApiResult } from '../request'
import { NCM_API } from '../config'

// ==================== Interfaces ====================

export interface Account {
  account_id: string
  nickname?: string
  avatar_url?: string
  status: 'active' | 'disabled' | 'banned' | string
}

export interface Session {
  id: number
  account_id?: string // from list_sessions
  user_id?: string    // from current_session (SimpleSession)
  login_type: string
  has_cookie?: boolean
  is_valid?: boolean
  last_selected_at?: string
  nickname?: string
  avatar_url?: string
}

export interface UserProfile {
  nickname: string
  avatarUrl: string
  userId: number
  signature?: string
  gender?: number
  backgroundUrl?: string
}

export type QrLoginStatus = 'idle' | 'waiting_scan' | 'waiting_confirm' | 'success' | 'expired'

export interface QrLoginStartData {
  qr_key: string
  qr_url: string
  qr_img: string
  status: string
}

export interface QrLoginCheckData {
  status: QrLoginStatus
  message?: string
  cookie?: string
}

export interface LoginStatusData {
  profile?: UserProfile
  account?: unknown
  bindings?: unknown[]
}

// Backend returns the session object directly for current user
export type CurrentUserData = Session

// Backend returns an array of sessions
export type SessionsListData = Session[]

// ==================== API Functions ====================

// --- QR Login ---

/**
 * Start QR code login process
 * @returns QR key and image data
 */
export const startQrLogin = async (): Promise<ApiResult<ApiEnvelope<QrLoginStartData>>> => {
  return http.post<ApiEnvelope<QrLoginStartData>>(NCM_API.USER.QR.START)
}

/**
 * Check QR code login status
 * @param qrKey The unique key from startQrLogin
 * @returns Login status and cookie if successful
 */
export const checkQrLogin = async (qrKey: string): Promise<ApiResult<ApiEnvelope<QrLoginCheckData>>> => {
  return http.post<ApiEnvelope<QrLoginCheckData>>(NCM_API.USER.QR.CHECK, { qr_key: qrKey })
}

// --- User Status ---

/**
 * Get current login status
 * @returns Login status information
 */
export const getLoginStatus = async (): Promise<ApiResult<ApiEnvelope<LoginStatusData>>> => {
  return http.get<ApiEnvelope<LoginStatusData>>(NCM_API.USER.STATUS)
}

/**
 * Upload a raw cookie string to create a session
 * @param cookie The raw cookie string
 * @returns Result of the upload
 */
export const uploadSession = async (cookie: string): Promise<ApiResult<ApiEnvelope<unknown>>> => {
  return http.post<ApiEnvelope<unknown>>(NCM_API.USER.SESSION.UPLOAD, { cookie })
}

// --- Session Management ---

/**
 * Invalidate (delete) a session
 * @param id The session ID to invalidate
 */
export const invalidateSession = async (id: number): Promise<ApiResult<ApiEnvelope<unknown>>> => {
  return http.post<ApiEnvelope<unknown>>(NCM_API.USER.SESSION.INVALIDATE, { id })
}

/**
 * List all sessions
 * @returns List of all sessions
 */
export const listAllSessions = async (): Promise<ApiResult<ApiEnvelope<SessionsListData>>> => {
  return http.get<ApiEnvelope<SessionsListData>>(NCM_API.USER.SESSION.LIST)
}

/**
 * Switch current active session
 * @param id The session ID to switch to
 */
export const switchSession = async (id: number): Promise<ApiResult<ApiEnvelope<unknown>>> => {
  return http.post<ApiEnvelope<unknown>>(NCM_API.USER.SESSION.SWITCH, { id })
}

// --- User Information ---

/**
 * Get current account info (session data)
 * @returns Current session information
 */
export const getCurrentSession = async (): Promise<ApiResult<ApiEnvelope<CurrentUserData>>> => {
  return http.get<ApiEnvelope<CurrentUserData>>(NCM_API.USER.SESSION.CURRENT)
}

/**
 * Get full user profile
 * @returns User profile information
 */
export const getUserProfile = async (): Promise<ApiResult<ApiEnvelope<UserProfile>>> => {
  return http.get<ApiEnvelope<UserProfile>>(NCM_API.USER.PROFILE)
}
