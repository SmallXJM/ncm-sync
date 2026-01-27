import { } from '../api/ncm/config'

export type ConfigValidationErrors = Record<string, string>

export interface DownloadSettingsDraft {
  cron_expr: string | null
  max_concurrent_downloads: number
  max_threads_per_download: number
  temp_downloads_dir: string
}

export interface SubscriptionSettingsDraft {
  filename: string
  music_dir_playlist: string
}

export interface AuthUserDraft {
  id?: string
  username: string
  password?: string
}

export interface AuthSettingsDraft {
  enabled: boolean
  access_token_expire_minutes: number
  user: AuthUserDraft
  rotate_secret_key?: boolean
  logout?: boolean
}

export interface NcmConfigDraft {
  download: DownloadSettingsDraft
  subscription: SubscriptionSettingsDraft
  auth: AuthSettingsDraft
}

export type NcmConfigFieldRule =
  | { kind: 'cron' }
  | { kind: 'intRange'; min: number; max: number; label: string }
  | { kind: 'pathLike'; label: string }
  | { kind: 'templateString'; label: string }
  | { kind: 'string'; min: number; max: number; label: string; regex?: string; required?: boolean }

export type NcmConfigFieldControl =
  | { type: 'cronToggle' }
  | { type: 'switch'; warning?: string }
  | { type: 'text'; placeholder?: string; mono?: boolean }
  | { type: 'intRange'; min: number; max: number }
  | { type: 'select'; options: { label: string; value: string }[] }
  | { type: 'button'; buttonLabel: string; confirm?: {message: string; dirtyWarn?: string}; actionId?: string; variant?: 'primary' | 'secondary' | 'danger' }

export type NcmConfigVisibleWhen =
  | { path: string; operator: 'notNull' }
  | { path: string; operator: 'equals'; value: string | boolean }

export interface NcmConfigFieldSchema {
  id: string
  path: string
  label: string
  description?: string
  control: NcmConfigFieldControl
  rule?: NcmConfigFieldRule
  visibleWhen?: NcmConfigVisibleWhen
}

export interface NcmConfigGroupSchema {
  id: string
  title: string
  description?: string
  fields: NcmConfigFieldSchema[]
}

