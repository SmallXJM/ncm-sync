<template>
  <div class="page">
    <main>
      <div class="container">
        <!-- Sidebar -->
        <aside class="glass-card config-sidebar">
          <div class="config-sidebar-header">
            <h3 class="config-sidebar-title">订阅任务</h3>
          </div>
          <nav class="config-nav">
            <button class="config-nav-item" :class="{ 'active': activeJobId === 0 }" @click="selectJob(0)"
              type="button">
              <span class="config-nav-item-text">所有任务</span>
            </button>
            <button v-for="job in jobs" :key="job.id" class="config-nav-item"
              :class="{ 'active': job.id === activeJobId }" @click="selectJob(job.id)" type="button">
              <span class="config-nav-item-text">{{ job.job_name }}</span>
            </button>
          </nav>
        </aside>

        <!-- Main Content -->
        <div class="main-content">
          <!-- Filters & Search -->
          <div class="glass-card mb-lg p-md">
            <div class="search-form" style="margin-bottom: 0;">
              <div class="search-input-wrapper" style="flex: 1;">
                <input v-model="searchKeyword" @keyup.enter="handleSearch" type="text" class="search-input"
                  placeholder="搜索音乐标题、艺术家、专辑..." />
              </div>

              <select v-model="filterStatus" class="input" style="width: auto;" @change="handleSearch">
                <option value="">所有状态</option>
                <option value="pending">等待中 (Pending)</option>
                <option value="downloading">下载中 (Downloading)</option>
                <option value="processing">处理中 (Processing)</option>
                <option value="completed">已完成 (Completed)</option>
                <option value="failed">失败 (Failed)</option>
                <option value="cancelled">已取消 (Cancelled)</option>
              </select>

              <button class="btn btn-primary" @click="handleSearch">
                搜索
              </button>
              <button class="btn btn-secondary" @click="resetFilters">
                重置
              </button>
            </div>
          </div>

          <!-- Stats & Pagination Info -->
          <div class="header">
            <p class="text-secondary">共 {{ totalTasks }} 首音乐</p>
            <div class="header-right">
              <p class="text-secondary">当前 {{ currentPage }} / {{ totalPages }} 页</p>
              <select v-model.number="pageSize" class="input page-size-select" @change="handlePageSizeChange">
                <option :value="10">每页 10 首</option>
                <option :value="20">每页 20 首</option>
                <option :value="50">每页 50 首</option>
              </select>
            </div>
          </div>

          <!-- Loading State -->
          <div v-if="isLoading" class="text-center py-2xl">
            <div class="loading-spinner mx-auto mb-md" style="width: 32px; height: 32px;"></div>
            <p class="text-secondary">正在加载音乐列表...</p>
          </div>

          <!-- Task Grid (Card Layout) -->
          <div v-else-if="tasks.length > 0" class="playlist-grid">
            <div v-for="task in tasks" :key="task.id" class="playlist-card">
              <div class="card-main">
                <div class="card-cover">
                  <img v-if="task.status === 'completed' && task.file_path && !coverErrorTaskIds.has(task.id)"
                    :src="getCoverSrc(task.id)" alt="cover" loading="lazy" @error="handleCoverError(task.id)" />
                  <div v-else class="default-cover">
                    <svg xmlns="http://www.w3.org/2000/svg" width="40" height="40" viewBox="0 0 24 24" fill="none"
                      stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                      <path d="M9 18V5l12-2v13"></path>
                      <circle cx="6" cy="18" r="3"></circle>
                      <circle cx="18" cy="16" r="3"></circle>
                    </svg>
                  </div>
                  
                  <!-- Status Overlay on Cover -->
                  <div class="status-overlay" :class="getStatusClass(task.status)">
                    <span>{{ getStatusText(task.status) }}</span>
                  </div>
                </div>
                
                <div class="card-info">
                  <h3 class="card-title" :title="task.music_title">{{ task.music_title || '未知标题' }}</h3>
                  <div class="creator-info">
                    <span>{{ task.music_artist || '未知艺术家' }}</span>
                  </div>
                  <div class="track-count">{{ task.music_album || '未知专辑' }}</div>
                  
                  <div class="item-extra mt-xs">
                     <span class="text-tertiary" v-if="task.quality">{{ task.quality }}</span>
                     <span class="text-tertiary" v-if="task.file_size"> · {{ formatSize(task.file_size) }}</span>
                  </div>
                </div>
              </div>

              <div class="card-footer">
                <div v-if="task.error_message" class="card-footer-error" :title="task.error_message">
                   <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--color-error)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>
                   <span class="text-error text-sm text-truncate" style="max-width: 120px;">{{ task.error_message }}</span>
                </div>
                <div v-else></div> <!-- Spacer -->

                <div class="action-buttons">
                   <button v-if="['failed', 'cancelled'].includes(task.status)" class="btn btn-sm btn-secondary"
                    @click.stop="resetTask(task)" :disabled="isProcessing(task.id)">
                    {{ isProcessing(task.id) ? '处理中...' : '重试' }}
                  </button>
                  <button class="btn btn-sm btn-primary ml-sm" @click="goDetail(task)">
                    详情
                  </button>
                </div>
              </div>
            </div>
          </div>

          <div v-else class="text-center py-2xl">
            <p class="text-secondary">暂无音乐任务数据</p>
          </div>

          <!-- Pagination -->
          <AppPagination
            :total-items="totalTasks"
            :current-page="currentPage"
            :page-size="pageSize"
            @page-change="changePage"
          />
        </div>
      </div>
    </main>
  </div>
