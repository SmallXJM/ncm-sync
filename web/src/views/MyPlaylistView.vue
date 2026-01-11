<template>
  <div class="page">
    <main>
      <div class="container">
        <div class="header">
          <p class="text-secondary">共 {{ playlists.length }} 个歌单</p>
          <p class="text-secondary">当前 {{ currentPage }}/{{ totalPages }} 页</p>
        </div>
        <div v-if="isLoading && !playlists.length" class="text-center py-2xl">
          <div class="loading-spinner mx-auto mb-md" style="width: 32px; height: 32px;"></div>
          <p class="text-secondary">正在获取歌单列表...</p>
        </div>

        <div v-else-if="playlists.length > 0" class="playlist-grid">
          <div v-for="playlist in displayPlaylists" :key="playlist.id" class="playlist-card">
            <div class="card-main">
              <div class="card-cover">
                <img :src="playlist.coverImgUrl" alt="cover" loading="lazy" />
                <div class="play-count">
                  <span>▶ {{ formatPlayCount(playlist.playCount) }}</span>
                </div>
              </div>
              <div class="card-info">
                <h3 class="card-title" :title="playlist.name">{{ playlist.name }}</h3>
                <div class="creator-info">
                  <img v-if="playlist.creator.avatarUrl" :src="playlist.creator.avatarUrl" class="creator-avatar"
                    alt="creator" />
                  <span>{{ playlist.creator.nickname }}</span>
                </div>
                <div class="track-count">{{ playlist.trackCount }} 首</div>
              </div>
            </div>

            <div class="card-footer">
              <button class="btn btn-secondary btn-sm btn-subscribe" @click="openSubscribe(playlist)">
                + 订阅
              </button>
            </div>
          </div>
        </div>

        <div v-else class="text-center py-2xl">
          <p class="text-secondary">暂无歌单数据</p>
        </div>

        <!-- Pagination -->
        <div v-if="totalPages > 1" class="pagination">
          <div class="btn-group">
            <button class="btn btn-secondary btn-sm icon-btn" :disabled="currentPage === 1" @click="currentPage = 1">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"
                stroke-linejoin="round">
                <polyline points="11 17 6 12 11 7"></polyline>
                <polyline points="18 17 13 12 18 7"></polyline>
              </svg>
            </button>

            <button class="btn btn-secondary btn-sm icon-btn" :disabled="currentPage === 1" @click="currentPage--">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"
                stroke-linejoin="round">
                <polyline points="15 18 9 12 15 6"></polyline>
              </svg>
            </button>

            <template v-for="page in visiblePages" :key="page">
              <span v-if="page === '...'" class="pagination-ellipsis">...</span>
              <button v-else class="btn btn-sm" :class="currentPage === page ? 'btn-primary' : 'btn-secondary'"
                @click="currentPage = page">
                {{ page }}
              </button>
            </template>

            <button class="btn btn-secondary btn-sm icon-btn" :disabled="currentPage === totalPages"
              @click="currentPage++">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"
                stroke-linejoin="round">
                <polyline points="9 18 15 12 9 6"></polyline>
              </svg>
            </button>

            <button class="btn btn-secondary btn-sm icon-btn" :disabled="currentPage === totalPages"
              @click="currentPage = totalPages">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"
                stroke-linejoin="round">
                <polyline points="13 17 18 12 13 7"></polyline>
                <polyline points="6 17 11 12 6 7"></polyline>
              </svg>
            </button>
          </div>
        </div>
      </div>
    </main>

    <!-- Subscription Drawer -->
    <div class="drawer-backdrop" :class="{ visible: isDrawerOpen }" @click="closeDrawer"></div>
    <aside class="drawer" :class="{ visible: isDrawerOpen }">
      <div class="drawer-header">
        <h3>配置订阅任务</h3>
        <button class="close-btn" @click="closeDrawer">×</button>
      </div>

      <div class="drawer-body" v-if="jobConfig">
        <div class="form-group">
          <label>订阅名称</label>
          <input v-model="jobConfig.job_name" class="input w-full" type="text" placeholder="输入订阅名称" />
        </div>

        <div class="form-group">
          <label>目标音质</label>
          <select v-model="jobConfig.target_quality" class="input w-full">
            <option value="hires">Hi-Res</option>
            <option value="lossless">无损 (Lossless)</option>
            <option value="exhigh">极高 (Exhigh)</option>
            <option value="standard">标准 (Standard)</option>
          </select>
        </div>

        <div class="form-section-title">歌曲数据配置</div>

        <div class="form-group row">
          <label>嵌入元数据</label>
          <label class="switch">
            <input type="checkbox" v-model="jobConfig.embed_metadata" />
            <span class="switch-track"></span>
            <span class="switch-handle"></span>
          </label>
        </div>

        <div class="form-group row">
          <label>嵌入封面</label>
          <label class="switch">
            <input type="checkbox" v-model="jobConfig.download_cover" />
            <span class="switch-track"></span>
            <span class="switch-handle"></span>
          </label>
        </div>

        <div class="form-group row">
          <label>嵌入歌词</label>
          <label class="switch">
            <input type="checkbox" v-model="jobConfig.download_lyrics" />
            <span class="switch-track"></span>
            <span class="switch-handle"></span>
          </label>
        </div>

        <div class="form-group">
          <label>文件名模板</label>
          <input v-model="jobConfig.filename_template" class="input w-full mono" type="text" />
          <p class="help-text">支持变量: {artist}, {title}, {album} 等</p>
        </div>

        <div class="form-group">
          <label>存储路径</label>
          <input v-model="jobConfig.storage_path" class="input w-full mono" type="text" />
          <p class="help-text">支持绝对路径或相对路径</p>
        </div>
      </div>

      <div class="drawer-footer">
        <button class="btn btn-secondary" @click="closeDrawer">取消</button>
        <button class="btn btn-primary" @click="submitJob" :disabled="isSubmitting">
          {{ isSubmitting ? '提交中...' : '添加订阅' }}
        </button>
      </div>
    </aside>

    <div v-if="toast.show" class="toast" :class="toast.type">
      <div class="toast-content">
        <span>{{ toast.message }}</span>
        <button class="toast-close" @click="hideToast">×</button>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { watch, computed, onMounted, reactive, ref } from 'vue'
