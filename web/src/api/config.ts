export const API_CONFIG = {
  BASE_URL: '',
  TIMEOUT: 10000,
  DEFAULT_HEADERS: {
    'Content-Type': 'application/json',
  },
} as const

export const NCM_API = {
  USER: {
    QR: {
      START: '/ncm/user/qr/start',
      CHECK: '/ncm/user/qr/check',
    },
    SESSION: {
      CURRENT: '/ncm/user/session/current',
      UPLOAD: '/ncm/user/session/upload',
      SWITCH: '/ncm/user/session/switch',
      INVALIDATE: '/ncm/user/session/invalidate',
      LIST: '/ncm/user/sessions/list',
    },
    STATUS: '/ncm/user/status',
    PROFILE: '/ncm/user/profile',
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
  DASHBOARD: {
    AGGREGATE: '/ncm/dashboard/aggregate',
  },
  DOWNLOAD: {
    CREATE_JOB: '/ncm/download/job/create',
    GET_JOB_LIST: '/ncm/download/job',
    UPDATE_JOB: '/ncm/download/job/update',
    DELETE_JOB: '/ncm/download/job/delete',
    TASK_LIST: '/ncm/download/task/list',
    TASK_RESET: '/ncm/download/task/reset',
    DAEMON_CONTROL: '/ncm/download/daemon/control',
  },
} as const
