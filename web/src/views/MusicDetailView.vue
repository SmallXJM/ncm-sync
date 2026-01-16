<template>
  <div class="page">
    <main>
      <div class="container">
        <div v-if="isLoading" class="text-center py-2xl">
          <div class="loading-spinner mx-auto mb-md" style="width: 32px; height: 32px;"></div>
          <p class="text-secondary">正在加载本地音乐详情...</p>
        </div>

        <div v-else-if="detail" class="detail-layout">
          <div class="glass-card detail-card">
            <div class="detail-header">
              <div class="detail-cover">
                <img v-if="!coverError" :src="coverSrc" alt="cover" loading="lazy" @error="coverError = true"
                  class="image-filter-brightness" />
                <div v-else class="default-cover">
                  <svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 24 24" fill="none"
                    stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M9 18V5l12-2v13"></path>
                    <circle cx="6" cy="18" r="3"></circle>
                    <circle cx="18" cy="16" r="3"></circle>
                  </svg>
                </div>
              </div>

              <div class="detail-meta">
                <h2 class="detail-title">{{ detail.music_title || '未知标题' }}</h2>
                <p class="text-secondary">艺术家：{{ detail.music_artist || '未知艺术家' }}</p>
                <p class="text-secondary">专辑：{{ detail.music_album || '未知专辑' }}</p>
                <div class="meta-row">
                  <span class="badge" :class="getStatusClass(detail.status)">{{ detail.status }}</span>
                  <span class="meta-item">
                    <span class="text-tertiary" v-if="detail.quality">· {{ detail.quality }}</span>
                    <span class="text-tertiary" v-if="detail.file_size">· {{ formatSize(detail.file_size) }}</span>
                  </span>
                </div>

              </div>
            </div>

            <div class="divider"></div>

            <div class="detail-section">
              <h3 class="section-title">本地文件</h3>
              <div class="info-grid">
                <div class="info-item">
                  <label>文件路径</label>
                  <span class="mono break-all">{{ detail.file_path || '-' }}</span>
                </div>
                <div class="info-item">
                  <label>文件名</label>
                  <span class="mono break-all">{{ detail.file_name || '-' }}</span>
                </div>
              </div>
            </div>

            <div class="divider"></div>

            <div class="detail-section">
              <h3 class="section-title">
                {{ isPlaying ? '正在播放' : '播放' }}
              </h3>

              <div class="custom-player glass-card">
                <audio ref="audioRef" :src="audioSrc" @timeupdate="onTimeUpdate" @loadedmetadata="onLoadedMetadata"
                  @ended="isPlaying = false"></audio>

                <div class="player-main">
                  <img :src="coverSrc" class="player-mini-cover image-filter-brightness"
                    :class="{ 'rotating': isPlaying }" @error="coverError = true">

                  <div class="player-content">
                    <div class="player-info">
                      <span class="player-title">{{ detail.music_title }}</span>
                      <span class="player-artist">{{ detail.music_artist }}</span>
                    </div>

                    <div class="progress-container">
                      <span class="time-stamp">{{ formatTime(currentTime) }}</span>
                      <div class="range-control">
                        <input type="range" class="range-slider" min="0" :max="duration"
                          :style="getRangeStyle(0, duration, currentTime)" step="0.01" v-model.number="currentTime"
                          @mousedown="onDragStart" @touchstart="onDragStart" @mouseup="onDragEnd" @touchend="onDragEnd"
                          @change="onDragEnd">
                        <span class="time-stamp">{{ formatTime(duration) }}</span>
                      </div>
                    </div>
                  </div>

                  <div class="player-controls">
                    <button class="btn-play-toggle" @click="togglePlay">
                      <svg v-if="isInitial" xmlns="http://www.w3.org/2000/svg" width="32" height="32"
                        viewBox="0 0 24 24">
                        <path fill="currentColor" fill-opacity="0" stroke="currentColor" stroke-dasharray="38"
                          stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 6l10 6l-10 6Z">
                          <animate fill="freeze" attributeName="stroke-dashoffset" dur="0.5s" values="38;0" />
                          <animate fill="freeze" attributeName="fill-opacity" begin="0.5s" dur="0.4s" to="1" />
                        </path>
                      </svg>

                      <svg v-else-if="!isPlaying" xmlns="http://www.w3.org/2000/svg" width="32" height="32"
                        viewBox="0 0 24 24">
                        <path fill="currentColor" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"
                          stroke-width="2" d="M13 15l-5 3l0 -12l5 3l0 0M13 9l5 3l0 0l-5 3l0 0">
                          <animate fill="freeze" attributeName="d" dur="0.6s" keyTimes="0;0.33;1"
                            values="M9 18l-2 0l0 -12l2 0l0 12M15 6l2 0l0 12l-2 0l0 -12;M13 15l-5 3l0 -12l5 3l0 6M13 9l5 3l0 0l-5 3l0 -6;M13 15l-5 3l0 -12l5 3l0 0M13 9l5 3l0 0l-5 3l0 0" />
                        </path>
                      </svg>

                      <svg v-else xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24">
                        <path fill="currentColor" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"
                          stroke-width="2" d="M9 18l-2 0l0 -12l2 0l0 12M15 6l2 0l0 12l-2 0l0 -12">
                          <animate fill="freeze" attributeName="d" dur="0.6s" keyTimes="0;0.33;1"
                            values="M13 15l-5 3l0 -12l5 3l0 0M13 9l5 3l0 0l-5 3l0 0;M13 15l-5 3l0 -12l5 3l0 6M13 9l5 3l0 0l-5 3l0 -6;M9 18l-2 0l0 -12l2 0l0 12M15 6l2 0l0 12l-2 0l0 -12" />
                        </path>
                      </svg>
                    </button>
                  </div>
                </div>
              </div>
            </div>

            <!-- 以后完善文件方面操作 -->
            <!-- <div class="divider"></div>
            <div class="detail-section">
              <h3 class="section-title">文件管理</h3>
              <div class="action-row">
                <button class="btn btn-secondary" @click="handleRename" :disabled="isWorking">
                  重命名
                </button>
                <button class="btn btn-secondary text-error" @click="handleDelete" :disabled="isWorking">
                  删除
                </button>
              </div>
            </div> -->

            <div v-if="detail.lyrics" class="divider"></div>

            <div v-if="detail.lyrics" class="detail-section">
              <h3 class="section-title">歌词</h3>
              <div class="lyrics-box">
                <pre>{{ detail.lyrics }}</pre>
              </div>
            </div>
          </div>
        </div>

        <div v-else class="text-center py-2xl">
          <p class="text-secondary">未找到本地音乐文件</p>
        </div>
      </div>
    </main>
  </div>
