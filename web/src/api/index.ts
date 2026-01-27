export { http, get, post, put, del } from './request'
export { API_CONFIG, NCM_API } from './config'

import * as user from './ncm/user'
import * as config from './ncm/config'
import * as download from './ncm/download'
import * as login from './modules/user/login'
import * as auth from './modules/auth'

import music from './ncm/music'

const api = {
  auth,
  login,
  user,
  music,
  config,
  download,
} as const

export type Api = typeof api
export default api
