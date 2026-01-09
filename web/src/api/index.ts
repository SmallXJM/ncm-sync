export { http, get, post, put, del } from './request'
export { API_CONFIG, API_ENDPOINTS, SERVICE_ENDPOINTS } from './config'

import * as auth from './ncm/auth'
import * as user from './ncm/user'
import * as music from './ncm/music'
import * as config from './ncm/config'
import * as login from './modules/user/login'

const api = {
  login,
  auth,
  user,
  music,
  config,
} as const

export type Api = typeof api
export default api

