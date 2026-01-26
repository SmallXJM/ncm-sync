<template>
  <div class="page">
    <main>
      <div class="container">

        <AppLoading v-if="isLoading && !originalConfig" message="正在获取设置信息" />

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
                      <div class="field-message">
                        <div v-if="errors[field.path] && !isPreviewLoading" class="field-error">
                          {{ errors[field.path] }}
                        </div>
                        <!-- 【新增】Cron 预览显示 -->
                        <div v-if="field.path === 'download.cron_expr' && (nextRunTimePreview || isPreviewLoading)"
                          class="field-preview">
                          <span v-if="isPreviewLoading">正在计算下次运行时间...</span>
                          <span v-else>预计下次运行: {{ formatTime(nextRunTimePreview) }}</span>
                        </div>
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

  </div>
</template>

<script lang="ts" setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import AppLoading from '@/components/AppLoading.vue'
import api from '@/api'
import {
  NCM_CONFIG_UI_SCHEMA,
  validateNcmConfigDraft,
  validateCronExpr,
  getValueByPath,
  setValueByPath,
  isVisibleByRule,
  getIntRangeMin,
  getIntRangeMax,
  deepClone,
  type ConfigValidationErrors,
  type NcmConfigDraft,
  type NcmConfigFieldSchema,
  type NcmConfigGroupSchema,
  type AuthUserDraft,
} from '@/utils/configValidation'
import { toast } from '@/utils/toast'
import { formatTime } from '@/utils/time'
import { type ApiEnvelope } from '@/api/request'
import { type NcmConfig } from '@/api/ncm/config'



const isLoading = ref(false)
const loadError = ref<string | null>(null)

const originalConfig = ref<NcmConfig | null>(null)
const draftConfig = ref<NcmConfigDraft | null>(null)
const errors = reactive<ConfigValidationErrors>({})

// 【新增】本地滑块状态，Key为字段path，Value为浮点数
const localSliderValues = reactive<Record<string, number>>({})
// 【新增】Cron 预览相关状态
const nextRunTimePreview = ref<string | null>(null)
const isPreviewLoading = ref(false)
let previewDebounceTimer: number | undefined
const lastCheckedCronExpr = ref<string | null>(null)
const isCronBackendInvalid = ref(false)



const configGroups = NCM_CONFIG_UI_SCHEMA
const activeGroupId = ref(configGroups[0]?.id ?? '')
const activeGroup = computed<NcmConfigGroupSchema | null>(() => {
  return configGroups.find((g) => g.id === activeGroupId.value) ?? configGroups[0] ?? null
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
    if (!next) return

    // 先触发预览逻辑（如果 Cron 变了，会置空 preview）
    handleCronPreview(next)

    // 再运行校验（此时 preview 可能已被置空，校验会报错）
    runValidation(next)

    // 【新增】当 draftConfig 变化时（例如通过数字输入框修改，或 reset），
    // 检查是否需要同步到 localSliderValues。
    // 逻辑：如果 local 值的四舍五入结果 不等于 新的 draft 值，说明是外部修改，强制同步。
    // 这样可以防止：滑动时 -> 修改 draft -> watcher 触发 -> 强制把 local 设为整数 -> 滑块顿挫。
    syncLocalFromDraft()
  },
  { deep: true },
)

// 【新增】监听预览结果/状态变化，重新校验
watch([nextRunTimePreview, isCronBackendInvalid], () => {
  if (draftConfig.value) {
    runValidation(draftConfig.value)
  }
})

function runValidation(draft: NcmConfigDraft) {
  Object.keys(errors).forEach((k) => delete errors[k])

  // 注入服务端预览状态作为校验上下文
  const context = {
    cronServerPreview: nextRunTimePreview.value,
    isCronBackendInvalid: isCronBackendInvalid.value
  }

  const nextErrors = validateNcmConfigDraft(draft, context)
  Object.entries(nextErrors).forEach(([k, v]) => {
    errors[k] = v
  })
}

