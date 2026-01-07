// API 配置文件
export const API_CONFIG = {
  // 基础 URL，可以根据环境变量动态配置
  BASE_URL: import.meta.env.VITE_API_BASE_URL || '',

  // 请求超时时间
  TIMEOUT: 10000,

  // 默认请求头
  DEFAULT_HEADERS: {
    'Content-Type': 'application/json',
  }
}

// API 端点定义
export const API_ENDPOINTS = {
  // 用户相关
  USER: {
    DETAIL: '/api/user/detail',

  },

  // 音乐相关
  MUSIC: {
    SEARCH_ENHANCED: '/ncm/music/search/enhanced',
    PLAYLIST_ANALYZE: '/ncm/music/playlist/analyze',
    DOWNLOAD_PREPARE: '/ncm/music/download/prepare'
  },

  // 基础模块
  MODULES: {
    REGISTER_ANONYMOUS: '/api/anonimous/register_anonimous',
    SEARCH_HOT: '/api/search/search_hot',
    SEARCH: '/api/search/search'
  }
}

// API 端点定义
export const SERVICE_ENDPOINTS = {
  // 认证相关 (已合并到 USER)
  AUTH: {
    QR_START: '/ncm/user/qr/start',
    QR_CHECK: '/ncm/user/qr/check',
    COOKIE_UPLOAD: '/ncm/user/cookie/upload',
    STATUS: '/ncm/user/status'
  },

  // 用户相关
  USER: {
    CURRENT: '/ncm/user/current',
    LIST: '/ncm/user/list',
    SWITCH: '/ncm/user/switch',
    SESSIONS_LIST: '/ncm/user/sessions/list',
    SESSION_INVALIDATE: '/ncm/user/session/invalidate',
    // 认证功能
    QR_START: '/ncm/user/qr/start',
    QR_CHECK: '/ncm/user/qr/check',
    COOKIE_UPLOAD: '/ncm/user/cookie/upload',
    STATUS: '/ncm/user/status'
  },

  // 音乐相关
  MUSIC: {
    SEARCH_ENHANCED: '/ncm/music/search/enhanced',
    PLAYLIST_ANALYZE: '/ncm/music/playlist/analyze',
    DOWNLOAD_PREPARE: '/ncm/music/download/prepare'
  },

  // 基础模块
  MODULES: {
    REGISTER_ANONYMOUS: '/api/anonimous/register_anonimous',
    SEARCH_HOT: '/api/search/search_hot',
    SEARCH: '/api/search/search'
  }
}
