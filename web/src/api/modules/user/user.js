import { http } from '../../request.js'
import { API_ENDPOINTS } from '../../config.js'

/**
 * User相关 API 服务
 */


// export async function userDetail(uid) {
//   return http.post('/api/user/detail', { uid })
// }
/**
 * 获取用户详情
 */
export const getUserDetail = async uid => http.post('/api/user/detail', { uid })

/**
 * 获取用户歌单列表
 * @param {string|number} uid 用户ID
 * @param {number} limit 返回数量，默认 30
 * @param {number} offset 偏移量，默认 0
 * @param {boolean} includeVideo 是否包含视频，默认 true
 */
export const getUserPlaylist = async ({
  uid,
  limit = 30,
  offset = 0,
  includeVideo = true
}) => {
  return http.get('/api/user/playlist', {
    uid,
    limit,
    offset,
    include_video: includeVideo
  })
}
