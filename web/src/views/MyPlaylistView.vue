<template>
  <div class="page">
    <main>
      <div class="container">
        <aside class="glass-card config-sidebar">
          <nav class="config-nav">
            <button v-for="group in selectGroups" :key="group.id" class="config-nav-item"
              :class="{ 'active': group.id == activeGroupId }" @click="activeGroupId = group.id" type="button">
              <span class="config-nav-item-text">{{ group.name }}</span>
            </button>
          </nav>
        </aside>
        <div class="header">
          <!-- <p class="text-secondary">共 {{ playlists.length }} 个歌单</p> -->
          <!-- <p class="text-secondary">{{ selectGroups.find(g => g.id == activeGroupId)?.name }}有 {{ showPlaylists.length }} 个</p> -->
          <p class="text-secondary">共 {{ showPlaylists.length }} 个歌单</p>
          <p class="text-secondary">当前 {{ currentPage }} / {{ totalPages }} 页</p>
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
              <div v-if="playlist.privacy == 10" class="card-footer-privacy">
                <!-- 小锁图标 -->
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24">
                  <path fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"
                    stroke-width="2"
                    d="M4 8V6a2 2 0 0 1 2-2h2M4 16v2a2 2 0 0 0 2 2h2m8-16h2a2 2 0 0 1 2 2v2m-4 12h2a2 2 0 0 0 2-2v-2M8 12a1 1 0 0 1 1-1h6a1 1 0 0 1 1 1v3a1 1 0 0 1-1 1H9a1 1 0 0 1-1-1zm2-1V9a2 2 0 1 1 4 0v2" />
                </svg>
                <p class="text-secondary">隐私歌单</p>
              </div>
              <button v-if="!isSubscribe(playlist)" class="btn btn-secondary btn-sm btn-subscribe"
                @click="openSubscribe(playlist)">
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24">
                  <path fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"
                    stroke-width="2" d="M5 12h14m-7 7V5" />
                </svg>
                订阅
              </button>

              <button v-else class="btn btn-secondary btn-sm btn-subscribe" disabled>
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24">
                  <path fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"
                    stroke-width="2" d="M5 11.917L9.724 16.5L19 7.5" />
                </svg>
                已订阅
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
                @click="currentPage = Number(page)">
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
        <div class="header-content">
          <h3>订阅歌单</h3>
          <div style="margin-top: 8px;">
            <p class="help-text">即将订阅歌单 "{{ jobConfig.source_name }}"</p>
            <p class="help-text">请配置以下信息：</p>
          </div>
        </div>
        <button class="close-btn" @click="closeDrawer">×</button>
      </div>

      <div class="drawer-body" v-if="jobConfig">
        <!-- <div class="form-group">
          <label>订阅名称</label>
          <input v-model="jobConfig.job_name" class="input w-full" type="text" placeholder="输入订阅名称" />
        </div> -->

        <div class="form-group">
          <label>目标音质</label>
          <select v-model="jobConfig.target_quality" class="input w-full">
            <!-- standard, exhigh, lossless, hires, jyeffect(高清环绕声), sky(沉浸环绕声), jymaster(超清母带) -->
            <option value="dolby">杜比全景声 (Dolby)</option>
            <option value="jymaster">超清母带 (Jymaster)</option>
            <option value="sky">沉浸环绕声 (Sky)</option>
            <option value="jyeffect">高清环绕声 (Jyeffect)</option>
            <option value="hires">高解析度无损 (Hi-Res)</option>
            <option value="lossless">无损 (Lossless)</option>
            <option value="exhigh">极高 (Exhigh)</option>
            <option value="standard">标准 (Standard)</option>
          </select>
          <p class="help-text">目标音质为请求的最高音质，如下载音乐未包含该音质，会由服务器自动向下兼容</p>
          <p class="help-text">推荐选择：高解析度无损</p>

        </div>

        <!-- <div class="form-section-title">歌曲数据配置</div> -->

        <div class="form-group">
          <div class="form-group row">
            <label>嵌入标签</label>
            <label class="switch">
              <input type="checkbox" v-model="jobConfig.embed_metadata" />
              <span class="switch-track"></span>
              <span class="switch-handle"></span>
            </label>
          </div>
          <p class="help-text">包含音乐基本数据，如艺术家、标题、专辑等</p>
        </div>

        <div class="form-group">
          <div class="form-group row">
            <label>嵌入封面</label>
            <label class="switch">
              <input type="checkbox" v-model="jobConfig.embed_cover" />
              <span class="switch-track"></span>
              <span class="switch-handle"></span>
            </label>
          </div>
          <p class="help-text">嵌入音乐专辑封面</p>
        </div>

        <div class="form-group">
          <div class="form-group row">
            <label>嵌入歌词</label>
            <label class="switch">
              <input type="checkbox" v-model="jobConfig.embed_lyrics" />
              <span class="switch-track"></span>
              <span class="switch-handle"></span>
            </label>
          </div>
          <p class="help-text">嵌入音乐同步歌词</p>
          <p class="help-text">支持Potplayer，Navidrome等播放器</p>
        </div>

        <div class="form-group">
          <label>音乐名模板</label>
          <input v-model="jobConfig.filename_template" class="input w-full mono" type="text" />
          <p class="help-text">详细定义见：[设置 - 模板设置 - 默认音乐名模板]</p>
        </div>

        <div class="form-group">
          <!-- 存储路径 红色* -->
          <label>存储路径 <span style="color: red;">*</span></label>

          <input v-model="jobConfig.storage_path" class="input w-full mono" type="text" />
          <p class="help-text">该路径将存放同步的音乐文件</p>
          <p class="help-text">路径示例：</p>
          <p class="help-text" style="margin-left: 1rem;">Mac/Linux: /home/downloads/歌单</p>
          <p class="help-text" style="margin-left: 1rem;">Windows: C:\Downloads\歌单</p>
        </div>
      </div>

      <div class="drawer-footer">
        <button class="btn btn-secondary" @click="closeDrawer">取消</button>
        <button class="btn btn-primary" @click="submitJob" :disabled="isSubmitting">
          {{ isSubmitting ? '提交中...' : '添加订阅' }}
        </button>
      </div>
    </aside>

  </div>
