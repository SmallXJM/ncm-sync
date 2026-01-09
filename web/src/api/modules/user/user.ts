import { http, type ApiEnvelope, type ApiResult } from '../../request'

export interface GetUserDetailParams {
  uid: string | number
}

export interface GetUserPlaylistParams {
  uid: string | number
  limit?: number
  offset?: number
  includeVideo?: boolean
}

export const getUserDetail = async (uid: string | number): Promise<ApiResult<ApiEnvelope<unknown>>> =>
  http.post<ApiEnvelope<unknown>>('/api/user/detail', { uid } satisfies GetUserDetailParams)

export const getUserPlaylist = async ({
  uid,
  limit = 30,
  offset = 0,
  includeVideo = true,
}: GetUserPlaylistParams): Promise<ApiResult<ApiEnvelope<unknown>>> => {
  return http.get<ApiEnvelope<unknown>>('/api/user/playlist', {
    uid,
    limit,
    offset,
    include_video: includeVideo,
  })
}

