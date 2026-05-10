<template>
  <div class="page">
    <div class="container">
      <div class="dashboard-grid">
        <div class="glass-card status-card">
          <div class="card-header">
            <div>
              <h2 class="section-title">下载服务</h2>
              <p class="section-subtitle">最近 {{ historyWindowSeconds }} 秒速度趋势</p>
            </div>
            <div class="status-indicator" :class="isRunning ? 'status-online' : 'status-pending'">
              <span class="status-dot"></span>
              {{ isRunning ? '运行中' : '未运行' }}
            </div>
          </div>

          <div class="hero-row">
            <div class="metric-group">
              <div class="metric-label">当前下载速度</div>
              <div class="metric-value">
                {{ currentSpeed.value }}<span class="unit">{{ currentSpeed.unit }}</span>
              </div>
            </div>

            <div class="summary-grid">
              <div class="summary-item">
                <span class="summary-label">平均速度</span>
                <span class="summary-value">{{ averageSpeed.value }} {{ averageSpeed.unit }}</span>
              </div>
              <div class="summary-item">
                <span class="summary-label">峰值速度</span>
                <span class="summary-value">{{ peakSpeed.value }} {{ peakSpeed.unit }}</span>
              </div>
              <div class="summary-item">
                <span class="summary-label">采样点数</span>
                <span class="summary-value">{{ speedTimeline.length }}</span>
              </div>
            </div>
          </div>

          <DashboardTrendChart
            :data="speedTimeline"
            :height="240"
            color= "var(--text-secondary)"
            systemColor= "var(--accent-color)"
            empty-text="等待速度采样"
          />

          <div class="info-list">
            <div class="info-item">
              <span class="label">本次运行</span>
              <span class="value">{{ formatTime(lastRunTime) }}</span>
            </div>
            <div class="info-item">
              <span class="label">运行结束</span>
              <span class="value">{{ formatTime(endTime) }}</span>
            </div>
            <div class="info-item">
              <span class="label">下次运行</span>
              <span class="value">{{ formatTime(nextRunTime) }}</span>
            </div>
          </div>

          <div class="action-area">
            <button class="btn btn-primary w-full" :disabled="isRunning || isStarting" @click="handleRunNow">
              <span v-if="isStarting" class="loading-spinner"></span>
              <span>{{ isRunning ? '下载进行中' : '立即运行一次' }}</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import api from '@/api'
import DashboardTrendChart from '@/components/dashboard/DashboardTrendChart.vue'
import wsClient from '@/stores/wsClient'
import { formatTime } from '@/utils/time'
import { toast } from '@/utils/toast'

interface SchedulerSnapshot {
  is_running: boolean
  started_at: string | null
  finished_at: string | null
  next_run_at: string | null
  current_speed: number
  system_download_speed: number
}

interface TrendPoint {
  x: number
  y: number
  systemY: number
}

const historyWindowSeconds = 30
const maxHistoryPoints = historyWindowSeconds

const isRunning = ref(false)
const isStarting = ref(false)
const currentSpeed = ref({ value: '0.00', unit: 'B/s' })
const lastRunTime = ref<string | null>(null)
const endTime = ref<string | null>(null)
const nextRunTime = ref<string | null>(null)
const latestSpeed = ref(0)
const latestSystemSpeed = ref(0)
const speedTimeline = ref<TrendPoint[]>([])

let debounceTimer: number | null = null
let samplingTimer: number | null = null

const schedulerSnapshot = computed<SchedulerSnapshot | null>(() => {
  const raw = wsClient.reactiveState.data.scheduler.value as SchedulerSnapshot | null
  if (!raw) return null

  return {
    is_running: Boolean(raw.is_running),
    started_at: raw.started_at ?? null,
    finished_at: raw.finished_at ?? null,
    next_run_at: raw.next_run_at ?? null,
    current_speed: Number(raw.current_speed ?? 0),
    system_download_speed: Number(raw.system_download_speed ?? 0),
  }
})

const peakSpeed = computed(() => {
  const max = speedTimeline.value.reduce((peak, point) => Math.max(peak, point.y), 0)
  return formatSpeed(max)
})

const averageSpeed = computed(() => {
  if (speedTimeline.value.length === 0) return formatSpeed(0)
  const total = speedTimeline.value.reduce((sum, point) => sum + point.y, 0)
  return formatSpeed(total / speedTimeline.value.length)
})

watch(
  schedulerSnapshot,
  (snapshot) => {
    if (!snapshot) return

    isRunning.value = snapshot.is_running
    lastRunTime.value = snapshot.started_at
    endTime.value = snapshot.finished_at
    nextRunTime.value = snapshot.next_run_at
    latestSpeed.value = snapshot.current_speed
    latestSystemSpeed.value = snapshot.system_download_speed
    currentSpeed.value = formatSpeed(snapshot.current_speed)
  },
  { immediate: true },
)

