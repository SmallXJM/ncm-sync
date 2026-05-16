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
              <span class="section-subtitle">下载任务调度</span>
              <div class="header-right"></div>
            </div>
          </div>

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

        <div class="glass-card subscription-card">
          <div class="card-header">
            <div class="header-line">
              <h2 class="section-title">当前监听</h2>
              <div class="header-right">
              </div>
            </div>
            <div class="header-line">
              <span class="section-subtitle">已开启订阅</span>
              <div class="header-right">
                <span class="section-figure">{{ enabledSubscriptionTotal }} 个</span>
              </div>
            </div>
          </div>

          <div v-if="subscriptionTypeStats.length > 0" class="subscription-grid">
            <div v-for="item in subscriptionTypeStats" :key="item.type" class="subscription-item">
              <span class="subscription-icon" aria-hidden="true">
                <component v-if="item.iconComponent" :is="item.iconComponent" />
                <span v-else>{{ item.iconText }}</span>
              </span>
              <span class="subscription-label">{{ item.label }}</span>
              <span class="subscription-count">{{ item.count }}</span>
            </div>
          </div>
          <div v-else class="subscription-empty">暂无开启的订阅</div>
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

          <BarChart :series="recentAddedSeries" :height="220" :value-formatter="formatMusicCount"
            :x-formatter="formatRecentAddedDate" empty-text="暂无入库记录" />
        </div>

        <div class="glass-card speed-card">
          <div class="card-header">
            <div class="header-line">
              <h2 class="section-title">下载速度</h2>
              <div class="header-right">

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

          <TrendChart :series="speedChartSeries" :height="200" :value-formatter="formatChartSpeed"
            empty-text="等待速度采样" />
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
import type { DownloadJobItem } from '@/api/ncm/download'
import { sidebarIcons } from '@/layout/AppSidebar.vue'
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
const currentSystemSpeed = ref({ value: '0.00', unit: 'B/s' })
const lastRunTime = ref<string | null>(null)
const endTime = ref<string | null>(null)
const nextRunTime = ref<string | null>(null)
const latestSpeed = ref(0)
const latestSystemSpeed = ref(0)
const speedTimeline = ref<TrendPoint[]>([])
const recentAddedDays = ref<RecentAddedMusicDay[]>([])
const subscriptionJobs = ref<DownloadJobItem[]>([])

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

const enabledSubscriptionJobs = computed(() => subscriptionJobs.value.filter((job) => job.enabled))

const enabledSubscriptionTotal = computed(() => enabledSubscriptionJobs.value.length)

const subscriptionTypeStats = computed(() => {
  const counts = new Map<string, number>()

  enabledSubscriptionJobs.value.forEach((job) => {
    const type = job.source_type || job.job_type || 'unknown'
    counts.set(type, (counts.get(type) ?? 0) + 1)
  })

  return Array.from(counts.entries())
    .map(([type, count]) => ({
      type,
      count,
      label: formatSourceType(type),
      iconComponent: getSourceTypeIconComponent(type),
      iconText: getSourceTypeIconText(type),
    }))
    .sort((a, b) => a.label.localeCompare(b.label, 'zh-CN'))
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

function formatSourceType(value: string) {
  const map: Record<string, string> = {
    playlist: '歌单',
    album: '专辑',
    artist: '艺术家',
  }
  return map[value] || value || '未知'
}

function getSourceTypeIconComponent(value: string) {
  if (value === 'playlist') return sidebarIcons.playlist
  return null
}

function getSourceTypeIconText(value: string) {
  const map: Record<string, string> = {
    album: '□',
    artist: '○',
  }
  return map[value] || '•'
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

const loadSubscriptionJobs = async () => {
  try {
    const res = await api.download.getJobList()
    if (res.success && res.data.code === 200 && res.data.data) {
      subscriptionJobs.value = res.data.data.jobs || []
    } else if (!res.success) {
      console.warn('Failed to load subscription jobs:', res.error)
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
  loadSubscriptionJobs()
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
.subscription-card,
.speed-card,
.recent-card {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
}

.subscription-card {
  order: 0;
}

.recent-card {
  order: 1;
}

.status-card {
  order: 2;
}

.speed-card {
  order: 3;
}

.card-header {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.header-line {
  display: flex;
  align-items: center;
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

.subscription-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--spacing-md) var(--spacing-lg);
}

.subscription-item {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  align-items: center;
  gap: var(--spacing-sm);
  min-width: 0;
}

.subscription-item:only-child,
.subscription-item:last-child:nth-child(odd) {
  grid-column: 1 / -1;
}

.subscription-icon {
  display: grid;
  place-items: center;
  width: 1.25rem;
  height: 1.25rem;
  color: var(--text-secondary);
  font-size: 0.95rem;
  line-height: 1;

  :deep(svg) {
    width: 1.1rem;
    height: 1.1rem;
  }
}

.subscription-label {
  min-width: 0;
  color: var(--text-primary);
  font-size: 0.95rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.subscription-count {
  min-width: 2rem;
  padding: 0.18rem 0.55rem;
  border: 1px solid color-mix(in srgb, var(--border-color) 78%, transparent);
  border-radius: var(--radius-full);
  color: var(--text-primary);
  font-size: 0.85rem;
  font-variant-numeric: tabular-nums;
  line-height: 1.25;
  text-align: center;
}

.subscription-empty {
  display: grid;
  place-items: center;
  min-height: 88px;
  color: var(--text-tertiary);
  font-size: 0.9rem;
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

  .info-list,
  .subscription-grid {
    grid-template-columns: minmax(0, 1fr);
  }
}

@media (min-width: 901px) {
  .dashboard-grid {
    grid-template-columns: repeat(12, minmax(0, 1fr));
    align-items: stretch;
  }

  .subscription-card {
    grid-column: 1 / -1;
  }

  .recent-card {
    grid-column: span 8;
  }

  .status-card {
    grid-column: span 4;
  }

  .speed-card {
    grid-column: 1 / -1;
  }

  .status-card .info-list {
    grid-template-columns: minmax(0, 1fr);
  }
}
</style>