</template>

<script lang="ts" setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { http } from '@/api'
import type { ApiEnvelope } from '@/api/request'
import { toast } from '@/utils/toast'
import { getStoredMusicQuery } from '@/composables/useMusicQuery'

type LocalMusicDetail = {
  id: number
  music_id: string
  music_title?: string
  music_artist?: string
  music_album?: string
  quality?: string
  file_path?: string
  file_name?: string
  file_format?: string
  file_size?: number
  status: string
  error_message?: string
  lyrics?: string
}

const route = useRoute()
const router = useRouter()

const taskId = computed(() => Number(route.params.taskId))
const isLoading = ref(false)
const isWorking = ref(false)
const coverError = ref(false)
const detail = ref<LocalMusicDetail | null>(null)

const coverSrc = computed(() => `/local/music/cover/${taskId.value}`)
const audioSrc = computed(() => `/local/music/stream/${taskId.value}`)

const fetchDetail = async () => {
  if (!taskId.value) return
  isLoading.value = true
  try {
    const res = await http.get<ApiEnvelope<LocalMusicDetail>>(`/local/music/detail/${taskId.value}`)
    if (res.success && res.data.code === 200 && res.data.data) {
      detail.value = res.data.data
    } else {
      toast.show('加载本地音乐详情失败', 'error')
    }
  } catch {
    toast.show('加载本地音乐详情失败', 'error')
  } finally {
    isLoading.value = false
  }
}

