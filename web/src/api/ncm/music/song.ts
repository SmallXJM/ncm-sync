import { http, type ApiEnvelope, type ApiResult } from '../../request'
import { NCM_API } from '../../config'

const SONG = NCM_API.MUSIC.SONG

export interface SongDetail {
  id: number
  name: string
  ar: { id: number; name: string }[]
  al: { id: number; name: string; picUrl: string }
  dt: number // duration
  // ... other fields as needed
}

export interface SongLyric {
  lrc?: { lyric: string }
  klyric?: { lyric: string }
  tlyric?: { lyric: string }
}

export const getSongDetail = async (ids: string | number | (string | number)[]): Promise<ApiResult<ApiEnvelope<{ songs: SongDetail[] }>>> => {
  const idsStr = Array.isArray(ids) ? ids.join(',') : String(ids)
  return http.get<ApiEnvelope<{ songs: SongDetail[] }>>(SONG.DETAIL, { ids: idsStr })
}

export const getSongLyric = async (id: string | number): Promise<ApiResult<ApiEnvelope<SongLyric>>> => {
  return http.get<ApiEnvelope<SongLyric>>(SONG.LYRIC, { id })
}