function formatSpeed(bytesPerSecond: number) {
  const units = ['B/s', 'KB/s', 'MB/s', 'GB/s'] as const

  if (!Number.isFinite(bytesPerSecond) || bytesPerSecond <= 0) {
    return { value: '0.00', unit: 'B/s' }
  }

  const base = 1024
  const index = Math.min(Math.floor(Math.log(bytesPerSecond) / Math.log(base)), units.length - 1)
  const value = bytesPerSecond / Math.pow(base, index)
  const unit = units[index] ?? 'B/s'

  return {
    value: value.toFixed(index === 0 ? 0 : 2),
    unit,
  }
}

function pushSpeedSample(speed: number, systemSpeed: number) {
  const point = {
    x: Date.now(),
    y: Math.max(0, Math.round(speed)),
    systemY: Math.max(0, Math.round(systemSpeed)),
  }

  const cutoff = point.x - historyWindowSeconds * 1000
  const nextTimeline = [...speedTimeline.value, point].filter((item) => item.x >= cutoff)
  speedTimeline.value = nextTimeline.slice(-maxHistoryPoints)
}

const triggerNow = async () => {
  if (isRunning.value || isStarting.value) return

  isStarting.value = true
  try {
    const res = await api.download.daemonControl('trigger_now')
    if (res.success) {
      const code = res.data.code
      const message = res.data.message || '任务已触发'
      if (code === 200 || code === 202) {
        toast.success('开始执行下载任务', '下载服务')
        const payload = res.data.data || {}
        if (payload.is_running !== undefined) {
          isRunning.value = !!payload.is_running
        }
        if (payload.next_run_time) {
          nextRunTime.value = payload.next_run_time
        }
      } else {
        toast.error(message || '触发任务失败', '下载服务')
      }
    } else {
      toast.error(res.error || '触发任务失败', '下载服务')
    }
  } catch (error) {
    console.error(error)
    toast.error('网络请求失败', '下载服务')
  } finally {
    isStarting.value = false
  }
}

const handleRunNow = () => {
  if (debounceTimer) {
    window.clearTimeout(debounceTimer)
  }

  debounceTimer = window.setTimeout(() => {
    triggerNow()
  }, 300)
}

onMounted(() => {
  wsClient.enterPage('dashboard', 'scheduler')
  pushSpeedSample(0, 0)
  samplingTimer = window.setInterval(() => {
    pushSpeedSample(latestSpeed.value, latestSystemSpeed.value)
  }, 1000)
})

onUnmounted(() => {
  if (debounceTimer) {
    window.clearTimeout(debounceTimer)
  }
  if (samplingTimer) {
    window.clearInterval(samplingTimer)
  }
  wsClient.leavePage('dashboard')
})
</script>

<style scoped lang="scss">
@use '@/assets/styles/variables' as *;

.dashboard-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  gap: var(--spacing-lg);
}

.status-card {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: var(--spacing-md);
}

.section-subtitle {
  margin: var(--spacing-xs) 0 0;
  color: var(--text-tertiary);
  font-size: 0.9rem;
}

.hero-row {
  display: grid;
  grid-template-columns: minmax(0, 1.4fr) minmax(280px, 1fr);
  gap: var(--spacing-lg);
  align-items: center;
}

.metric-group {
  min-width: 0;

  .metric-label {
    font-size: 0.95rem;
    color: var(--text-secondary);
    margin-bottom: var(--spacing-xs);
  }

  .metric-value {
    font-size: clamp(2.3rem, 4vw, 3.25rem);
    line-height: 1;
    font-weight: 700;
    color: var(--text-primary);
    font-variant-numeric: tabular-nums;

    .unit {
      font-size: 1rem;
      color: var(--text-tertiary);
      font-weight: 500;
      margin-left: 6px;
    }
  }
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: var(--spacing-sm);
}

.summary-item {
  background: color-mix(in srgb, var(--bg-surface) 84%, transparent);
  border: 1px solid color-mix(in srgb, var(--border-color) 70%, transparent);
  border-radius: 14px;
  padding: 0.85rem 0.9rem;
}

.summary-label {
  display: block;
  margin-bottom: 0.35rem;
  font-size: 0.82rem;
  color: var(--text-tertiary);
}

.summary-value {
  display: block;
  color: var(--text-primary);
  font-weight: 600;
  font-variant-numeric: tabular-nums;
}

.info-list {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: var(--spacing-md);
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  min-width: 0;

  .label {
    color: var(--text-secondary);
    font-size: 0.9rem;
  }

  .value {
    color: var(--text-primary);
    font-family: monospace;
    font-size: 0.95rem;
    font-variant-numeric: tabular-nums;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
}

.action-area {
  margin-top: auto;
}

.w-full {
  width: 100%;
}

@media (max-width: 900px) {
  .hero-row {
    grid-template-columns: minmax(0, 1fr);
  }

  .summary-grid,
  .info-list {
    grid-template-columns: minmax(0, 1fr);
  }
}
</style>
