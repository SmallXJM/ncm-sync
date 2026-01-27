import { http, type ApiEnvelope, type ApiResult } from '../request'
import { NCM_API } from '../config'

const CONFIG = NCM_API.CONFIG

export interface DownloadSettings {
  cron_expr: string | null
  max_concurrent_downloads: number
  max_threads_per_download: number
  temp_downloads_dir: string
}

export interface SubscriptionSettings {
  target_quality: string
  embed_metadata: boolean
  embed_cover: boolean
  embed_lyrics: boolean
  filename: string
  music_dir_playlist: string
}

export interface AuthUser {
  username: string
  password?: string
  password_changed_at?: number
}

export interface AuthSettings {
  enabled: boolean
  access_token_expire_minutes: number
  user: AuthUser
  rotate_secret_key: boolean
  logout: boolean
}

export interface NcmConfig {
  download: DownloadSettings
  subscription: SubscriptionSettings
  auth: AuthSettings
}

export type UpdateConfigPayload = {
  download?: Partial<DownloadSettings>
  subscription?: Partial<SubscriptionSettings>
  auth?: Partial<AuthSettings>
}

export const getConfig = async (): Promise<ApiResult<ApiEnvelope<NcmConfig>>> => {
  return http.get<ApiEnvelope<NcmConfig>>(CONFIG.GET)
}

export const updateConfig = async (partialConfig: UpdateConfigPayload): Promise<ApiResult<ApiEnvelope<NcmConfig>>> => {
  return http.post<ApiEnvelope<NcmConfig>>(CONFIG.UPDATE, partialConfig)
}