import api from '@/api'
import type { CreateJobParams } from '@/api/ncm/download'

interface Playlist {
  id: number
  name: string
  coverImgUrl: string
  trackCount: number
  playCount: number
  creator: {
    nickname: string
    userId: number
    avatarUrl?: string
  }
}

interface Toast {
  show: boolean
  message: string
  type: 'info' | 'success' | 'warning' | 'error'
}

// State
const isLoading = ref(false)
const isSubmitting = ref(false)
const playlists = ref<Playlist[]>([])
const currentPage = ref(1)
const pageSize = 30
const isDrawerOpen = ref(false)
const globalConfig = ref<any>(null)

// Job Config State
const jobConfig = reactive<CreateJobParams>({
  job_name: '',
  job_type: 'playlist',
  source_type: 'playlist',
  source_id: '',
  source_name: '',
  source_owner_id: '',
  target_quality: 'lossless',
  embed_metadata: true,
  download_cover: true,
  download_lyrics: true,
  filename_template: '{artist} - {title}',
  storage_path: '',
})

// Toast State
const toast = reactive<Toast>({
  show: false,
  message: '',
  type: 'info',
})

// Computed
const totalPages = computed(() => Math.ceil(playlists.value.length / pageSize))
const displayPlaylists = computed(() => {
  const start = (currentPage.value - 1) * pageSize
  return playlists.value.slice(start, start + pageSize)
})

const visiblePages = computed(() => {
  const total = totalPages.value
  const current = currentPage.value
  const windowSize = 5

  // 总页数不够 5，全部显示
  if (total <= windowSize) {
    return Array.from({ length: total }, (_, i) => i + 1)
  }

  let start = current - Math.floor(windowSize / 2)
  let end = current + Math.floor(windowSize / 2)

  // 左边越界
  if (start < 1) {
    start = 1
    end = windowSize
  }

  // 右边越界
  if (end > total) {
    end = total
    start = total - windowSize + 1
  }

  const pages = []

  // 左边省略号
  if (start > 1) {
    pages.push("...")   // 省略
  }

  // 中间页码
  for (let i = start; i <= end; i++) {
    pages.push(i)
  }

  // 右边省略号
  if (end < total) {
    pages.push("...")   // 省略
  }

  return pages
})

