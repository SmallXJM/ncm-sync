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

export interface NcmConfigDraft {
  download: DownloadSettingsDraft
  subscription: SubscriptionSettingsDraft
}

export type NcmConfigFieldRule =
  | { kind: 'cron' }
  | { kind: 'intRange'; min: number; max: number; label: string }
  | { kind: 'pathLike'; label: string }
  | { kind: 'templateString'; label: string }

export type NcmConfigFieldControl =
  | { type: 'cronToggle' }
  | { type: 'switch' }
  | { type: 'text'; placeholder?: string; mono?: boolean }
  | { type: 'intRange'; min: number; max: number }
  | { type: 'select'; options: { label: string; value: string }[] }

export type NcmConfigVisibleWhen =
  | { path: string; operator: 'notNull' }
  | { path: string; operator: 'equals'; value: string }

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
]

export function validateCronExpr(value: string | null): string | null {
  if (value === null) return null
  const trimmed = value.trim()
  if (!trimmed) return 'cron_expr 不能为空字符串（或设置为 null 禁用）'
  const parts = trimmed.split(/\s+/)
  if (parts.length !== 5 && parts.length !== 6) return 'cron_expr 需要 5 或 6 段（空格分隔）'
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

function getValueByPath(obj: unknown, path: string): unknown {
  let current: unknown = obj
  for (const part of path.split('.')) {
    if (!current || typeof current !== 'object') return undefined
    const record = current as Record<string, unknown>
    if (!(part in record)) return undefined
    current = record[part]
  }
  return current
}

function isVisibleByRule(draft: NcmConfigDraft, rule?: NcmConfigVisibleWhen): boolean {
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
  return validateTemplateString(value, rule.label)
}

export function validateNcmConfigDraft(draft: NcmConfigDraft): ConfigValidationErrors {
  const errors: ConfigValidationErrors = {}

  for (const group of NCM_CONFIG_UI_SCHEMA) {
    for (const field of group.fields) {
      if (!field.rule) continue
      if (!isVisibleByRule(draft, field.visibleWhen)) continue
      const value = getValueByPath(draft, field.path)
      const error = validateByRule(value, field.rule)
      if (error) errors[field.path] = error
    }
  }

  return errors
}