export const NCM_CONFIG_UI_SCHEMA: NcmConfigGroupSchema[] = [
  {
    id: 'download',
    title: '下载设置',
    description: '控制定时任务调度及并发下载性能',
    fields: [
      {
        id: 'download.cron_toggle',
        path: 'download.cron_expr',
        label: '定时任务调度',
        description: [
          '启用后将按照 Cron 表达式自动执行下载任务。',
          '关闭后仅支持手动触发。',
        ].join('\n'),
        control: { type: 'cronToggle' },
      },
      {
        id: 'download.cron_expr',
        path: 'download.cron_expr',
        label: '定时设置',
        description: [
          'Cron 表达式（[秒] 分 时 日 月 周）。',
          '例如：0 2 * * * 表示每天凌晨 2 点执行。',
        ].join('\n'),
        control: { type: 'text', placeholder: '例如：0 2 * * *', mono: true },
        rule: { kind: 'cron' },
        visibleWhen: { path: 'download.cron_expr', operator: 'notNull' },
      },
      {
        id: 'download.max_concurrent_downloads',
        path: 'download.max_concurrent_downloads',
        label: '最大并发下载数',
        description: [
          '同时进行的下载任务数量（1 ~ 10）。',
          '数值过大可能导致网络拥堵或被封禁。',
        ].join('\n'),
        control: { type: 'intRange', min: 1, max: 10 },
        rule: { kind: 'intRange', min: 1, max: 10, label: '最大并发量' },
      },
      {
        id: 'download.max_threads_per_download',
        path: 'download.max_threads_per_download',
        label: '单任务线程数',
        description: [
          '单个下载任务使用的最大线程数（1 ~ 10）。',
          '建议设置为 4。',
        ].join('\n'),
        control: { type: 'intRange', min: 1, max: 10 },
        rule: { kind: 'intRange', min: 1, max: 10, label: '单任务最大线程数' },
      },

    ],
  },
  {
    id: 'subscription',
    title: '订阅设置',
    description: '设置订阅时的默认设置',
    fields: [
      {
        id: 'subscription.target_quality',
        path: 'subscription.target_quality',
        label: '目标音质',
        description: '默认歌曲下载的目标音质。',
        //         <option value="jymaster">超清母带 (Jymaster)</option>
        // <option value="dolby">杜比全景声 (Dolby)</option>
        // <option value="sky">沉浸环绕声 (Sky)</option>
        // <option value="jyeffect">高清环绕声 (Jyeffect)</option>
        // <option value="hires">Hi-Res</option>
        // <option value="lossless">无损 (Lossless)</option>
        // <option value="exhigh">极高 (Exhigh)</option>
        // <option value="standard">标准 (Standard)</option>
        control: {
          type: 'select',
          options:
            [
              { label: '杜比全景声 (Dolby)', value: 'dolby' },
              { label: '超清母带 (Jymaster)', value: 'jymaster' },
              { label: '沉浸环绕声 (Sky)', value: 'sky' },
              { label: '高清环绕声 (Jyeffect)', value: 'jyeffect' },
              { label: '高解析度无损 (Hi-Res)', value: 'hires' },
              { label: '无损 (Lossless)', value: 'lossless' },
              { label: '极高 (Exhigh)', value: 'exhigh' },
              { label: '标准 (Standard)', value: 'standard' }
            ]
        },
        rule: { kind: 'templateString', label: '文件名模板' },
      },
      {
        id: 'subscription.embed_metadata',
        path: 'subscription.embed_metadata',
        label: '嵌入标签',
        description: [
          '嵌入音乐标签',
          '包含音乐基本数据，如艺术家、标题、专辑等基本信息。',
        ].join('\n'),
        control: { type: 'switch' },
      },
      {
        id: 'subscription.embed_cover',
        path: 'subscription.embed_cover',
        label: '嵌入封面',
        description: [
          '嵌入音乐专辑封面。',
        ].join('\n'),
        control: { type: 'switch' },
      },
      {
        id: 'subscription.embed_lyrics',
        path: 'subscription.embed_lyrics',
        label: '嵌入歌词',
        description: [
          '嵌入音乐同步歌词',
          '支持Potplayer，Navidrome等播放器。',
        ].join('\n'),
        control: { type: 'switch' },
      },
      {
        id: 'subscription.filename',
        path: 'subscription.filename',
        label: '文件名模板',
        description: [
          '同步时的音乐文件名模板。',
          '支持变量：{id}: 音乐ID, {title}: 音乐名, {artist}: 艺术家, {album}: 专辑, {quality}: 音质, {format}: 文件格式',
          '文件名示例：',
          '    {artist} - {title} ({quality}) -> 苏打绿 - 我好想你 (hires).flac',
        ].join('\n'),
        control: { type: 'text', placeholder: '{artist} - {title}', mono: true },
        rule: { kind: 'templateString', label: '文件名模板' },
      },
      {
        id: 'subscription.music_dir_playlist',
        path: 'subscription.music_dir_playlist',
        label: '歌单存储路径',
        description: [
          '歌单同步时的音乐文件存储路径。',
          '支持变量：{user_id}: 用户ID, {user_name}: 用户名, {playlist_id}: 歌单ID, {playlist_name}: 歌单名',
          '路径示例：',
          '    Mac/Linux: /home/downloads/歌单/{user_name}/{playlist_name}',
          '    Windows: C:\\Downloads\\歌单\\{user_name}\\{playlist_name}',
        ].join('\n'),
        control: { type: 'text', placeholder: '歌单/{user_name}/{playlist_name}', mono: true },
        rule: { kind: 'templateString', label: '存储路径模板' },
      },
    ],
  },
  {
    id: 'auth',
    title: '认证设置',
    description: 'WebUI 访问控制与认证',
    fields: [
      {
        id: 'auth.enabled',
        path: 'auth.enabled',
        label: '启用认证',
        description: [
          '是否启用 WebUI 登录验证。开启后需登录才能访问 WebUI。',
          '<span class="text-error">警告⚠：如果关闭验证，可能导致安全风险，请谨慎操作。</span>',
        ].join('\n'),
        control: { type: 'switch' },
      },
      {
        id: 'auth.logout',
        path: 'auth.logout',
        label: '退出登录',
        description: '点击按钮将立即清除当前会话并退出登录。',
        control: { 
          type: 'button', 
          buttonLabel: '退出登录', 
          confirm: {message: '确定要退出登录吗？', dirtyWarn: '\n<span class="text-warning">当前有未保存的更改，退出登录将会丢失更改。</span>'}, 
          actionId: 'logout',
          variant: 'danger'
        },
        visibleWhen: { path: 'auth.enabled', operator: 'equals', value: true }
      },
      {
        id: 'auth.access_token_expire_minutes',
        path: 'auth.access_token_expire_minutes',
        label: '会话有效期 (小时)',
        description: '登录会话保持时间。默认值：168小时 (7天)。',
        control: { type: 'intRange', min: 1, max: 720 },
        rule: { kind: 'intRange', min: 1, max: 720, label: '会话有效期' },
        visibleWhen: { path: 'auth.enabled', operator: 'equals', value: true }
      },
      {
        id: 'auth.user.username',
        path: 'auth.user.username',
        label: '登录用户名',
        description: [
          '登录时的用户名。如需修改，请输入新用户名。',
          '用户名长度必须在 3-20 个字符之间，且只能包含字母、数字和下划线。',
          '<span class="text-warning">注意：修改用户名后将会退出当前会话。</span>',
        ].join('\n'),
        control: { type: 'text', placeholder: '新用户名' },
        rule: { kind: 'string', min: 3, max: 20, label: '用户名', regex: '^[a-zA-Z0-9_]+$' },
        visibleWhen: { path: 'auth.enabled', operator: 'equals', value: true }
      },
      {
        id: 'auth.user.password',
        path: 'auth.user.password',
        label: '登录密码',
        description: [
          '登录时的密码。如需修改，请输入新密码。',
          '密码长度必须在 3-20 个字符之间，且只能包含字母、数字和特殊字符。',
          '<span class="text-warning">注意：修改密码后将会退出当前会话。</span>',
        ].join('\n'),
        control: { type: 'text', placeholder: '新密码' },
        rule: { kind: 'string', min: 3, max: 20, label: '密码', regex: '^[a-zA-Z0-9!@#$%^&*()_+\\-=\\[\\]{}|;:\'",.<>/?]+$', required: false },
        visibleWhen: { path: 'auth.enabled', operator: 'equals', value: true }
      },
      {
        id: 'auth.rotate_secret_key',
        path: 'auth.rotate_secret_key',
        label: '重置密钥',
        description: [
          '如果启用并应用保存，将会重置 API 签名密钥。',
          '<span class="text-warning">注意：如果签名密钥被重置，所有已登录用户将被强制下线。</span>',
        ].join('\n'),
        control: { type: 'switch', warning: '注意：如果签名密钥被重置，所有已登录用户将被强制下线。' },
        visibleWhen: { path: 'auth.enabled', operator: 'equals', value: true }
      }
    ]
  }
]