import {  nextTick } from 'vue'

// 1. 定义引用 (名称需与模板中的 ref 一致)
const contentRef = ref<HTMLElement | null>(null)

// 2. 监听页码变化
watch(currentPage, async () => {
  await nextTick()
  // 查找 Layout 组件中定义的那个滚动容器类名
  const scrollContainer = document.querySelector('.layout__content')
  if (scrollContainer) {
    scrollContainer.scrollTo({
      top: 0,
      behavior: 'smooth'
    })
  }
})

// Methods
onMounted(async () => {
  await fetchGlobalConfig()
  await fetchPlaylists()
})

async function fetchGlobalConfig() {
  try {
    const res = await api.config.getConfig()
    if (res.success && res.data.code === 200) {
      globalConfig.value = res.data.data
    }
  } catch (e) {
    console.error('Failed to load global config', e)
  }
}

async function fetchPlaylists() {
  isLoading.value = true
  try {
    const res = await api.music.user.getUserPlaylist({ limit: 1000, uid: '' }) // uid empty means current user
    if (res.success && res.data.code === 200) {
      // The API returns { playlist: [...] }
      const data = res.data as any
      if (data && Array.isArray(data.playlist)) {
        playlists.value = data.playlist
      }
    } else {
      showToast('获取歌单失败: ' + (res.error || '未知错误'), 'error')
    }
  } catch (e) {
    showToast('获取歌单失败', 'error')
  } finally {
    isLoading.value = false
  }
}

function openSubscribe(playlist: Playlist) {
  // Reset config with defaults
  jobConfig.job_name = playlist.name
  jobConfig.source_id = String(playlist.id)
  jobConfig.source_name = playlist.name
  jobConfig.source_owner_id = String(playlist.creator.userId)

  // Set default storage path from global config
  if (globalConfig.value?.template?.music_dir_prefix_playlist) {
    // Simple template replacement for preview/default
    // Note: The backend will handle the actual replacement, but here we construct a default path
    // We replace {playlist_name} with actual name to give user a concrete path
    let path = globalConfig.value.template.music_dir_prefix_playlist
    // path = path.replace('{user_name}', playlist.creator.nickname) // Optional: might need user name
    // path = path.replace('{playlist_name}', playlist.name)

    // According to requirement: template.music_dir_prefix_playlist + "/" + current playlist name
    // But we need to be careful about slashes
    const prefix = path.endsWith('/') || path.endsWith('\\') ? path.slice(0, -1) : path
    jobConfig.storage_path = `${prefix}/${sanitizeFilename(playlist.name)}`
  } else {
    jobConfig.storage_path = `Downloads/${sanitizeFilename(playlist.name)}`
  }

  jobConfig.filename_template = globalConfig.value?.template?.filename || '{artist} - {title}'

  isDrawerOpen.value = true
}

function closeDrawer() {
  isDrawerOpen.value = false
}

async function submitJob() {
  if (!jobConfig.job_name || !jobConfig.storage_path) {
    showToast('请填写完整信息', 'warning')
    return
  }

  isSubmitting.value = true
  try {
    const res = await api.download.createJob(jobConfig)
    if (res.success && (res.data.code === 200 || res.data.code === 201)) {
      showToast('订阅成功', 'success')
      closeDrawer()
    } else {
      showToast('订阅失败: ' + (res.error || res.data?.message || '未知错误'), 'error')
    }
  } catch (e) {
    showToast('订阅失败', 'error')
  } finally {
    isSubmitting.value = false
  }
}

function formatPlayCount(count: number): string {
  if (count > 100000000) return (count / 100000000).toFixed(1) + '亿'
  if (count > 10000) return (count / 10000).toFixed(1) + '万'
  return String(count)
}

