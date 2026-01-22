export const API_CONFIG = {
  BASE_URL: '',
  TIMEOUT: 10000,
  DEFAULT_HEADERS: {
    'Content-Type': 'application/json',
  },
} as const

// [2026-01-22 10:14:33,283] Controller: [POST] /ncm/user/qr/check -> AuthController.check_qr_login
// [2026-01-22 10:14:33,284] Controller: [GET, POST] /ncm/user/status -> AuthController.get_login_status
// [2026-01-22 10:14:33,285] Controller: [POST] /ncm/user/qr/start -> AuthController.start_qr_login
// [2026-01-22 10:14:33,286] Controller: [POST] /ncm/user/cookie/upload -> AuthController.upload_cookie
// [2026-01-22 10:14:33,286] Controller: [POST] /ncm/user/session/invalidate -> ManagementController.invalidate_session
// [2026-01-22 10:14:33,287] Controller: [GET] /ncm/user/sessions/list -> ManagementController.list_all_sessions
// [2026-01-22 10:14:33,287] Controller: [POST] /ncm/user/switch -> ManagementController.switch_session
// [2026-01-22 10:14:33,288] Controller: [GET] /ncm/user/current -> ProfileController.get_current_account_info
// [2026-01-22 10:14:33,289] Controller: [GET, POST] /ncm/user/profile -> ProfileController.get_user_profile

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
