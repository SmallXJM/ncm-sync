<template>
  <div class="page">
    <main>
      <div class="container">

        <div v-if="isLoading && !originalConfig" class="text-center py-2xl">
          <div class="loading-spinner mx-auto mb-md" style="width: 32px; height: 32px;"></div>
          <p class="text-secondary">正在加载配置...</p>
        </div>

        <div v-else-if="draftConfig && originalConfig" class="config-layout">
          <aside class="glass-card config-sidebar">
            <nav class="config-nav">
              <button v-for="group in configGroups" :key="group.id" class="config-nav-item"
                :class="{ active: activeGroupId === group.id }" @click="activeGroupId = group.id" type="button">
                <span class="config-nav-item-text">{{ group.title }}</span>
              </button>
            </nav>
          </aside>

          <section v-if="activeGroup" class="glass-card config-panel">
            <div class="group-header">
              <h3>{{ activeGroup.title }}</h3>
              <p v-if="activeGroup.description">{{ activeGroup.description }}</p>
            </div>

            <template v-for="field in activeGroup.fields" :key="field.id">
              <div v-if="isFieldVisible(field)" class="config-item">
                <div class="item-info">
                  <label>{{ field.label }}</label>
                  <div v-if="field.description" class="item-desc">{{ field.description }}</div>
                </div>

                <div class="item-control">
                  <template v-if="field.control.type === 'cronToggle'">
                    <label class="switch">
                      <input type="checkbox" :checked="getDraftValue(field.path) !== null" @change="toggleCron" />
                      <span class="switch-track"></span>
                      <span class="switch-handle"></span>
                    </label>
                  </template>

                  <template v-else-if="field.control.type === 'switch'">
                    <label class="switch">
                      <input type="checkbox" :checked="getDraftValue(field.path) === true" :data-path="field.path"
                        @change="toggleSwitch" />
                      <span class="switch-track"></span>
                      <span class="switch-handle"></span>
                    </label>
                  </template>
                  
                  <template v-else-if="field.control.type === 'select'">
                    <select :value="getDraftValue(field.path)" class="input w-full"
                      @change="(e) => setDraftText(field.path, (e.target as HTMLSelectElement).value)">
                      <option v-for="option in field.control.options" :key="option.value" :value="option.value">
                        {{ option.label }}
                      </option>
                    </select>
                    <div v-if="errors[field.path]" class="field-error">
                      {{ errors[field.path] }}
                    </div>
                  </template>
                  <template v-else-if="field.control.type === 'text'">
                    <div class="w-full">
                      <input :value="String(getDraftValue(field.path) ?? '')"
                        :class="['input', 'w-full', field.control.mono ? 'mono' : '']"
                        :placeholder="field.control.placeholder"
                        @input="(e) => setDraftText(field.path, (e.target as HTMLInputElement).value)" />
                      <div v-if="errors[field.path]" class="field-error">
                        {{ errors[field.path] }}
                      </div>
                    </div>
                  </template>

                  <template v-else-if="field.control.type === 'intRange'">
                    <div class="range-control">
                      <input type="range" class="range-slider" step="0.01" :min="getIntRangeMin(field.control)"
                        :max="getIntRangeMax(field.control)" :value="getLocalSliderValue(field.path)"
                        :style="getRangeStyle(field)"
                        @input="(e) => handleSliderInput(field.path, (e.target as HTMLInputElement).value, getIntRangeMin(field.control))">

                      <input class="input range-input" type="number" :min="getIntRangeMin(field.control)"
                        :max="getIntRangeMax(field.control)" :value="Number(getDraftValue(field.path))"
                        @input="(e) => setDraftInt(field.path, (e.target as HTMLInputElement).value, getIntRangeMin(field.control))" />
                    </div>
                  </template>
                </div>
              </div>

              <div v-if="isFieldVisible(field) && field.control.type === 'intRange' && errors[field.path]"
                class="field-error text-right">
                {{ errors[field.path] }}
              </div>
            </template>
          </section>
        </div>
      </div>
    </main>

    <div class="action-bar" :class="{ visible: isDirty }">
      <div class="action-info">
        <div class="changed-dot"></div>
        <span>配置已修改</span>
      </div>
      <div class="action-buttons">
        <button class="btn btn-secondary btn-sm" @click="resetDraft">放弃修改</button>
        <button class="btn btn-primary btn-sm" @click="save" :disabled="isLoading || hasErrors">
          应用保存
        </button>
      </div>
    </div>

    <div v-if="toast.show" class="toast" :class="toast.type">
      <div class="toast-content">
        <span>{{ toast.message }}</span>
        <button class="toast-close" @click="hideToast">×</button>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import api from '@/api'
import {
  NCM_CONFIG_UI_SCHEMA,
  validateNcmConfigDraft,
  type ConfigValidationErrors,
  type NcmConfigDraft,
  type NcmConfigFieldSchema,
  type NcmConfigGroupSchema,
} from '@/utils/configValidation'

