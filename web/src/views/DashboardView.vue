<template>
  <div class="page">
    <div class="container">
      <!-- <header class="page-header">
        <h1 class="page-title">仪表盘</h1>
        <p class="page-subtitle">系统运行状态概览</p>
      </header> -->

      <div class="dashboard-grid">
        <!-- 下载状态卡片 -->
        <div class="glass-card status-card">
          <div class="card-header">
            <h2 class="section-title">下载服务</h2>
            <div class="status-indicator" :class="isRunning ? 'status-online' : 'status-pending'">
              <span class="status-dot"></span>
              {{ isRunning ? '运行中' : '未运行' }}
            </div>
          </div>

          <div class="card-content">
            <div class="metric-group">
              <div class="metric-label">当前速度</div>
              <div class="metric-value">
                {{ currentSpeed.value }}<span class="unit">{{ currentSpeed.unit }}</span>
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
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import api from '@/api'
import { toast } from '@/utils/toast'
import wsClient from '@/stores/wsClient'
import { formatTime } from '@/utils/time'

interface SchedulerSnapshot {
  is_running: boolean
  started_at: string | null
  finished_at: string | null
  next_run_at: string | null
  current_speed: number
}

const isRunning = ref(false)
const isStarting = ref(false)
const currentSpeed = ref({ value: '0.00', unit: 'B/s' })

const lastRunTime = ref<string | null>(null)
const endTime = ref<string | null>(null)
const nextRunTime = ref<string | null>(null)
let debounceTimer: number | null = null


const schedulerSnapshot = computed<SchedulerSnapshot | null>(() => {
  const raw = wsClient.reactiveState.data.scheduler.value as SchedulerSnapshot | null
  if (!raw) return null
  return {
    is_running: Boolean(raw.is_running),
    started_at: raw.started_at ?? null,
    finished_at: raw.finished_at ?? null,
    next_run_at: raw.next_run_at ?? null,
    current_speed: raw.current_speed,
  }
})

watch(
  schedulerSnapshot,
  (snapshot) => {
    if (!snapshot) return
    isRunning.value = snapshot.is_running
    lastRunTime.value = snapshot.started_at
    endTime.value = snapshot.finished_at
    nextRunTime.value = snapshot.next_run_at
    currentSpeed.value = formatSpeed(snapshot.current_speed)
  },
  { immediate: true },
)

// 按照speed格式化速度为KB/s 或者 MB/s
function formatSpeed(bytesPerSecond: number) {
  if (bytesPerSecond === 0) return { value: '0.00', unit: 'B/s' };
  const k = 1024;
  const sizes = ['B/s', 'KB/s', 'MB/s', 'GB/s'];
  const i = Math.floor(Math.log(bytesPerSecond) / Math.log(k));
  return {
    value: (bytesPerSecond / Math.pow(k, i)).toFixed(2) || '0.00',
    unit: sizes[i] || 'B/s'
  };
}



// 立即运行
const triggerNow = async () => {
  if (isRunning.value || isStarting.value) return

  isStarting.value = true
  try {
    const res = await api.download.daemonControl('trigger_now')
    if (res.success) {
      const code = res.data.code
      const message = res.data.message || '任务已触发'
      if (code === 200 || code === 202) {
        toast.success("开始执行下载任务", "下载服务")
        const payload = (res.data).data || {}
        if (payload.is_running !== undefined) {
          isRunning.value = !!payload.is_running
        }
        if (payload.next_run_time) {
          nextRunTime.value = payload.next_run_time
        }
      } else {
        toast.error(message || '触发任务失败', "下载服务")
      }
    } else {
      toast.error(res.error || '触发任务失败', "下载服务")
    }
  } catch (e) {
    console.error(e)
    toast.error('网络请求失败', "下载服务")
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
})

onUnmounted(() => {
  if (debounceTimer) {
    window.clearTimeout(debounceTimer)
  }
  wsClient.leavePage('dashboard')
})
</script>

<style scoped lang="scss">
@use '@/assets/styles/variables' as *;

.dashboard-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
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
  align-items: center;
}

.metric-group {
  text-align: center;
  margin-bottom: var(--spacing-xl);

  .metric-label {
    font-size: 0.9rem;
    color: var(--text-secondary);
    margin-bottom: var(--spacing-xs);
  }

  .metric-value {
    /* 如果需要间距，可以在这里设置具体的像素值，比如 4px */
    font-size: 2.5rem;
    font-weight: 700;
    color: var(--text-primary);
    font-variant-numeric: tabular-nums;

    .unit {
      font-size: 1rem;
      color: var(--text-tertiary);
      font-weight: 400;
      margin-left: 4px;
    }
  }
}

.info-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-xl);
}

.info-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.95rem;

  .label {
    color: var(--text-secondary);
  }

  .value {
    color: var(--text-primary);
    font-family: monospace;
    font-variant-numeric: tabular-nums;
  }
}

.action-area {
  margin-top: auto;
}

.w-full {
  width: 100%;
}
</style>
