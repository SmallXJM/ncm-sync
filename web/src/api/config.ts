export const API_CONFIG = {
  BASE_URL: import.meta.env.VITE_API_BASE_URL || '',
  TIMEOUT: 10000,
  DEFAULT_HEADERS: {
    'Content-Type': 'application/json',
  },
} as const

export const API_ENDPOINTS = {
  USER: {
    DETAIL: '/api/user/detail',
  },
  MUSIC: {
    SEARCH_ENHANCED: '/ncm/music/search/enhanced',
    PLAYLIST_ANALYZE: '/ncm/music/playlist/analyze',
    DOWNLOAD_PREPARE: '/ncm/music/download/prepare',
  },
  MODULES: {
    REGISTER_ANONYMOUS: '/api/anonimous/register_anonimous',
    SEARCH_HOT: '/api/search/search_hot',
    SEARCH: '/api/search/search',
  },
} as const

export const SERVICE_ENDPOINTS = {
  AUTH: {
    QR_START: '/ncm/user/qr/start',
    QR_CHECK: '/ncm/user/qr/check',
    COOKIE_UPLOAD: '/ncm/user/cookie/upload',
    STATUS: '/ncm/user/status',
  },
  USER: {
    CURRENT: '/ncm/user/current',
    LIST: '/ncm/user/list',
    SWITCH: '/ncm/user/switch',
    SESSIONS_LIST: '/ncm/user/sessions/list',
    SESSION_INVALIDATE: '/ncm/user/session/invalidate',
    QR_START: '/ncm/user/qr/start',
    QR_CHECK: '/ncm/user/qr/check',
    COOKIE_UPLOAD: '/ncm/user/cookie/upload',
    STATUS: '/ncm/user/status',
  },
  MUSIC: {
    SEARCH_ENHANCED: '/ncm/music/search/enhanced',
    PLAYLIST_ANALYZE: '/ncm/music/playlist/analyze',
    DOWNLOAD_PREPARE: '/ncm/music/download/prepare',
  },
  CONFIG: {
    GET: '/ncm/config',
    UPDATE: '/ncm/config',
  },
  MODULES: {
    REGISTER_ANONYMOUS: '/api/anonimous/register_anonimous',
    SEARCH_HOT: '/api/search/search_hot',
    SEARCH: '/api/search/search',
  },
} as const