// ... 保持原有 interface 定义不变 ...
interface ApiEnvelope<T> {
  code: number
  message: string
  data: T
}

interface DownloadSettings {
  cron_expr: string | null
  max_concurrent_downloads: number
  max_threads_per_download: number
  temp_downloads_dir: string
}

interface SubscriptionSettings {
  filename: string
  music_dir_playlist: string
}

interface NcmConfig {
  download: DownloadSettings
  subscription: SubscriptionSettings
}

interface Toast {
  show: boolean
  message: string
  type: 'info' | 'success' | 'warning' | 'error'
}

const isLoading = ref(false)
const loadError = ref<string | null>(null)

const originalConfig = ref<NcmConfig | null>(null)
const draftConfig = ref<NcmConfigDraft | null>(null)
const errors = reactive<ConfigValidationErrors>({})

// 【新增】本地滑块状态，Key为字段path，Value为浮点数
const localSliderValues = reactive<Record<string, number>>({})

const configGroups = NCM_CONFIG_UI_SCHEMA
const activeGroupId = ref(configGroups[0]?.id ?? '')
const activeGroup = computed<NcmConfigGroupSchema | null>(() => {
  return configGroups.find((g) => g.id === activeGroupId.value) ?? configGroups[0] ?? null
})

const toast = reactive<Toast>({
  show: false,
  message: '',
  type: 'info',
})

const isDirty = computed(() => {
  if (!originalConfig.value || !draftConfig.value) return false
  return JSON.stringify(originalConfig.value) !== JSON.stringify(draftConfig.value)
})

const hasErrors = computed(() => Object.keys(errors).length > 0)

onMounted(() => {
  reload()
})

// 实时校验 + 【新增】本地状态同步
watch(
  draftConfig,
  (next) => {
    Object.keys(errors).forEach((k) => delete errors[k])
    if (!next) return

    const nextErrors = validateNcmConfigDraft(next)
    Object.entries(nextErrors).forEach(([k, v]) => {
      errors[k] = v
    })

    // 【新增】当 draftConfig 变化时（例如通过数字输入框修改，或 reset），
    // 检查是否需要同步到 localSliderValues。
    // 逻辑：如果 local 值的四舍五入结果 不等于 新的 draft 值，说明是外部修改，强制同步。
    // 这样可以防止：滑动时 -> 修改 draft -> watcher 触发 -> 强制把 local 设为整数 -> 滑块顿挫。
    syncLocalFromDraft()
  },
  { deep: true },
)

// 辅助函数：获取嵌套属性值
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

