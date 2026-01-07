// 统一的 API 入口文件
export { http, get, post, put, del } from './request.js'
export { API_CONFIG, API_ENDPOINTS, SERVICE_ENDPOINTS } from './config.js'

// 导出所有服务
import * as auth from './services/auth.js'
import * as user from './services/user.js'
import * as music from './services/music.js'
import * as login from './modules/user/login.js'

// 创建统一的 API 对象
const api = {
  login,
  auth,
  user,
  music,
}

// 默认导出
export default api