</template>

<script lang="ts" setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '@/api'
import type { DownloadJobItem, DownloadTaskItem } from '@/api/ncm/download'
import { toast } from '@/utils/toast'
import AppPagination from '@/components/AppPagination.vue'

// 说明：该页面只展示并管理本地已下载文件；不再发起 NCM(song/detail、lyric) 等网络请求

const route = useRoute()
const router = useRouter()

// State
const jobs = ref<DownloadJobItem[]>([])
const tasks = ref<DownloadTaskItem[]>([])
const activeJobId = ref(Number(route.query.job_id) || 0)
const searchKeyword = ref(route.query.keyword as string || '')
const filterStatus = ref((route.query.status as string) || 'completed')
const currentPage = ref(Number(route.query.page) || 1)
const totalTasks = ref(0)
const pageSize = ref(20)
const isLoading = ref(false)
const processingTasks = ref<Set<number>>(new Set())
const coverErrorTaskIds = ref<Set<number>>(new Set())

// Computed
const totalPages = computed(() => Math.ceil(totalTasks.value / pageSize.value))

// Methods
const fetchJobs = async () => {
  try {
    const res = await api.download.getJobList()
    if (res.success && res.data.code === 200) {
      jobs.value = (res.data.data as { jobs: DownloadJobItem[] }).jobs
    }
  } catch (e) {
    console.error('Failed to load jobs', e)
  }
}

const fetchTasks = async () => {
  isLoading.value = true
  try {
    const params = {
      page: currentPage.value,
      limit: pageSize.value,
      job_id: activeJobId.value || undefined,
      status: filterStatus.value || undefined,
      keyword: searchKeyword.value || undefined
    }
    const res = await api.download.getTaskList(params)
    if (res.success && res.data.code === 200) {
      if (res.data.data) {
        tasks.value = res.data.data.tasks
        totalTasks.value = res.data.data.total
      }
    } else {
      toast.show('获取任务列表失败', 'error')
    }
  } catch (e) {
    console.error('Failed to load tasks', e)
    toast.show('获取任务列表失败', 'error')
  } finally {
    isLoading.value = false
  }
}

const updateUrl = () => {
  const query: any = { ...route.query }

  if (activeJobId.value === 0) delete query.job_id
  else query.job_id = activeJobId.value

  if (!searchKeyword.value) delete query.keyword
  else query.keyword = searchKeyword.value

  if (!filterStatus.value) delete query.status
  else query.status = filterStatus.value

  if (currentPage.value === 1) delete query.page
  else query.page = currentPage.value

  router.push({ query })
}

const handleSearch = () => {
  currentPage.value = 1
  updateUrl()
  fetchTasks()
}

const handlePageSizeChange = () => {
  currentPage.value = 1
  updateUrl()
  fetchTasks()
}