// 【新增】处理 Cron 预览
function handleCronPreview(draft: NcmConfigDraft) {
  const cronPath = 'download.cron_expr'
  const cronExpr = getValueByPath(draft, cronPath) as string | null

  // 0. 检查是否真的变化了，防止无关字段修改导致重置
  if (cronExpr === lastCheckedCronExpr.value) return
  lastCheckedCronExpr.value = cronExpr

  // 如果值没变（符合原配置），默认它是有效的（不阻断保存）
  // 只要值变了（且不等于原配置），先假设它是无效的（阻断保存），直到服务端返回有效结果
  const originalCron = originalConfig.value?.download.cron_expr
  if (cronExpr === originalCron) {
    isCronBackendInvalid.value = false
  } else {
    isCronBackendInvalid.value = true
  }

  // 清空预览
  nextRunTimePreview.value = null

  // 清除旧的 timer
  if (previewDebounceTimer) {
    clearTimeout(previewDebounceTimer)
    previewDebounceTimer = undefined
  }

  // 1. 如果没有值，或格式校验不通过，直接返回（由 regex 校验负责报错）
  if (!cronExpr) return
  if (validateCronExpr(cronExpr)) return

  // 2. 防抖调用后端接口
  previewDebounceTimer = window.setTimeout(async () => {
    try {
      isPreviewLoading.value = true
      const result = await api.download.daemonControl('preview_cron', cronExpr)

      // 只有当明确返回 200 且 next_run_time 为 null 时，才标记为无效
      if (result.success && result.data?.code === 200) {
        if (result.data.data?.next_run_time) {
          nextRunTimePreview.value = result.data.data.next_run_time
          isCronBackendInvalid.value = false
        } else {
          // 明确无效
          nextRunTimePreview.value = null
          isCronBackendInvalid.value = true
        }
      } else {
        // 接口错误（如网络问题），暂不阻拦保存，仅清空预览
        nextRunTimePreview.value = null
        isCronBackendInvalid.value = false
      }
    } catch (e) {
      console.error('Failed to preview cron:', e)
      nextRunTimePreview.value = null
      isCronBackendInvalid.value = false
    } finally {
      isPreviewLoading.value = false
    }
  }, 300) // 50ms 防抖
}

// 辅助函数：获取嵌套属性值
// getValueByPath, setValueByPath 已从 @/utils/configValidation 导入

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

function isFieldVisible(field: NcmConfigFieldSchema): boolean {
  if (!draftConfig.value) return false
  return isVisibleByRule(draftConfig.value, field.visibleWhen)
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
    // 确保 rotate_secret_key 在 originalConfig 中存在（默认为 false），以保证脏检查正常
    if (originalConfig.value?.auth) {
      (originalConfig.value.auth as any).rotate_secret_key = false
    }

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
  toast.show('已放弃所有未保存的修改', 'info')
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
    toast.show('请先修复校验错误后再保存', 'error')
    return
  }

  try {
    isLoading.value = true
    const partial = {
      download: draftConfig.value.download,
      subscription: draftConfig.value.subscription,
      auth: draftConfig.value.auth
    }

    const result = await api.config.updateConfig(partial)
    if (!result.success) {
      toast.show(result.error || '保存失败', 'error')
      return
    }

    const payload = result.data as ApiEnvelope<NcmConfig>
    if (payload.code !== 200) {
      toast.show(payload.message || '保存失败', 'error')
      return
    }

    originalConfig.value = payload.data!
    draftConfig.value = deepClone(payload.data) as NcmConfigDraft
    // 保存后同步一次（虽然理论上值一样，但保持一致性）
    syncLocalFromDraft()

    toast.show('配置已保存并生效', 'success')
  } catch (error) {
    console.error('Failed to save config:', error)
    toast.show('保存失败', 'error')
  } finally {
    isLoading.value = false
  }
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

.field-message {
  margin-top: 4px;
}

.field-error {
  font-size: 0.85em;
  color: var(--color-error);
  line-height: 1.5;
  white-space: pre-wrap;
  word-break: break-word;
}

.field-preview {
  font-size: 0.85em;
  color: var(--text-tertiary);
}

/* 用户列表样式 */
.user-list-control {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.user-row {
  display: flex;
  gap: var(--spacing-sm);
  align-items: center;
}

.flex-1 {
  flex: 1;
  min-width: 0;
}

.btn-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  padding: 0;
  border-radius: 4px;
  border: 1px solid var(--border-color);
  background: var(--bg-surface);
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.2s;
}

.btn-icon:hover:not(:disabled) {
  background: var(--bg-surface-hover);
  color: var(--text-primary);
  border-color: var(--border-hover);
}

.btn-icon:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