</template>

<script lang="ts" setup>
import { watch, computed, onMounted, reactive, ref } from 'vue'
import api from '@/api'
import type { Playlist } from '@/api/ncm/music/user'
import type { CreateJobParams, DownloadJobItem } from '@/api/ncm/download'
import type { NcmConfig } from '@/api/ncm/config'
import { useRoute, useRouter } from 'vue-router'
import { nextTick } from 'vue'
import { toast } from '@/utils/toast'

const route = useRoute()
const router = useRouter()


interface Toast {
  show: boolean
  message: string
  type: 'info' | 'success' | 'warning' | 'error'
}

// State
const isLoading = ref(false)
const isSubmitting = ref(false)
const selectGroups = ref([
  {
    id: 1,
    name: '创建的歌单',
  },
  {
    id: 2,
    name: '收藏的歌单',
  },
])
const activeGroupId = ref(Number(route.query.group) || 1)

const playlists = ref<Playlist[]>([])
const pageSize = 30
const currentPage = ref(Number(route.query.page) || 1)
const isDrawerOpen = ref(false)
const globalConfig = ref<NcmConfig | null>(null)
const DownloadJob = ref<DownloadJobItem[] | null>(null)

// Job Config State
const jobConfig = reactive<CreateJobParams>({
  job_name: '',
  job_type: 'playlist',
  source_type: 'playlist',
  source_id: '',
  source_name: '',
  source_owner_id: '',
  target_quality: 'hires',
  embed_metadata: true,
  embed_cover: true,
  embed_lyrics: true,
  filename_template: '{artist} - {title}',
  storage_path: '',
})


// Computed
const showPlaylists = computed(() => {
  if (activeGroupId.value === 1) {
    return playlists.value.filter(p => p.subscribed === false)
  }
  return playlists.value.filter(p => p.subscribed === true)
})