const resetFilters = () => {
  searchKeyword.value = ''
  filterStatus.value = ''
  activeJobId.value = 0
  currentPage.value = 1
  updateUrl()
  fetchTasks()
}

const selectJob = (id: number) => {
  activeJobId.value = id
  currentPage.value = 1
  updateUrl()
}

const changePage = (page: number) => {
  currentPage.value = page
  updateUrl()
}

const resetTask = async (task: DownloadTaskItem) => {
  if (processingTasks.value.has(task.id)) return
  processingTasks.value.add(task.id)

  try {
    const res = await api.download.resetTask(task.id)
    if (res.success && res.data.code === 200) {
      toast.show('任务已重置', 'success')
      task.status = 'pending'
      task.error_message = ''
    } else {
      toast.show('重置失败', 'error')
    }
  } catch (e) {
    toast.show('重置失败', 'error')
  } finally {
    processingTasks.value.delete(task.id)
  }
}

const isProcessing = (taskId: number) => processingTasks.value.has(taskId)

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
    case 'completed': return 'badge-success'
    case 'downloading': return 'badge-primary'
    case 'failed': return 'badge-error'
    case 'cancelled': return 'badge-warning'
    default: return 'badge-secondary'
  }
}

const getStatusText = (status: string) => {
   const map: Record<string, string> = {
      'pending': '等待中',
      'downloading': '下载中',
      'processing': '处理中',
      'completed': '已完成',
      'failed': '失败',
      'cancelled': '已取消'
   }
   return map[status] || status
}

const goDetail = (task: DownloadTaskItem) => {
  router.push({ name: 'music-detail', params: { taskId: String(task.id) } })
}

const getCoverSrc = (taskId: number) => `/local/music/cover/${taskId}`

const handleCoverError = (taskId: number) => {
  coverErrorTaskIds.value.add(taskId)
}

// Watchers
watch(() => route.query, (newQuery) => {
  activeJobId.value = Number(newQuery.job_id) || 0
  searchKeyword.value = (newQuery.keyword as string) || ''
  filterStatus.value = (newQuery.status as string) || 'completed'
  currentPage.value = Number(newQuery.page) || 1
  fetchTasks()
}, { deep: true })

onMounted(() => {
  fetchJobs()
  fetchTasks()
})
</script>

<style scoped lang="scss">
.main-content {
  flex: 1;
  min-width: 0;
}

.header-right {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.page-size-select {
  width: auto;
}

/* Custom styles for Music Cards extending base components */
.playlist-card {
   /* Ensure footer stays at bottom */
   display: flex;
   flex-direction: column;
   justify-content: space-between;
}

.card-cover {
   /* Adjust for status overlay */
   position: relative;
}

.default-cover {
   width: 100%;
   height: 100%;
   display: flex;
   align-items: center;
   justify-content: center;
   background: var(--bg-surface-hover);
   color: var(--text-tertiary);
   
   &.large {
      width: 120px;
      height: 120px;
      border-radius: 0.75rem;
   }
}

.status-overlay {
   position: absolute;
   bottom: 4px;
   right: 4px;
   padding: 2px 6px;
   border-radius: 4px;
   font-size: 0.75rem;
   font-weight: 600;
   color: white;
   backdrop-filter: blur(4px);
   
   &.badge-success { background: rgba(var(--color-success-rgb), 0.8); }
   &.badge-primary { background: rgba(var(--color-primary-rgb), 0.8); }
   &.badge-error { background: rgba(var(--color-error-rgb), 0.8); }
   &.badge-warning { background: rgba(var(--color-warning-rgb), 0.8); }
   &.badge-secondary { background: rgba(0,0,0, 0.6); }
}

.card-footer {
   display: flex;
   justify-content: space-between;
   align-items: center;
}

.card-footer-error {
   display: flex;
   align-items: center;
   gap: 4px;
   flex: 1;
   min-width: 0;
}

.action-buttons {
   display: flex;
   align-items: center;
}

.text-truncate {
   overflow: hidden;
   text-overflow: ellipsis;
   white-space: nowrap;
}
.mt-xs { margin-top: var(--spacing-xs); }
.ml-sm { margin-left: var(--spacing-sm); }
</style>