export function validateCronExpr(value: string | null): string | null {
  if (value === null) return null
  const trimmed = value.trim()
  if (!trimmed) return 'cron_expr 不能为空字符串（或设置为 null 禁用）'
  const parts = trimmed.split(/\s+/)
  if (parts.length !== 5 && parts.length !== 6) return 'cron_expr 需要 5 或 6 段（空格分隔）'

  // 基础数字格式校验
  // 简单的正则检查，允许 *, /, -, , 和数字
  // 这不是完美的 cron 校验，但能过滤掉明显的错误字符
  const illegalCharRegex = /[^\d*/\-,?]/g
  const errors = []

  for (let i = 0; i < parts.length; i++) {
    const part = parts[i]
    if (!part) continue

    const illegalChars = part.match(illegalCharRegex)
    if (!illegalChars) continue

    const unique = [...new Set(illegalChars)].join(', ')
    errors.push(`第 ${i + 1} 段包含非法字符: ${unique}`)
  }

  if (errors.length > 0) {
    return errors.join('\n')
  }


  return null
}

export function validateIntRange(
  value: unknown,
  options: { min: number; max: number; label: string },
): string | null {
  const num = typeof value === 'number' ? value : Number(value)
  if (!Number.isFinite(num)) return `${options.label} 必须是数字`
  if (!Number.isInteger(num)) return `${options.label} 必须是整数`
  if (num < options.min || num > options.max) {
    return `${options.label} 需要在 ${options.min} ~ ${options.max} 之间`
  }
  return null
}