function setValueByPath(obj: unknown, path: string, value: unknown): void {
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

function getDraftValue(path: string): unknown {
  if (!draftConfig.value) return null
  return getValueByPath(draftConfig.value, path)
}

// 【新增】获取本地滑块值，如果本地没有初始化，回退到 draftConfig
function getLocalSliderValue(path: string): number {
  if (localSliderValues[path] !== undefined) {
    return localSliderValues[path]
  }
  return Number(getDraftValue(path)) || 0
}

// 【新增】将 Draft 中的所有 intRange 值同步到 localSliderValues
function syncLocalFromDraft() {
  if (!draftConfig.value) return

  // 遍历配置结构找到所有 intRange
  configGroups.forEach(group => {
    group.fields.forEach(field => {
      if (field.control.type === 'intRange') {
        const draftVal = Number(getDraftValue(field.path))
        const localVal = localSliderValues[field.path]

        // 关键逻辑：
        // 1. 如果本地还没值 (undefined)，直接同步
        // 2. 如果本地值四舍五入后不等于 draft 值，说明 draft 发生了非滑动产生的变化（如输入框修改、重置），需要同步
        if (localVal === undefined || Math.round(localVal) !== draftVal) {
          localSliderValues[field.path] = draftVal
        }
      }
    })
  })
}

// 【新增】处理滑块滑动：实现无顿挫滑动的核心
function handleSliderInput(path: string, rawValue: string, min: number) {
  const floatVal = parseFloat(rawValue)

  // 1. 立即更新本地值，保证滑块和背景条完全跟手（无顿挫）
  localSliderValues[path] = floatVal

  // 2. 计算整数逻辑值
  const intVal = Math.round(floatVal)

  // 3. 只有当整数值真正改变时才更新 Draft（减少抖动和性能消耗）
  const currentDraftVal = Number(getDraftValue(path))
  if (currentDraftVal !== intVal) {
    setDraftInt(path, String(intVal), min)
  }
}

function setDraftText(path: string, value: string): void {
  if (!draftConfig.value) return
  setValueByPath(draftConfig.value, path, value)
}

function setDraftInt(path: string, raw: string, fallback: number): void {
  if (!draftConfig.value) return
  const parsed = Number.parseInt(raw, 10)
  setValueByPath(draftConfig.value, path, Number.isNaN(parsed) ? fallback : parsed)
}

function setDraftBool(path: string, value: boolean): void {
  if (!draftConfig.value) return
  setValueByPath(draftConfig.value, path, value)
}

function getIntRangeMin(control: NcmConfigFieldSchema['control']): number {
  return control.type === 'intRange' ? control.min : 1
}

function getIntRangeMax(control: NcmConfigFieldSchema['control']): number {
  return control.type === 'intRange' ? control.max : 1
}

function isFieldVisible(field: NcmConfigFieldSchema): boolean {
  if (!draftConfig.value) return false
  const rule = field.visibleWhen
  if (!rule) return true
  const value = getValueByPath(draftConfig.value, rule.path)
  if (rule.operator === 'notNull') return value !== null
  return value === rule.value
}

// 【修改】样式计算现在依赖 localSliderValues 里的浮点数
function getRangeStyle(field: NcmConfigFieldSchema): Record<string, string> {
  if (field.control.type !== 'intRange') return {}

  const min = field.control.min
  const max = field.control.max
  // 使用 getLocalSliderValue 获取精确的浮点数位置
  const value = getLocalSliderValue(field.path)

  const clamped = Number.isFinite(value) ? Math.min(max, Math.max(min, value)) : min
  const percent = max === min ? 0 : ((clamped - min) / (max - min)) * 100

  return {
    '--range-percent': `${percent}%`,
    background: `linear-gradient(to right, var(--range-fill) 0%, var(--range-fill) ${percent}%, var(--range-track) ${percent}%, var(--range-track) 100%)`
  }
}

async function reload(): Promise<void> {
  try {
    isLoading.value = true
    loadError.value = null

    const result = await api.config.getConfig()
    if (!result.success) {
      loadError.value = result.error || '请求失败'
      return
    }

    const payload = result.data as ApiEnvelope<NcmConfig>
    if (payload.code !== 200 || !payload.data) {
      loadError.value = payload.message || '后端返回异常'
      return
    }

    originalConfig.value = payload.data
    draftConfig.value = deepClone(payload.data) as NcmConfigDraft

    // 初始化本地滑块值
    syncLocalFromDraft()

    if (!activeGroupId.value) activeGroupId.value = configGroups[0]?.id ?? ''
  } catch (error) {
    console.error('Failed to load config:', error)
    loadError.value = '加载配置失败'
  } finally {
    isLoading.value = false
  }
}

function resetDraft(): void {
  if (!originalConfig.value) return
  draftConfig.value = deepClone(originalConfig.value) as NcmConfigDraft
  // 重置时同步本地滑块
  syncLocalFromDraft()
  showToast('已放弃所有未保存的修改', 'info')
}

function toggleCron(event: Event): void {
  if (!draftConfig.value) return
  const checked = (event.target as HTMLInputElement).checked
  if (!checked) {
    draftConfig.value.download.cron_expr = null
  } else {
    const originalCron = originalConfig.value?.download.cron_expr
    draftConfig.value.download.cron_expr = originalCron || '0 2 * * *'
  }
}

function toggleSwitch(event: Event): void {
  if (!draftConfig.value) return
  const checked = (event.target as HTMLInputElement).checked
  setDraftBool((event.target as HTMLInputElement).dataset.path || '', checked)
}



async function save(): Promise<void> {
  if (!draftConfig.value) return
  if (hasErrors.value) {
    showToast('请先修复校验错误后再保存', 'error')
    return
  }

  try {
    isLoading.value = true
    const partial = {
      download: draftConfig.value.download,
      subscription: draftConfig.value.subscription,
    }

    const result = await api.config.updateConfig(partial)
    if (!result.success) {
      showToast(result.error || '保存失败', 'error')
      return
    }

    const payload = result.data as ApiEnvelope<NcmConfig>
    if (payload.code !== 200) {
      showToast(payload.message || '保存失败', 'error')
      return
    }

    originalConfig.value = payload.data
    draftConfig.value = deepClone(payload.data) as NcmConfigDraft
    // 保存后同步一次（虽然理论上值一样，但保持一致性）
    syncLocalFromDraft()

    showToast('配置已保存并生效', 'success')
  } catch (error) {
    console.error('Failed to save config:', error)
    showToast('保存失败', 'error')
  } finally {
    isLoading.value = false
  }
}

function deepClone<T>(value: T): T {
  return JSON.parse(JSON.stringify(value))
}

function showToast(message: string, type: Toast['type'] = 'info'): void {
  toast.message = message
  toast.type = type
  toast.show = true
  setTimeout(() => hideToast(), 5000)
}

function hideToast(): void {
  toast.show = false
}
</script>

<style scoped>
.w-full {
  width: 100%;
}

.text-right {
  text-align: right;
}

.mt-xs {
  margin-top: var(--spacing-xs);
}

.px-xs {
  padding-left: 4px;
  padding-right: 4px;
}

.rounded {
  border-radius: 4px;
}
</style>