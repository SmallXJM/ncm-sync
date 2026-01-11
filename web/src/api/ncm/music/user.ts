import { http, type ApiResult } from '../../request'
import { NCM_API } from '../../config'

const MUSIC = NCM_API.MUSIC

export interface GetUserPlaylistParams {
    uid: string | number
    limit?: number
    offset?: number
    includeVideo?: boolean
}

export interface GetUserPlaylistResult {
    code: number
    more: boolean
    playlist: Playlist[]
}

export interface Playlist {
  id: number
  name: string
  coverImgUrl: string
  coverImgId?: number
  coverImgId_str?: string
  trackCount: number
  playCount: number
  privacy: number
  description?: string
  subscribedCount?: number
  cloudTrackCount?: number
  ordered?: boolean
  newImported?: boolean
  highQuality?: boolean
  updateTime?: number
  trackUpdateTime?: number
  commentThreadId?: string
  specialType?: number
  createTime?: number
  userId?: number
  // creator 信息
  creator: {
    nickname: string
    userId: number
    avatarUrl?: string
    defaultAvatar?: boolean
    province?: number
    city?: number
    gender?: number
    signature?: string
    userType?: number
    vipType?: number
    djStatus?: number
    expertTags?: string[]
    anchor?: boolean
    backgroundUrl?: string
    avatarImgId?: number
    backgroundImgId?: number
  }
  // 可选扩展字段
  subscribers?: unknown[]
  subscribed?: boolean
  tracks?: unknown[] | null
  top?: boolean
  updateFrequency?: string | null
  titleImage?: number
  titleImageUrl?: string | null
  englishTitle?: string | null
  opRecommend?: boolean
  recommendInfo?: unknown | null
  anonimous?: boolean
  adType?: number
  tags?: string[]
  containsTracks?: boolean
  sharedUsers?: unknown[] | null
  shareStatus?: unknown | null
  copied?: boolean
}




export const getUserPlaylist = async ({
    uid,
    limit = 30,
    offset = 0,
    includeVideo = true,
}: GetUserPlaylistParams): Promise<ApiResult<GetUserPlaylistResult>> => {
    return http.post<GetUserPlaylistResult>(MUSIC.USER.PLAYLIST_LIST, {
        uid,
        limit,
        offset,
        include_video: includeVideo,
    })
}

