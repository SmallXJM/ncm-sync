import { http, type ApiEnvelope, type ApiResult } from '../request'
import { SERVICE_ENDPOINTS } from '../config'

const MUSIC = SERVICE_ENDPOINTS.MUSIC
const MODULES = SERVICE_ENDPOINTS.MODULES

export interface EnhancedSearchParams {
  keywords: string
  search_type?: string
  limit?: number
  include_details?: boolean
}

export const enhancedSearch = async (params: EnhancedSearchParams): Promise<ApiResult<ApiEnvelope<unknown>>> => {
  const { keywords, search_type = 'song', limit = 30, include_details = false } = params
  return http.post<ApiEnvelope<unknown>>(MUSIC.SEARCH_ENHANCED, {
    keywords,
    search_type,
    limit,
    include_details,
  })
}

export const analyzePlaylist = async (
  playlistId: string | number,
  includeSongDetails = false,
): Promise<ApiResult<ApiEnvelope<unknown>>> => {
  return http.post<ApiEnvelope<unknown>>(MUSIC.PLAYLIST_ANALYZE, {
    playlist_id: playlistId,
    include_song_details: includeSongDetails,
  })
}

export const prepareDownload = async (
  songIds: Array<string | number>,
  quality: string = 'standard',
): Promise<ApiResult<ApiEnvelope<unknown>>> => {
  return http.post<ApiEnvelope<unknown>>(MUSIC.DOWNLOAD_PREPARE, {
    song_ids: songIds,
    quality,
  })
}

export const basicSearch = async (params: Record<string, unknown>): Promise<ApiResult<ApiEnvelope<unknown>>> => {
  return http.get<ApiEnvelope<unknown>>(MODULES.SEARCH, params)
}

export const getHotSearch = async (): Promise<ApiResult<ApiEnvelope<unknown>>> => {
  return http.get<ApiEnvelope<unknown>>(MODULES.SEARCH_HOT)
}

