export type ConfigValidationErrors = Record<string, string>

export interface DownloadSettingsDraft {
  cron_expr: string | null
  max_concurrent_downloads: number
  max_threads_per_download: number
  temp_downloads_dir: string
}

export interface TemplateSettingsDraft {
  filename: string
  music_dir_prefix_playlist: string
}

export interface NcmConfigDraft {
  download: DownloadSettingsDraft
  template: TemplateSettingsDraft
}

export type NcmConfigFieldRule =
  | { kind: 'cron' }
  | { kind: 'intRange'; min: number; max: number; label: string }
  | { kind: 'pathLike'; label: string }
  | { kind: 'templateString'; label: string }

export type NcmConfigFieldControl =
  | { type: 'cronToggle' }
  | { type: 'text'; placeholder?: string; mono?: boolean }
  | { type: 'intRange'; min: number; max: number }

export type NcmConfigVisibleWhen =
  | { path: string; operator: 'notNull' }
  | { path: string; operator: 'equals'; value: unknown }

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
        description: '启用后将按照 Cron 表达式自动执行下载任务。\n关闭后仅支持手动触发。',
        control: { type: 'cronToggle' },
      },
      {
        id: 'download.cron_expr',
        path: 'download.cron_expr',
        label: '定时设置',
        description:
          'Cron 表达式（[秒] 分 时 日 月 周）。\n例如：0 2 * * * 表示每天凌晨 2 点执行。',
        control: { type: 'text', placeholder: '例如：0 2 * * *', mono: true },
        rule: { kind: 'cron' },
        visibleWhen: { path: 'download.cron_expr', operator: 'notNull' },
      },
      {
        id: 'download.max_concurrent_downloads',
        path: 'download.max_concurrent_downloads',
        label: '最大并发下载数',
        description: '同时进行的下载任务数量（1 ~ 10）。\n数值过大可能导致网络拥堵或被封禁。',
        control: { type: 'intRange', min: 1, max: 10 },
        rule: { kind: 'intRange', min: 1, max: 10, label: '最大并发量' },
      },
      {
        id: 'download.max_threads_per_download',
        path: 'download.max_threads_per_download',
        label: '单任务线程数',
        description: '单个下载任务使用的最大线程数（1 ~ 10）。\n建议设置为 2-6 之间。',
        control: { type: 'intRange', min: 1, max: 10 },
        rule: { kind: 'intRange', min: 1, max: 10, label: '单任务最大线程数' },
      },
      {
        id: 'download.temp_downloads_dir',
        path: 'download.temp_downloads_dir',
        label: '临时下载目录',
        description: '下载过程中的临时文件存放位置。\n支持绝对路径或相对于运行目录的相对路径。',
        control: { type: 'text', placeholder: 'downloads' },
        rule: { kind: 'pathLike', label: '临时下载目录' },
      },
    ],
  },
  {
    id: 'template',
    title: '模板设置',
    description: '自定义文件命名和目录结构',
    fields: [
      {
        id: 'template.filename',
        path: 'template.filename',
        label: '文件名模板',
        description: '歌曲文件的命名格式。\n支持变量：{artist}, {title}, {album} 等。',
        control: { type: 'text', placeholder: '{artist} - {title}', mono: true },
        rule: { kind: 'templateString', label: '文件名模板' },
      },
      {
        id: 'template.music_dir_prefix_playlist',
        path: 'template.music_dir_prefix_playlist',
        label: '歌单目录前缀',
        description: '歌单下载时的目录层级结构。\n支持变量：{user_name}, {playlist_name}。',
        control: { type: 'text', placeholder: '歌单/{user_name}/{playlist_name}', mono: true },
        rule: { kind: 'templateString', label: '歌单目录前缀模板' },
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