export function validateString(
  value: unknown,
  options: { min: number; max: number; label: string; regex?: string; required?: boolean },
): string | null {
  const str = typeof value === 'string' ? value : String(value ?? '')
  if (!str.trim()) {
    if (options.required === false) return null
    return `${options.label} 不能为空`
  }
  if (str.length < options.min || str.length > options.max) {
    return `${options.label} 需要在 ${options.min} ~ ${options.max} 之间`
  }
  if (options.regex && !new RegExp(options.regex).test(str)) {
    return `${options.label} 格式错误`
  }
  return null
}



export function validateNonEmptyString(value: unknown, label: string): string | null {
  if (typeof value !== 'string') return `${label} 必须是字符串`
  if (!value.trim()) return `${label} 不能为空`
  return null
}

export function validatePathLike(value: unknown, label: string): string | null {
  const base = validateNonEmptyString(value, label)
  if (base) return base
  const str = String(value)
  if (/[\u0000\r\n]/.test(str)) return `${label} 不能包含换行或空字符`
  return null
}

export function validateTemplateString(value: unknown, label: string): string | null {
  const base = validateNonEmptyString(value, label)
  if (base) return base

  const str = String(value)
  let depth = 0
  for (const ch of str) {
    if (ch === '{') depth += 1
    if (ch === '}') depth -= 1
    if (depth < 0) return `${label} 存在未匹配的 }`
  }
  if (depth !== 0) return `${label} 存在未匹配的 {`
  return null
}

export function getValueByPath(obj: unknown, path: string): unknown {
  let current: unknown = obj
  for (const part of path.split('.')) {
    if (!current || typeof current !== 'object') return undefined
    const record = current as Record<string, unknown>
    if (!(part in record)) return undefined
    current = record[part]
  }
  return current
}

export function setValueByPath(obj: unknown, path: string, value: unknown): void {
  if (!obj || typeof obj !== 'object') return
  const parts = path.split('.')
  const last = parts.pop()
  if (!last) return

  let current = obj as Record<string, unknown>
  for (const part of parts) {
    const next = current[part]
    if (!next || typeof next !== 'object') return
    current = next as Record<string, unknown>
  }
  current[last] = value
}

export function getIntRangeMin(control: NcmConfigFieldSchema['control']): number {
  return control.type === 'intRange' ? control.min : 1
}

export function getIntRangeMax(control: NcmConfigFieldSchema['control']): number {
  return control.type === 'intRange' ? control.max : 1
}

export function deepClone<T>(value: T): T {
  return JSON.parse(JSON.stringify(value))
}

export function isVisibleByRule(draft: NcmConfigDraft, rule?: NcmConfigVisibleWhen): boolean {
  if (!rule) return true
  const value = getValueByPath(draft, rule.path)
  if (rule.operator === 'notNull') return value !== null
  return value === rule.value
}

function validateByRule(value: unknown, rule: NcmConfigFieldRule): string | null {
  if (rule.kind === 'cron') {
    const normalized =
      value === null ? null : typeof value === 'string' ? value : value === undefined ? '' : String(value)
    return validateCronExpr(normalized)
  }
  if (rule.kind === 'intRange') return validateIntRange(value, rule)
  if (rule.kind === 'pathLike') return validatePathLike(value, rule.label)
  if (rule.kind === 'string') return validateString(value, rule)
  if (rule.kind === 'templateString') return validateTemplateString(value, rule.label)
  return null
}

export interface ValidationContext {
  cronServerPreview?: string | null
  isCronBackendInvalid?: boolean
}

export function validateNcmConfigDraft(
  draft: NcmConfigDraft,
  context?: ValidationContext,
): ConfigValidationErrors {
  const errors: ConfigValidationErrors = {}

  for (const group of NCM_CONFIG_UI_SCHEMA) {
    for (const field of group.fields) {
      if (!field.rule) continue
      if (!isVisibleByRule(draft, field.visibleWhen)) continue
      const value = getValueByPath(draft, field.path)
      const error = validateByRule(value, field.rule)
      if (error) {
        errors[field.path] = error
      } else {
        // 额外的业务逻辑校验：当服务端返回无效时报错
        if (field.path === 'download.cron_expr' && typeof value === 'string' && value.trim()) {
          if (context?.isCronBackendInvalid) {
            errors[field.path] = '无有效运行时间'
          }
        }
      }
    }
  }

  return errors
}
