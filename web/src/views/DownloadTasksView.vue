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
            <p class="text-secondary">共 {{ totalTasks }} 个任务</p>
            <p class="text-secondary">当前 {{ currentPage }} / {{ totalPages }} 页</p>
          </div>

          <!-- Loading State -->
          <div v-if="isLoading" class="text-center py-2xl">
            <div class="loading-spinner mx-auto mb-md" style="width: 32px; height: 32px;"></div>
            <p class="text-secondary">正在加载任务列表...</p>
          </div>

          <!-- Task List -->
          <div v-else-if="tasks.length > 0" class="results-list">
            <div v-for="task in tasks" :key="task.id" class="result-item">
              <!-- Icon/Status -->
              <div class="item-cover d-flex align-center justify-center bg-surface-hover">
                <svg v-if="task.status === 'completed'" xmlns="http://www.w3.org/2000/svg" width="24" height="24"
                  viewBox="0 0 24 24" fill="none" stroke="var(--color-success)" stroke-width="2" stroke-linecap="round"
                  stroke-linejoin="round">
                  <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
                  <polyline points="22 4 12 14.01 9 11.01"></polyline>
                </svg>
                <svg v-else-if="task.status === 'failed'" xmlns="http://www.w3.org/2000/svg" width="24" height="24"
                  viewBox="0 0 24 24" fill="none" stroke="var(--color-error)" stroke-width="2" stroke-linecap="round"
                  stroke-linejoin="round">
                  <circle cx="12" cy="12" r="10"></circle>
                  <line x1="15" y1="9" x2="9" y2="15"></line>
                  <line x1="9" y1="9" x2="15" y2="15"></line>
                </svg>
                <svg v-else-if="task.status === 'downloading'" xmlns="http://www.w3.org/2000/svg" width="24" height="24"
                  viewBox="0 0 24 24" fill="none" stroke="var(--color-primary)" stroke-width="2" stroke-linecap="round"
                  stroke-linejoin="round">
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                  <polyline points="7 10 12 15 17 10"></polyline>
                  <line x1="12" y1="15" x2="12" y2="3"></line>
                </svg>
                <svg v-else xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none"
                  stroke="var(--text-secondary)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <circle cx="12" cy="12" r="10"></circle>
                  <polyline points="12 6 12 12 16 14"></polyline>
                </svg>
              </div>

              <!-- Info -->
              <div class="item-info">
                <div class="item-name" :title="task.music_title">{{ task.music_title || 'Unknown Title' }}</div>
                <div class="item-meta">
                  <span>{{ task.music_artist || 'Unknown Artist' }}</span>
                  <span v-if="task.music_album"> - {{ task.music_album }}</span>
                </div>
                <div class="item-extra">
                  <span class="badge" :class="getStatusClass(task.status)">{{ task.status }}</span>
                  <span class="ml-sm text-tertiary" v-if="task.quality"> | {{ task.quality }}</span>
                  <span class="ml-sm text-tertiary" v-if="task.file_size"> | {{ formatSize(task.file_size) }}</span>
                  <span class="ml-sm text-error" v-if="task.error_message" :title="task.error_message"> | {{
                    task.error_message }}</span>
                </div>
              </div>

              <!-- Actions -->
              <div class="item-actions">
                <button v-if="['failed', 'cancelled'].includes(task.status)" class="btn btn-sm btn-secondary"
                  @click="resetTask(task)" :disabled="isProcessing(task.id)">
                  {{ isProcessing(task.id) ? '处理中...' : '重试' }}
                </button>
                <span v-else-if="task.status === 'completed'" class="text-success text-sm">已完成</span>
              </div>
            </div>
          </div>

          <div v-else class="text-center py-2xl">
            <p class="text-secondary">暂无任务数据</p>
          </div>

          <!-- Pagination -->
          <div v-if="totalPages > 1" class="pagination">
            <div class="btn-group">
              <button class="btn btn-secondary btn-sm icon-btn" :disabled="currentPage === 1" @click="changePage(1)">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"
                  stroke-linejoin="round">
                  <polyline points="11 17 6 12 11 7"></polyline>
                  <polyline points="18 17 13 12 18 7"></polyline>
                </svg>
              </button>
              <button class="btn btn-secondary btn-sm icon-btn" :disabled="currentPage === 1"
                @click="changePage(currentPage - 1)">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"
                  stroke-linejoin="round">
                  <polyline points="15 18 9 12 15 6"></polyline>
                </svg>
              </button>

              <template v-for="page in visiblePages" :key="page">
                <span v-if="page === '...'" class="pagination-ellipsis">...</span>
                <button v-else class="btn btn-sm" :class="currentPage === page ? 'btn-primary' : 'btn-secondary'"
                  @click="changePage(Number(page))">
                  {{ page }}
                </button>
              </template>

              <button class="btn btn-secondary btn-sm icon-btn" :disabled="currentPage === totalPages"
                @click="changePage(currentPage + 1)">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"
                  stroke-linejoin="round">
                  <polyline points="9 18 15 12 9 6"></polyline>
                </svg>
              </button>
              <button class="btn btn-secondary btn-sm icon-btn" :disabled="currentPage === totalPages"
                @click="changePage(totalPages)">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"
                  stroke-linejoin="round">
                  <polyline points="13 17 18 12 13 7"></polyline>
                  <polyline points="6 17 11 12 6 7"></polyline>
                </svg>
              </button>
            </div>
          </div>
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

