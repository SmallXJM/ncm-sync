import { http, type ApiEnvelope, type ApiResult } from '../../request'
import { NCM_API } from '../../config'

const MUSIC = NCM_API.MUSIC

export interface GetUserPlaylistParams {
  uid: string | number
  limit?: number
  offset?: number
  includeVideo?: boolean
}

export const getUserPlaylist = async ({
  uid,
  limit = 30,
  offset = 0,
  includeVideo = true,
}: GetUserPlaylistParams): Promise<ApiResult<ApiEnvelope<unknown>>> => {
  return http.get<ApiEnvelope<unknown>>(MUSIC.USER.PLAYLIST_LIST, {
    uid,
    limit,
    offset,
    include_video: includeVideo,
  })
}