const handleRename = async () => {
  if (!detail.value) return
  const newName = window.prompt('请输入新的文件名（包含扩展名）', detail.value.file_name || '')
  if (!newName) return

  isWorking.value = true
  try {
    const res = await http.post<ApiEnvelope<LocalMusicDetail>>('/local/music/rename', {
      task_id: detail.value.id,
      new_name: newName,
    })
    if (res.success && res.data.code === 200 && res.data.data) {
      detail.value = res.data.data
      coverError.value = false
      toast.show('重命名成功', 'success')
    } else {
      toast.show('重命名失败', 'error')
    }
  } catch {
    toast.show('重命名失败', 'error')
  } finally {
    isWorking.value = false
  }
}

const handleDelete = async () => {
  if (!detail.value) return
  const ok = window.confirm('确认删除本地文件？该操作不可恢复。')
  if (!ok) return

  isWorking.value = true
  try {
    const res = await http.post<ApiEnvelope<unknown>>('/local/music/delete', {
      task_id: detail.value.id,
    })
    if (res.success && res.data.code === 200) {
      toast.show('已删除本地文件', 'success')
      const storedQuery = getStoredMusicQuery()
      if (storedQuery) {
        router.push({ name: 'music', query: storedQuery })
      } else {
        router.push({ name: 'music' })
      }
    } else {
      toast.show('删除失败', 'error')
    }
  } catch {
    toast.show('删除失败', 'error')
  } finally {
    isWorking.value = false
  }
}

const formatSize = (bytes?: number) => {
  if (!bytes) return '-'
  const units = ['B', 'KB', 'MB', 'GB']
  let size = bytes
  let unitIndex = 0
  while (size >= 1024 && unitIndex < units.length - 1) {
    size /= 1024
    unitIndex++
  }
  return `${size.toFixed(1)} ${units[unitIndex]}`
}

const getStatusClass = (status: string) => {
  switch (status) {
    case 'completed':
      return 'badge-success'
    case 'downloading':
      return 'badge-primary'
    case 'failed':
      return 'badge-error'
    case 'cancelled':
      return 'badge-warning'
    default:
      return 'badge-secondary'
  }
}

onMounted(() => {
  fetchDetail()
})

const isDragging = ref(false)
const audioRef = ref<HTMLAudioElement | null>(null)
const isPlaying = ref(false)
const isInitial = ref(true) // 新增：标记是否为页面初始化状态
const currentTime = ref(0)
const duration = ref(0)

// 播放/暂停切换
const togglePlay = () => {
  if (!audioRef.value) return

  if (isInitial.value) {
    isInitial.value = false
  }

  if (isPlaying.value) {
    audioRef.value.pause()
    isPlaying.value = false
  } else {
    audioRef.value.play()
    isPlaying.value = true

    // ⭐ 只在真正开始播放时初始化 MediaSession
    updateMediaSession()
    updateMediaSessionPosition()
  }
}

// 更新进度条位置
const onTimeUpdate = () => {
  if (!audioRef.value || isDragging.value) return

  currentTime.value = audioRef.value.currentTime

  // ⭐ 核心：持续向 Android 汇报播放位置
  // const now = Date.now()
  // if (now - lastMediaUpdate > 500) {
  //   updateMediaSessionPosition()
  //   lastMediaUpdate = now
  // }
}

const updateMediaSessionPosition = () => {
  if (
    !('mediaSession' in navigator) ||
    !audioRef.value ||
    !isFinite(audioRef.value.duration)
  ) return

  navigator.mediaSession.setPositionState({
    duration: audioRef.value.duration,
    position: audioRef.value.currentTime,
    playbackRate: audioRef.value.playbackRate || 1
  })
}


// 获取歌曲总长度
const onLoadedMetadata = () => {
  if (!audioRef.value) return

  duration.value = audioRef.value.duration

  // ⭐ 拿到 duration 后立即告诉系统一次
  updateMediaSessionPosition()
}

// 拖动进度条跳转
const seekAudio = () => {
  if (audioRef.value) {
    audioRef.value.currentTime = currentTime.value
    isInitial.value=false
    isPlaying.value = true
    audioRef.value.play()
    updateMediaSession()
  }
}