const route = useRoute()
const router = useRouter()

// State
const jobs = ref<DownloadJobItem[]>([])
const tasks = ref<DownloadTaskItem[]>([])
const activeJobId = ref(Number(route.query.job_id) || 0)
const searchKeyword = ref(route.query.keyword as string || '')
const filterStatus = ref(route.query.status as string || '')
const currentPage = ref(Number(route.query.page) || 1)
const totalTasks = ref(0)
const pageSize = 20
const isLoading = ref(false)
const processingTasks = ref<Set<number>>(new Set())

// Computed
const totalPages = computed(() => Math.ceil(totalTasks.value / pageSize))

const visiblePages = computed(() => {
  const total = totalPages.value
  const current = currentPage.value
  const windowSize = 5

  if (total <= windowSize) {
    return Array.from({ length: total }, (_, i) => i + 1)
  }

  let start = current - Math.floor(windowSize / 2)
  let end = current + Math.floor(windowSize / 2)

  if (start < 1) {
    start = 1
    end = windowSize
  }

  if (end > total) {
    end = total
    start = total - windowSize + 1
  }

  const pages = []
  if (start > 1) pages.push("...")
  for (let i = start; i <= end; i++) pages.push(i)
  if (end < total) pages.push("...")
  return pages
})

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
      limit: pageSize,
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
  // fetchTasks will be triggered by watch
}

const changePage = (page: number) => {
  currentPage.value = page
  updateUrl()
  // fetchTasks will be triggered by watch
}

const resetTask = async (task: DownloadTaskItem) => {
  if (processingTasks.value.has(task.id)) return
  processingTasks.value.add(task.id)

  try {
    const res = await api.download.resetTask(task.id)
    if (res.success && res.data.code === 200) {
      toast.show('任务已重置', 'success')
      // Update local state
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

// Watchers
watch(() => route.query, (newQuery) => {
  activeJobId.value = Number(newQuery.job_id) || 0
  searchKeyword.value = (newQuery.keyword as string) || ''
  filterStatus.value = (newQuery.status as string) || ''
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

.badge {
  display: inline-block;
  padding: 0.25em 0.4em;
  font-size: 75%;
  font-weight: 700;
  line-height: 1;
  text-align: center;
  white-space: nowrap;
  vertical-align: baseline;
  border-radius: 0.25rem;
}

.badge-success {
  color: var(--color-success);
  background-color: rgba(var(--color-success-rgb), 0.1);
}

.badge-primary {
  color: var(--color-primary);
  background-color: rgba(var(--color-primary-rgb), 0.1);
}

.badge-error {
  color: var(--color-error);
  background-color: rgba(var(--color-error-rgb), 0.1);
}

.badge-warning {
  color: var(--color-warning);
  background-color: rgba(var(--color-warning-rgb), 0.1);
}

.badge-secondary {
  color: var(--text-secondary);
  background-color: var(--bg-surface-hover);
}

.ml-sm {
  margin-left: var(--spacing-sm);
}

.mb-lg {
  margin-bottom: var(--spacing-lg);
}

.p-md {
  padding: var(--spacing-md);
}

.bg-surface-hover {
  background-color: var(--bg-surface-hover);
}

.d-flex {
  display: flex;
}

.align-center {
  align-items: center;
}

.justify-center {
  justify-content: center;
}

.text-sm {
  font-size: 0.875rem;
}

.text-success {
  color: var(--color-success);
}

.text-error {
  color: var(--color-error);
}
</style>