export const API_CONFIG = {
  BASE_URL: '',
  TIMEOUT: 10000,
  DEFAULT_HEADERS: {
    'Content-Type': 'application/json',
  },
} as const

export const NCM_API = {
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
    AUTH: {
      QR_START: '/ncm/user/qr/start',
      QR_CHECK: '/ncm/user/qr/check',
      COOKIE_UPLOAD: '/ncm/user/cookie/upload',
      STATUS: '/ncm/user/status',
    },
  },
  MUSIC: {
    USER: {
      PLAYLIST_LIST: '/ncm/music/user/playlist',
    },
    SONG: {
      URLV1: '/ncm/music/song/url_v1',
      DETAIL: '/ncm/music/song/detail',
      LYRIC: '/ncm/music/song/lyric',
    },
    SEARCH: '/ncm/music/search',
    PLAYLIST: {
      DETAIL: '/ncm/music/playlist/detail',
    },
  },
  CONFIG: {
    GET: '/ncm/config',
    UPDATE: '/ncm/config',
  },
  DOWNLOAD: {
    CREATE_JOB: '/ncm/download/job/create',
    GET_JOB_LIST: '/ncm/download/job',
    UPDATE_JOB: '/ncm/download/job/update',
  },
} as const