// 4. 开始拖拽 (鼠标按下/手指触摸)
const onDragStart = () => {
  isDragging.value = true
}

// 5. 结束拖拽 (鼠标松开/手指离开)
const onDragEnd = () => {
  isDragging.value = false
  // 确保松手时，最后同步一次音频位置（双重保险）
  seekAudio()
}


// 格式化时间 00:00
const formatTime = (seconds: number) => {
  const min = Math.floor(seconds / 60)
  const sec = Math.floor(seconds % 60)
  return `${min.toString().padStart(2, '0')}:${sec.toString().padStart(2, '0')}`
}

// 更新系统媒体信息
const updateMediaSession = () => {
  if (!('mediaSession' in navigator) || !detail.value || !audioRef.value) return

  // 1️⃣ 元数据（只设置一次）
  navigator.mediaSession.metadata = new MediaMetadata({
    title: detail.value.music_title || '未知标题',
    artist: detail.value.music_artist || '未知艺术家',
    album: detail.value.music_album || '未知专辑',
    artwork: [
      { src: coverSrc.value, sizes: '512x512', type: 'image/png' }
    ]
  })

  try {
    navigator.mediaSession.setActionHandler('play', () => {
      audioRef.value?.play()
      isPlaying.value = true
    })

    navigator.mediaSession.setActionHandler('pause', () => {
      audioRef.value?.pause()
      isPlaying.value = false
    })

    // 显式注销上一首/下一首，把位置留给快进快退
    // 1. 将“上一首”拦截，改为“后退 10 秒”
    navigator.mediaSession.setActionHandler('previoustrack', () => {
      if (audioRef.value) {
        audioRef.value.currentTime = Math.max(audioRef.value.currentTime - 10, 0);
        updateMediaSessionPosition(); // 立即同步进度给系统
      }
    });

    // 2. 将“下一首”拦截，改为“前进 10 秒”
    navigator.mediaSession.setActionHandler('nexttrack', () => {
      if (audioRef.value) {
        audioRef.value.currentTime = Math.min(audioRef.value.currentTime + 10, audioRef.value.duration);
        updateMediaSessionPosition(); // 立即同步进度给系统
      }
    });

    navigator.mediaSession.setActionHandler('seekbackward', () => {
      if (audioRef.value) audioRef.value.currentTime -= 10
    })

    navigator.mediaSession.setActionHandler('seekforward', () => {
      if (audioRef.value) audioRef.value.currentTime += 10
    })

    navigator.mediaSession.setActionHandler('seekto', (details) => {
      if (details.seekTime !== undefined && audioRef.value) {
        audioRef.value.currentTime = details.seekTime
        updateMediaSessionPosition()
      }
    })
  } catch { }
}


// 【修改】样式计算现在依赖 localSliderValues 里的浮点数
function getRangeStyle(min: number, max: number, value: number): Record<string, string> {
  // 使用 getLocalSliderValue 获取精确的浮点数位置

  const clamped = Number.isFinite(value) ? Math.min(max, Math.max(min, value)) : min
  const percent = max === min ? 0 : ((clamped - min) / (max - min)) * 100

  return {
    '--range-percent': `${percent}%`,
    background: `linear-gradient(to right, var(--range-fill) 0%, var(--range-fill) ${percent}%, var(--range-track) ${percent}%, var(--range-track) 100%)`
  }
}
</script>

<style scoped lang="scss">
.detail-card {
  padding: var(--spacing-lg);

}

.detail-header {
  display: flex;
  gap: var(--spacing-lg);
}

.detail-cover {
  width: 140px;
  height: 140px;
  border-radius: 0.75rem;
  overflow: hidden;
  background: var(--bg-surface-hover);
  flex-shrink: 0;
  transition: all 0.3s ease;
  box-shadow: var(--shadow-lg);

  img {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }
}

.default-cover {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-tertiary);
  transition: all 0.3s ease;
}

.detail-meta {
  flex: 1;
  min-width: 0;
}

