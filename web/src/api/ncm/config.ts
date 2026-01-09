import { http, type ApiEnvelope, type ApiResult } from '../request'
import { SERVICE_ENDPOINTS } from '../config'

const CONFIG = SERVICE_ENDPOINTS.CONFIG

export interface DownloadSettings {
  cron_expr: string | null
  max_concurrent_downloads: number
  max_threads_per_download: number
  temp_downloads_dir: string
}

export interface TemplateSettings {
  filename: string
  music_dir_prefix_playlist: string
}

export interface NcmConfig {
  download: DownloadSettings
  template: TemplateSettings
}

export type UpdateConfigPayload = {
  download?: Partial<DownloadSettings>
  template?: Partial<TemplateSettings>
}

export const getConfig = async (): Promise<ApiResult<ApiEnvelope<NcmConfig>>> => {
  return http.get<ApiEnvelope<NcmConfig>>(CONFIG.GET)
}

export const updateConfig = async (partialConfig: UpdateConfigPayload): Promise<ApiResult<ApiEnvelope<NcmConfig>>> => {
  return http.post<ApiEnvelope<NcmConfig>>(CONFIG.UPDATE, partialConfig)
}

