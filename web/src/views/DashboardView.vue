<template>
  <div class="page">
    <div class="container">
      <div class="dashboard-grid">
        <div class="glass-card status-card">
          <div class="card-header">
            <div class="header-line">
              <h2 class="section-title">下载服务</h2>
              <div class="header-right">
                <div class="status-indicator" :class="isRunning ? 'status-online' : 'status-pending'">
                  <span class="status-dot"></span>
                  {{ isRunning ? '运行中' : '未运行' }}
                </div>
              </div>
            </div>
            <div class="header-line">
              <span class="section-subtitle">当前下载速度</span>
              <div class="header-right">
                <div class="section-figure">
                  {{ currentSystemSpeed.value }}{{ currentSystemSpeed.unit }}
                </div>
              </div>
            </div>
          </div>

          <TrendChart
            :series="speedChartSeries"
            :height="200"
            :value-formatter="formatChartSpeed"
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

        <div class="glass-card recent-card">
          <div class="card-header">
            <div class="header-line">
              <h2 class="section-title">最近入库</h2>
              <div class="header-right"></div>
            </div>
            <div class="header-line">
              <span class="section-subtitle">近 7 日新增音乐</span>
              <div class="header-right">
                <div class="section-figure">{{ recentAddedTotalCount }} 首</div>
              </div>
            </div>
          </div>
          
          <BarChart
            :series="recentAddedSeries"
            :height="220"
            :value-formatter="formatMusicCount"
            :x-formatter="formatRecentAddedDate"
            empty-text="暂无入库记录"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import api from '@/api'
import BarChart from '@/components/chart/BarChart.vue'
import TrendChart from '@/components/chart/TrendChart.vue'
import type { BarChartSeries, TrendChartSeries } from '@/components/chart/chartUtils'
import type { RecentAddedMusicDay } from '@/api/ncm/dashboard'
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
const currentSystemSpeed = ref({ value: '0.00', unit: 'B/s' })
const lastRunTime = ref<string | null>(null)
const endTime = ref<string | null>(null)
const nextRunTime = ref<string | null>(null)
const latestSpeed = ref(0)
const latestSystemSpeed = ref(0)
const speedTimeline = ref<TrendPoint[]>([])
const recentAddedDays = ref<RecentAddedMusicDay[]>([])

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

const speedChartSeries = computed<TrendChartSeries[]>(() => [
  {
    key: 'system',
    title: '整体下载',
    color: 'var(--accent-color)',
    data: speedTimeline.value.map((point) => ({
      x: point.x,
      y: point.systemY,
    })),
  },
  {
    key: 'app',
    title: '程序下载',
    color: 'var(--text-secondary)',
    data: speedTimeline.value.map((point) => ({
      x: point.x,
      y: point.y,
    })),
  },
])

const recentAddedSeries = computed<BarChartSeries[]>(() => [
  {
    key: 'recent-added',
    title: '新增音乐',
    color: 'var(--accent-color)',
    data: recentAddedDays.value.map((day) => ({
      x: day.date,
      y: day.count,
    })),
  },
])

const recentAddedTotalCount = computed(() =>
  recentAddedDays.value.reduce((sum, day) => sum + day.count, 0),
)

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
    currentSystemSpeed.value = formatSpeed(snapshot.system_download_speed)
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

function formatChartSpeed(bytesPerSecond: number) {
  const speed = formatSpeed(bytesPerSecond)
  return `${speed.value} ${speed.unit}`
}

function formatMusicCount(count: number) {
  return `${Math.max(0, Math.round(count))} 首`
}

function formatRecentAddedDate(date: string) {
  return date
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

const loadDashboardAggregate = async () => {
  try {
    const res = await api.dashboard.getAggregate()
    if (res.success && res.data.code === 200 && res.data.data) {
      recentAddedDays.value = res.data.data.recent_added_music?.days ?? []
    } else if (!res.success) {
      console.warn('Failed to load dashboard aggregate:', res.error)
    }
  } catch (error) {
    console.error(error)
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
  loadDashboardAggregate()
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

.status-card,
.recent-card {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
}

.card-header {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.header-line {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: var(--spacing-md);
  min-width: 0;
}

.section-subtitle {
  color: var(--text-tertiary);
  font-size: 0.9rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.header-right {
  display: flex;
  align-items: flex-end;
  justify-content: flex-end;
  gap: var(--spacing-xs);
  flex: 0 0 auto;
  min-width: max-content;
}

.section-figure {
  color: var(--text-primary);
  font-size: 0.9rem;
  font-weight: 400;
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
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
  .info-list {
    grid-template-columns: minmax(0, 1fr);
  }
}
</style>