.detail-title {
  margin: 0 0 var(--spacing-xs);
  font-size: 1.6rem;
  font-weight: 650;
  color: var(--text-primary);
  line-height: 1.2;
}

.meta-row {
  margin-top: var(--spacing-sm);
  display: flex;
  align-items: center;

  /* 核心修复：允许换行 */
  flex-wrap: wrap;

  /* 间距控制：gap 是行间距和列间距的简写 */
  gap: 8px var(--spacing-sm);

  /* 限制最大宽度，防止在超大屏幕撑开太远 */
  width: 100%;

  /* 确保内部文字不会因为换行而显得参差不齐 */
  line-height: 1.2;
}


.meta-item {
  display: inline-flex;
  align-items: center;
  /* 在子元素之间自动添加 4px 间距 */
  gap: 4px;
}

.badge {
  /* 确保 Badge 在换行后不会被拉伸 */
  flex-shrink: 0;
}

.divider {
  height: 1px;
  background: var(--border-color);
  margin: var(--spacing-lg) 0;
  transition: all 0.3s ease;
}

.detail-section {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.section-title {
  margin: 0;
  font-size: 1rem;
  font-weight: 600;
  color: var(--text-primary);
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: var(--spacing-md);
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 4px;

  label {
    font-size: 0.85rem;
    color: var(--text-secondary);
  }
}

.mono {
  font-family: var(--font-mono);
}

.break-all {
  word-break: break-all;
}

.audio-player {
  width: 100%;
  color-scheme: var(--color-scheme);
}

.action-row {
  display: flex;
  gap: var(--spacing-md);
  flex-wrap: wrap;
}

.lyrics-box {
  border: 1px solid var(--border-color);
  border-radius: 0.75rem;
  background: var(--bg-surface);
  padding: var(--spacing-md);
  max-height: 320px;
  overflow: auto;
  transition: all 0.3s ease;

  pre {
    margin: 0;
    white-space: pre-wrap;
    line-height: 1.8;
    color: var(--text-secondary);
    font-family: inherit;
  }
}

.custom-player {
  background: var(--bg-surface-hover);
  border: 1px solid var(--border-color);
  padding: var(--spacing-md);
  border-radius: 1rem;

  .player-main {
    display: flex;
    align-items: center;
    gap: var(--spacing-md);
  }
}

.player-mini-cover {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  object-fit: cover;
  border: 2px solid var(--border-color);

  /* 1. 将动画定义移到基础类中，让它始终存在 */
  animation: rotate 10s linear infinite;

  /* 2. 默认状态设为"暂停" */
  animation-play-state: paused;

  /* 这是一个性能优化属性，告诉浏览器这玩意儿会动 */
  will-change: transform;

  /* 当有 rotating 类名时，状态改为"运行" */
  &.rotating {
    animation-play-state: running;
  }
}

@keyframes rotate {
  from {
    transform: rotate(0deg);
  }

  to {
    transform: rotate(360deg);
  }
}

@keyframes rotate {
  from {
    transform: rotate(0deg);
  }

  to {
    transform: rotate(360deg);
  }
}

.player-content {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.player-info {
  display: flex;
  flex-direction: column;

  .player-title {
    font-weight: 600;
    color: var(--text-primary);
    font-size: 1rem;
  }

  .player-artist {
    font-size: 0.85rem;
    color: var(--text-secondary);
  }
}

.progress-container {
  display: flex;
  align-items: center;
  gap: 10px;

  .time-stamp {
    font-size: 0.75rem;
    color: var(--text-tertiary);
    font-family: var(--font-mono);
    min-width: 35px;
  }

  .progress-bar {
    flex: 1;
    height: 4px;
    accent-color: var(--color-info);
    /* 进度条颜色 */
    cursor: pointer;
  }
}

.btn-play-toggle {
  background: var(--color-primary);
  color: var(--text-primary);
  border: none;
  width: 48px;
  height: 48px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 12px rgba(var(--color-primary-rgb), 0.3);

  &:hover {
    transform: scale(1.05);
  }

  &:active {
    transform: scale(0.95);
  }
}
</style>
