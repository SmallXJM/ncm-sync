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
                <img v-if="!coverError" :src="coverSrc" alt="cover" loading="lazy" @error="coverError = true" />
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
                  <span class="text-tertiary" v-if="detail.quality">· {{ detail.quality }}</span>
                  <span class="text-tertiary" v-if="detail.file_size">· {{ formatSize(detail.file_size) }}</span>
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
              <h3 class="section-title">播放</h3>
              <audio class="audio-player" controls :src="audioSrc"></audio>
            </div>

            <div class="divider"></div>

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
            </div>

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

// 说明：本详情页仅面向本地已下载文件；不再依赖任何 NCM(song/detail、lyric) 网络请求。
//      音频播放、封面与文件管理均通过本地文件接口完成。

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
      router.push({ name: 'music' })
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
</script>

<style scoped lang="scss">
.detail-layout {
  margin-top: var(--spacing-lg);
}

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
  gap: var(--spacing-sm);
}

.divider {
  height: 1px;
  background: var(--border-color);
  margin: var(--spacing-lg) 0;
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

  pre {
    margin: 0;
    white-space: pre-wrap;
    line-height: 1.8;
    color: var(--text-secondary);
    font-family: inherit;
  }
}
</style>
