import { http } from '../request.js'
import { SERVICE_ENDPOINTS } from '../config.js'

/**
 * 音乐相关 API 服务
 */

const MUSIC = SERVICE_ENDPOINTS.MUSIC
const MODULES = SERVICE_ENDPOINTS.MODULES

/**
 * 增强搜索
 */
export const enhancedSearch = async (params) => {
  const {
    keywords,
    search_type = 'song',
    limit = 30,
    include_details = false
  } = params

  return http.post(MUSIC.SEARCH_ENHANCED, {
    keywords,
    search_type,
    limit,
    include_details
  })
}

/**
 * 歌单分析
 */
export const analyzePlaylist = async (playlistId, includeSongDetails = false) => {
  return http.post(MUSIC.PLAYLIST_ANALYZE, {
    playlist_id: playlistId,
    include_song_details: includeSongDetails
  })
}

/**
 * 准备下载
 */
export const prepareDownload = async (songIds, quality = 'standard') => {
  return http.post(MUSIC.DOWNLOAD_PREPARE, {
    song_ids: songIds,
    quality
  })
}

/**
 * 基础搜索（使用 modules 接口）
 */
export const basicSearch = async (params) => {
  return http.get(MODULES.SEARCH, params)
}

/**
 * 获取热门搜索
 */
export const getHotSearch = async () => {
  return http.get(MODULES.SEARCH_HOT)
}