const totalPages = computed(() => Math.ceil(showPlaylists.value.length / pageSize))

console.log('currentPage', currentPage.value, totalPages.value, showPlaylists.value.length,Number(route.query.page))
const displayPlaylists = computed(() => {
  const start = (currentPage.value - 1) * pageSize
  return showPlaylists.value.slice(start, start + pageSize)
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



// Methods
onMounted(async () => {
  console.log('Component Mounted', new Date().getTime());
  // fetchGlobalConfig(),
  await fetchDownloadJob()
  await fetchPlaylists()
  
  // 修正正确页码逻辑
  if (Number(route.query.group) < 1) {
    activeGroupId.value = 1
  }
  if (Number(route.query.group) > selectGroups.value.length) {
    activeGroupId.value = selectGroups.value.length
  }
  if (Number(route.query.page) < 1) {
    currentPage.value = 1
  }
  if (Number(route.query.page) > totalPages.value) {
    currentPage.value = totalPages.value
  }

  updateUrl()

})


const updateUrl = () => {
  const query = { ...route.query }

  if (activeGroupId.value === 1) {
    delete query.group
  } else {
    query.group = activeGroupId.value.toString()
  }

  if (currentPage.value === 1) {
    delete query.page
  } else {
    query.page = currentPage.value.toString()
  }

  router.push({ query })
}


watch(activeGroupId, (newVal, oldVal) => {
  if (newVal !== oldVal) {
    currentPage.value = 1 // 切换分类时强制回第一页
    updateUrl()
  }
})

watch(currentPage, async (newVal, oldVal) => {
  if (newVal === oldVal) return
  // 更新 URL (如果不是通过路由变化触发的)
  updateUrl()

  // 滚动到顶部逻辑
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

// 监听路由 query 的变化，确保点击后退键时 UI 同步更新
watch(() => route.query, (newQuery) => {
  const qGroup = Number(newQuery.group) > selectGroups.value.length ? selectGroups.value.length : Number(newQuery.group) || 1
  const qPage = Number(newQuery.page) > totalPages.value ? totalPages.value : Number(newQuery.page) || 1

  
  if (activeGroupId.value !== qGroup) {
    activeGroupId.value = qGroup
  }
  if (currentPage.value !== qPage) {
    currentPage.value = qPage
  }




}, { deep: true })



async function fetchGlobalConfig() {
  try {
    const res = await api.config.getConfig()
    if (res.success && res.data.code === 200) {
      globalConfig.value = res.data.data || null
    }
  } catch (e) {
    console.error('Failed to load global config', e)
  }
}

async function fetchDownloadJob() {
  try {
    const res = await api.download.getJobList()
    if (res.success && res.data.code === 200) {
      // 断言 res.data.data 为包含 jobs 字段的对象
      DownloadJob.value = (res.data.data as { jobs: DownloadJobItem[] }).jobs
    }
  } catch (e) {
    console.error('Failed to load download job', e)
  }
}

async function fetchPlaylists() {
  if (isLoading.value) return
  console.log('fetchPlaylists called')
  isLoading.value = true
  try {
    const res = await api.music.user.getUserPlaylist({ limit: 1000, uid: '' }) // uid empty means current user
    if (res.success && res.data.code === 200) {
      // The API returns { playlist: [...] }
      const data = res.data
      if (data && Array.isArray(data.playlist)) {
        playlists.value = data.playlist || []
      } else {
        playlists.value = []
      }
    } else {
      toast.show('获取歌单失败: ' + (res.success ? res.data.code : res.error || '未知错误'), 'error')
    }
  } catch (e) {
    toast.show('获取歌单失败:' + (e as Error).message, 'error')
  } finally {
    isLoading.value = false
  }
}

function isSubscribe(playlist: Playlist) {
  return DownloadJob.value?.some((job: DownloadJobItem) => job.job_type === 'playlist' && job.source_id === String(playlist.id))
}

function openSubscribe(playlist: Playlist) {
  fetchGlobalConfig().then(() => {
    //等待全局配置加载完成
    // Reset config with defaults
    jobConfig.job_name = playlist.name
    jobConfig.source_id = String(playlist.id)
    jobConfig.source_name = playlist.name
    jobConfig.source_owner_id = String(playlist.creator.userId)
    jobConfig.target_quality = globalConfig.value?.subscription?.target_quality || 'hires'
    jobConfig.embed_metadata = globalConfig.value?.subscription?.embed_metadata
    jobConfig.embed_cover = globalConfig.value?.subscription?.embed_cover
    jobConfig.embed_lyrics = globalConfig.value?.subscription?.embed_lyrics

    // Set default storage path from global config
    if (globalConfig.value?.subscription?.music_dir_playlist) {
      // Simple template replacement for preview/default
      // Note: The backend will handle the actual replacement, but here we construct a default path
      // We replace {playlist_name} with actual name to give user a concrete path
      const path = globalConfig.value.subscription.music_dir_playlist
      // path = path.replace('{user_name}', playlist.creator.nickname) // Optional: might need user name
      // path = path.replace('{playlist_name}', playlist.name)

      // According to requirement: template.music_dir_prefix_playlist + "/" + current playlist name
      // But we need to be careful about slashes
      // 歌单/{user_name}/{playlist_name}/SmallXJM喜欢的音乐
      // const prefix = path.endsWith('/') || path.endsWith('\\') ? path.slice(0, -1) : path
      const prefix = path.endsWith('/') || path.endsWith('\\') ? path.slice(0, -1) : path

      // jobConfig.storage_path = `${prefix}/${sanitizeFilename(playlist.name)}`
      jobConfig.storage_path = prefix
        .replace('{user_name}', playlist.creator.nickname)
        .replace('{playlist_name}', playlist.name)

    } else {
      jobConfig.storage_path = `Downloads/${sanitizeFilename(playlist.name)}`
    }

    jobConfig.filename_template = globalConfig.value?.subscription?.filename || jobConfig.filename_template
  })
  isDrawerOpen.value = true
  // drawer-body 到最顶层
  const scrollContainer = document.querySelector('.drawer-body')
  if (scrollContainer) {
    scrollContainer.scrollTo({
      top: 0,
      behavior: 'smooth'
    })
  }
}

function closeDrawer() {
  isDrawerOpen.value = false
}

async function submitJob() {
  if (!jobConfig.job_name || !jobConfig.storage_path) {
    toast.show('请填写完整信息', 'warning')
    return
  }

  isSubmitting.value = true
  try {
    const res = await api.download.createJob(jobConfig)
    if (res.success && (res.data.code === 200 || res.data.code === 201)) {
      toast.show(`订阅歌单 "${jobConfig.job_name}"成功`, 'success')
      closeDrawer()
      fetchDownloadJob()
    } else {
      // 访问 res.data.message 前先判断 res.success
      const message = res.success ? res.data.message : res.error
      toast.show('订阅失败: ' + (message || '未知错误'), 'error')
    }
  } catch (e) {
    toast.show('订阅失败:' + (e as Error).message, 'error')
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

</script>

<style scoped lang="scss">
.container {
  margin: 0 auto;
}


.header {
  display: flex;
  align-items: center;
  gap: var(--spacing-lg);
  margin-top: var(--spacing-lg);
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
  background: var(--bg-modal);
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
  align-items: flex-start; // 改为顶部对齐，防止按钮被文字撑到中间

  .header-content {
    display: flex;
    flex-direction: column; // 文字上下排列
    gap: var(--spacing-xs); // h3 和 p 之间的间距

    h3 {
      font-size: 1.25rem;
      font-weight: 600;
      margin: 0;
      line-height: 1.2;
    }

    .help-text {
      font-size: 0.875rem;
      color: var(--text-secondary);
    }
  }

  .close-btn {
    font-size: 1.5rem;
    line-height: 1; // 确保按钮点击区域和图标对齐
    background: none;
    border: none;
    cursor: pointer;
    color: var(--text-secondary);
    padding: 4px; // 增加点击感
    margin-top: -4px; // 微调位置与标题齐平

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
</style>