function sanitizeFilename(name: string): string {
  return name.replace(/[\\/:*?"<>|]/g, '_')
}

function showToast(message: string, type: Toast['type'] = 'info') {
  toast.message = message
  toast.type = type
  toast.show = true
  setTimeout(() => hideToast(), 3000)
}

function hideToast() {
  toast.show = false
}
</script>

<style scoped lang="scss">

.container {
  margin: 0 auto;
}


.header {
  display: flex;
  align-items: center;
  gap: var(--spacing-lg);
  margin-bottom: var(--spacing-lg);

  p {
    font-size: 1rem;
    font-weight: 500;
  }
}


.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  margin-top: var(--spacing-lg);
}

.btn-group {
  display: flex;
  gap: var(--spacing-sm);
  /* 按钮之间的间距 */

  .btn {
    font-weight: 550;
    width: 36px;
    height: 36px;
  }

  /* 让按钮支持 Flex 布局以对齐 SVG */
  .icon-btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    padding: 0;
    /* 移除默认内边距，手动控制宽高 */
  }

  /* 控制 SVG 的粗细和大小 */
  .icon-btn svg {
    width: 16px;
    height: 16px;
    stroke-width: 2.5px;
    /* 可以根据喜好调整线条粗细 */
  }
}



.pagination-ellipsis {
  padding: 0 0.5rem;
  color: var(--text-muted);
  line-height: 2;
}



/* Drawer Styles - assuming these are not in components.scss or need to be local */
.drawer-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(4px);
  z-index: 100;
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.3s ease;

  &.visible {
    opacity: 1;
    pointer-events: auto;
  }
}

.drawer {
  position: fixed;
  top: 0;
  right: 0;
  bottom: 0;
  width: 400px;
  max-width: 90vw;
  background: var(--bg-surface);
  box-shadow: var(--shadow-2xl);
  z-index: 101;
  transform: translateX(100%);
  transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  display: flex;
  flex-direction: column;

  &.visible {
    transform: translateX(0);
  }
}

.drawer-header {
  padding: var(--spacing-lg);
  border-bottom: 1px solid var(--border-color);
  display: flex;
  justify-content: space-between;
  align-items: center;

  h3 {
    font-size: 1.25rem;
    font-weight: 600;
    margin: 0;
  }

  .close-btn {
    font-size: 1.5rem;
    background: none;
    border: none;
    cursor: pointer;
    color: var(--text-secondary);

    &:hover {
      color: var(--text-primary);
    }
  }
}

.drawer-body {
  flex: 1;
  overflow-y: auto;
  padding: var(--spacing-lg);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
}

.drawer-footer {
  padding: var(--spacing-lg);
  border-top: 1px solid var(--border-color);
  display: flex;
  justify-content: flex-end;
  gap: var(--spacing-md);
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);

  label {
    font-weight: 500;
    color: var(--text-primary);
  }

  &.row {
    flex-direction: row;
    justify-content: space-between;
    align-items: center;
  }
}

.form-section-title {
  font-weight: 600;
  color: var(--text-secondary);
  font-size: 0.9rem;
  margin-top: var(--spacing-md);
  padding-bottom: var(--spacing-xs);
  border-bottom: 1px solid var(--border-color);
}

.help-text {
  font-size: 0.85rem;
  color: var(--text-tertiary);
  margin: 0;
}

.toast {
  position: fixed;
  top: 2rem;
  left: 50%;
  transform: translateX(-50%);
  z-index: 200;

  .toast-content {
    background: var(--bg-surface);
    color: var(--text-primary);
    padding: var(--spacing-md) var(--spacing-lg);
    border-radius: 2rem;
    box-shadow: var(--shadow-lg);
    display: flex;
    align-items: center;
    gap: var(--spacing-md);
    border: 1px solid var(--border-color);
  }

  &.success .toast-content {
    border-color: var(--color-success);
  }

  &.error .toast-content {
    border-color: var(--color-error);
  }

  &.warning .toast-content {
    border-color: var(--color-warning);
  }

  .toast-close {
    background: none;
    border: none;
    cursor: pointer;
    font-size: 1.2rem;
    color: var(--text-secondary);

    &:hover {
      color: var(--text-primary);
    }
  }
}
</style>
