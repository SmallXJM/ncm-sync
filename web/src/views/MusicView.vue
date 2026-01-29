<template>
  <div class="page">
    <main>
      <div class="container">
        <div class="main-content">
          <div class="glass-card headbar">
            <div class="search-form">

              <div class="search-input-wrapper" style="flex: 1;">
                <span class="search-icon">
                  <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none"
                    stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <circle cx="11" cy="11" r="8"></circle>
                    <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
                  </svg>
                </span>
                <input v-model="searchKeyword" @keyup.enter="handleSearch" type="text" class="search-input"
                  placeholder="搜索音乐标题、艺术家、专辑..." />
                <button v-if="searchKeyword" class="search-clear" @click="searchKeyword = ''; handleSearch()">
                  ×
                </button>
              </div>
            </div>
            <div class="filter-wrapper" ref="filterContainerRef">
              <!-- Status Filter -->
              <div class="filter-group relative">
                <button type="button" class="filter-trigger" :aria-expanded="isStatusFilterOpen ? 'true' : 'false'"
                  aria-haspopup="listbox" @click.stop="toggleStatusFilterDropdown">
                  <span class="filter-label">状态：</span>

                  <span class="filter-tag" :class="{ 'filter-tag-muted': !filterStatus }">
                    <span class="filter-text">{{ filterStatus ? getStatusOptions(filterStatus) : '未应用' }}</span>
                    <button v-if="filterStatus" type="button" class="filter-clear" aria-label="清除状态筛选"
                      @click.stop="clearStatusFilter">
                      ×
                    </button>
                  </span>

                  <!-- <span class="filter-arrow">
                    <svg width="12" height="12" viewBox="0 0 24 24">
                      <path d="M6 9l6 6 6-6" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"
                        stroke-linejoin="round" />
                    </svg>
                  </span> -->
                </button>

                <transition name="dropdown-fade">
                  <div v-if="isStatusFilterOpen" class="filter-dropdown glass-card dropdown-left" role="listbox">
                    <button v-for="option in statusOptions" :key="option.value" type="button" class="submenu-option"
                      :class="{ 'is-selected': option.value === filterStatus }"
                      @click="selectStatusFilter(option.value)">
                      {{ option.label }}
                    </button>
                    <div class="dropdown-footer">
                      <button type="button" class="submenu-option" @click="selectStatusFilter('')">
                        移除筛选
                      </button>
                    </div>
                  </div>
                </transition>
              </div>

              <!-- Job Filter -->
              <div class="filter-group relative" ref="jobFilterGroupRef">
                <button type="button" class="filter-trigger" :aria-expanded="isJobFilterOpen ? 'true' : 'false'"
                  aria-haspopup="listbox" @click.stop="toggleJobFilterDropdown">
                  <span class="filter-label">订阅：</span>

                  <span class="filter-tag" :class="{ 'filter-tag-muted': !selectedJob }">
                    <span class="filter-text">{{ selectedJob ? selectedJob.job_name : '未应用' }}</span>
                    <button v-if="selectedJob" type="button" class="filter-clear" aria-label="清除订阅筛选"
                      @click.stop="clearJobFilter">
                      ×
                    </button>
                  </span>

                  <!-- <span class="filter-arrow">
                    <svg width="12" height="12" viewBox="0 0 24 24">
                      <path d="M6 9l6 6 6-6" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"
                        stroke-linejoin="round" />
                    </svg>
                  </span> -->
                </button>

                <transition name="dropdown-fade">
                  <div v-if="isJobFilterOpen" class="filter-dropdown glass-card dropdown-large" :class="{ 'dropdown-left': jobDropdownPlacement === 'left' }" role="listbox">
                    <div class="submenu-list-form search-form">
                      <div class="search-input-wrapper" style="flex: 1;">
                        <span class="search-icon">
                          <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none"
                            stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <circle cx="11" cy="11" r="8"></circle>
                            <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
                          </svg>
                        </span>
                        <input ref="filterSearchInputRef" v-model="jobSearchKeyword" type="text" class="search-input"
                          placeholder="搜索订阅..." @click.stop />
                      </div>
                    </div>
                    <div class="submenu-list">
                      <button v-for="job in filteredJobs" :key="job.id" type="button" class="submenu-option"
                        :class="{ 'is-selected': job.id === activeJobId }" @click="selectJobFromDropdown(job)">
                        <span class="filter-option-name">{{ job.job_name }}</span>
                      </button>
                      <div v-if="filteredJobs.length === 0" class="filter-empty text-tertiary">
                        未找到 "{{ jobSearchKeyword }}"
                      </div>
                    </div>
                    <div class="dropdown-footer">
                      <button type="button" class="submenu-option"
                        @click="selectJobFromDropdown({ id: 0, job_name: '所有订阅' } as any)">
                        移除筛选
                      </button>
                    </div>
                  </div>
                </transition>
              </div>
            </div>
          </div>


          <!-- Stats & Pagination Info -->
          <div class="header">
            <p class="text-secondary">共 {{ totalTasks }} 首音乐</p>
            <p class="text-secondary">当前 {{ currentPage }} / {{ totalPages }} 页</p>
            <!-- <div class="header-right">
              <select v-model.number="pageSize" class="input page-size-select" @change="handlePageSizeChange">
                <option :value="10">每页 10 首</option>
                <option :value="20">每页 20 首</option>
                <option :value="50">每页 50 首</option>
              </select>
            </div> -->
          </div>

          <!-- Loading State -->
          <AppLoading v-if="isLoading" message="正在加载本地音乐" />

          <!-- Task Grid (Card Layout) -->
          <div v-else-if="tasks.length > 0" class="playlist-grid">
            <div v-for="task in tasks" :key="task.id" class="playlist-card">
              <div class="card-main">
                <div class="card-cover">
                  <img v-if="task.status === 'completed' && task.file_path && !coverErrorTaskIds.has(task.id)"
                    :src="getCoverSrc(task.id)" alt="cover" loading="lazy" @error="handleCoverError(task.id)"
                    class="image-filter-brightness" />
                  <div v-else class="default-cover">
                    <svg xmlns="http://www.w3.org/2000/svg" width="40" height="40" viewBox="0 0 24 24" fill="none"
                      stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                      <path d="M9 18V5l12-2v13"></path>
                      <circle cx="6" cy="18" r="3"></circle>
                      <circle cx="18" cy="16" r="3"></circle>
                    </svg>
                  </div>

                  <!-- Status Overlay on Cover -->
                  <!-- <div class="status-overlay" :class="getStatusClass(task.status)">
                    <span>{{ getStatusText(task.status) }}</span>
                  </div> -->
                  <div class="status-badge status-overlay">
                    <div class="status-dot" :class="getStatusClass(task.status)"></div>
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
                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none"
                    stroke="var(--color-error)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <circle cx="12" cy="12" r="10"></circle>
                    <line x1="12" y1="8" x2="12" y2="12"></line>
                    <line x1="12" y1="16" x2="12.01" y2="16"></line>
                  </svg>
                  <span class="text-error text-sm text-truncate" style="max-width: 120px;">{{ task.error_message
                  }}</span>
                </div>
                <div v-else></div> <!-- Spacer -->

                <div class="action-buttons">
                  <button v-if="['failed', 'cancelled'].includes(task.status)" class="btn btn-sm btn-secondary"
                    @click.stop="resetTask(task)" :disabled="isProcessing(task.id)">
                    {{ isProcessing(task.id) ? '处理中...' : '重置' }}
                  </button>
                  <button class="btn btn-sm btn-secondary ml-sm" @click="goDetail(task)">
                    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24">
                      <path fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"
                        stroke-width="2" d="M4 6h16M4 12h16M4 18h12" />
                    </svg>
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
          <AppPagination :total-items="totalTasks" :current-page="currentPage" :page-size="pageSize"
            @page-change="changePage" />
        </div>
      </div>
    </main>
  </div>
</template>

<script lang="ts" setup>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/api'
import type { DownloadJobItem, DownloadTaskItem } from '@/api/ncm/download'
import { toast } from '@/utils/toast'
import AppPagination from '@/components/AppPagination.vue'
import AppLoading from '@/components/AppLoading.vue'
import { useMusicQuery } from '@/composables/useMusicQuery'

const router = useRouter()

const jobs = ref<DownloadJobItem[]>([])
const tasks = ref<DownloadTaskItem[]>([])
const totalTasks = ref(0)
const pageSize = ref(20)
const isLoading = ref(false)
const searchDebounceTimer = ref<number | null>(null)
const processingTasks = ref<Set<number>>(new Set())
const coverErrorTaskIds = ref<Set<number>>(new Set())
const isStatusFilterOpen = ref(false)
const isJobFilterOpen = ref(false)
const jobFilterGroupRef = ref<HTMLElement | null>(null)
const jobDropdownPlacement = ref<'left' | 'right'>('left')
const jobSearchKeyword = ref('')
const filterHighlightedIndex = ref(-1)
const filterSearchInputRef = ref<HTMLInputElement | null>(null)

const {
  activeJobId,
  searchKeyword,
  filterStatus,
  currentPage,
  updateUrl,
  saveToStorage: saveMusicQueryToStorage,
} = useMusicQuery({
  onRouteQueryChange: () => {
    fetchTasks()
  },
})

const totalPages = computed(() => Math.ceil(totalTasks.value / pageSize.value))

const selectedJob = computed<DownloadJobItem | undefined>(() =>
  jobs.value.find((job) => job.id === activeJobId.value && activeJobId.value !== 0),
)

type TaskStatusFilter =
  | ''
  | 'pending'
  | 'downloading'
  | 'processing'
  | 'completed'
  | 'failed'
  | 'cancelled'

const statusOptions: { value: TaskStatusFilter; label: string }[] = [
  // { value: '', label: '所有状态' },
  { value: 'pending', label: '仅等待' },
  // { value: 'downloading', label: '下载中' },
  // { value: 'processing', label: '处理中' },
  { value: 'completed', label: '仅完成' },
  { value: 'failed', label: '仅失败' },
  // { value: 'cancelled', label: '已取消' },
]

const getStatusOptions = (status: string) => {
  const map: Record<string, string> = {
    pending: '仅等待',
    completed: '仅完成',
    failed: '仅失败',
  }
  return map[status] || status
}


const filteredJobs = computed<DownloadJobItem[]>(() => {
  const keyword = jobSearchKeyword.value.trim().toLowerCase()
  if (!keyword) return jobs.value
  return jobs.value.filter((job) => (job.job_name || '').toLowerCase().includes(keyword))
})

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
      keyword: searchKeyword.value || undefined,
    }
    const res = await api.download.getTaskList(params)
    if (res.success && res.data.code === 200) {
      if (res.data.data) {
        tasks.value = res.data.data.tasks
        totalTasks.value = res.data.data.total
      }
    } else {
      toast.error('获取任务列表失败')
    }
  } catch (e) {
    console.error('Failed to load tasks', e)
    toast.error('获取任务列表失败')
  } finally {
    isLoading.value = false
  }
}

const runSearch = () => {
  currentPage.value = 1
  updateUrl()
  fetchTasks()
}

const runSearchDebounced = () => {
  if (searchDebounceTimer.value !== null) {
    window.clearTimeout(searchDebounceTimer.value)
  }
  searchDebounceTimer.value = window.setTimeout(() => {
    runSearch()
  }, 300)
}

const handleSearch = () => {
  if (searchDebounceTimer.value !== null) {
    window.clearTimeout(searchDebounceTimer.value)
    searchDebounceTimer.value = null
  }
  runSearch()
}

// const handlePageSizeChange = () => {
//   currentPage.value = 1
//   runSearch()
// }

const selectJob = (id: number) => {
  activeJobId.value = id
  currentPage.value = 1
  runSearchDebounced()
}

const clearJobFilter = () => {
  activeJobId.value = 0
  currentPage.value = 1
  jobSearchKeyword.value = ''
  runSearchDebounced()
}

const clearStatusFilter = () => {
  filterStatus.value = ''
  currentPage.value = 1
  runSearchDebounced()
}

const selectStatusFilter = (value: TaskStatusFilter) => {
  if (filterStatus.value === value) return
  filterStatus.value = value
  currentPage.value = 1
  runSearchDebounced()
  isStatusFilterOpen.value = false
}

const toggleStatusFilterDropdown = () => {
  isStatusFilterOpen.value = !isStatusFilterOpen.value
  if (isStatusFilterOpen.value) {
    isJobFilterOpen.value = false
  }
}

const toggleJobFilterDropdown = () => {
  isJobFilterOpen.value = !isJobFilterOpen.value
  if (isJobFilterOpen.value) {
    isStatusFilterOpen.value = false
    jobSearchKeyword.value = ''
    filterHighlightedIndex.value = -1
    // Reset to preferred alignment first
    jobDropdownPlacement.value = 'left'
    nextTick(() => {
      // Check collision
      if (jobFilterGroupRef.value && filterContainerRef.value) {
        const groupRect = jobFilterGroupRef.value.getBoundingClientRect()
        const containerRect = filterContainerRef.value.getBoundingClientRect()
        const dropdownWidth = 260 // Minimum width of dropdown-large

        // Check if extending to the right would overflow the container's right edge
        // Left alignment means the dropdown starts at groupRect.left
        if (groupRect.left + dropdownWidth > containerRect.right) {
          jobDropdownPlacement.value = 'right'
        }
      }
      // filterSearchInputRef.value?.focus()
    })
  }
}

const selectJobFromDropdown = (job: DownloadJobItem) => {
  selectJob(job.id)
  isJobFilterOpen.value = false
  jobSearchKeyword.value = ''
}

const filterContainerRef = ref<HTMLElement | null>(null) // 新增 container 引用

// 处理外部点击的函数
const handleClickOutside = (event: MouseEvent) => {
  // 如果下拉框是打开的，且点击的元素不在 container 内部
  if ((isStatusFilterOpen.value || isJobFilterOpen.value) &&
    filterContainerRef.value &&
    !filterContainerRef.value.contains(event.target as Node)) {
    isStatusFilterOpen.value = false
    isJobFilterOpen.value = false
  }
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
      toast.success('任务已重置')
      task.status = 'pending'
      task.error_message = ''
    } else {
      toast.error('重置失败')
    }
  } catch {
    toast.error('重置失败')
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

// const getStatusClass = (status: string) => {
//   switch (status) {
//     case 'completed': return 'badge-success'
//     case 'downloading': return 'badge-primary'
//     case 'failed': return 'badge-error'
//     case 'cancelled': return 'badge-warning'
//     default: return 'badge-secondary'
//   }
// }

function getStatusClass(status: string): string {
  switch (status) {
    case 'completed': return 'status-online'
    case 'failed':
    case 'cancelled': return 'status-offline'
    default: return 'status-pending'
  }
}

const getStatusText = (status: string) => {
  const map: Record<string, string> = {
    pending: '等待',
    downloading: '下载',
    processing: '处理',
    completed: '完成',
    failed: '失败',
    cancelled: '取消',
  }
  return map[status] || status
}

const goDetail = (task: DownloadTaskItem) => {
  saveMusicQueryToStorage()
  router.push({ name: 'music-detail', params: { taskId: String(task.id) } })
}

const getCoverSrc = (taskId: number) => `/local/music/cover/${taskId}`

const handleCoverError = (taskId: number) => {
  coverErrorTaskIds.value.add(taskId)
}

onMounted(() => {
  fetchJobs()
  fetchTasks()
  // 挂载时添加全局监听
  window.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  // 销毁时移除监听，防止内存泄露
  window.removeEventListener('click', handleClickOutside)
  if (searchDebounceTimer.value !== null) {
    window.clearTimeout(searchDebounceTimer.value)
  }
})
</script>

<style scoped lang="scss">
.main-content {
  flex: 1;
  min-width: 0;
}

.headbar {
  display: flex;
  flex-wrap: wrap;
  /* 宽度不够时自动换行 */
  align-items: center;
  gap: var(--spacing-sm);
  /* 左右/上下间距 */
  padding: var(--spacing-sm);

  margin-bottom: var(--spacing-lg);

  .search-form {
    flex: 500 1 300px;
    /* 占据剩余所有空间，且权重远大于 filter-wrapper，确保同一行时 filter 保持内容宽度 */
    min-width: 300px;
    /* 保证搜索框在窄屏下不会缩得太小，触发换行 */
    display: flex;
    margin-bottom: 0;
    /* 覆盖原有的 margin */

    .search-input-wrapper {
      position: relative;
      /* 必须：作为图标定位的基准 */
      display: flex;
      align-items: center;

      .search-icon {
        position: absolute;
        left: 12px;
        /* 图标距离左侧的距离 */
        display: flex;
        align-items: center;
        justify-content: center;
        color: var(--text-tertiary);
        /* 使用你现有的次级文本颜色 */
        pointer-events: none;
        /* 重要：点击图标时事件会穿透到 input 上 */
        transition: color 0.2s ease;
      }

      .search-input {
        width: 100%;
        padding-left: 38px;
        /* 如果有清除按钮，input 右侧也要加 padding */
        padding-right: 30px;
        /* 重要：留出图标的空间 (图标宽度 + 间距) */
        transition: background-color 0.3s ease, border-color 0.3s ease;
      }

      .search-input:focus {
        border-color: var(--border-hover);
        box-shadow: none;
        /* 修正：清除阴影的标准写法 */
        outline: none;
        /* 关键：清除浏览器默认的对焦外框 */
      }

      /* 推荐做法：使用 focus-within 让 input 聚焦时图标也变色 */
      &:focus-within {
        .search-icon {
          color: var(--text-secondary);
          /* 聚焦时放大镜变色 */
        }
      }

      .search-clear {
        position: absolute;
        right: 10px;
        background: transparent;
        border: none;
        color: var(--text-tertiary);
        cursor: pointer;
        font-size: 18px;
        padding: 4px;
        line-height: 1;
        transition: color 0.3s ease;

        &:hover {
          color: var(--text-primary);
        }
      }


    }


  }

  .filter-wrapper {
    display: flex;
    flex-wrap: nowrap;
    gap: 8px;
    flex: 1 1 auto;
    /* 允许生长，但在同一行时会被 search-form 挤压 */
    min-width: 0;

    .filter-group:first-child {
      flex: 0 0 auto;
      /* 状态筛选始终保持内容宽度 */
    }

    .filter-group:last-child {
      flex: 1 1 auto;
      /* 订阅筛选在空间足够（如换行）时自动填充 */
      min-width: 0;
    }

    @media (max-width: 600px) {
      flex-basis: 100%;

      /* 移除原本的 .filter-group flex: 1，遵循新的规则：状态内容宽，订阅填充 */
      .filter-trigger {
        width: 100%;
      }
    }
  }
}

.filter-group {
  position: relative;
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

.header-right {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.page-size-select {
  width: auto;
}



.search-form {
  flex: 1;
  margin-bottom: 0;
}

.filter-wrapper {
  position: relative;
  flex-shrink: 0;
}

.filter-trigger {
  width: 100%;
  display: inline-flex;
  align-items: center;
  justify-content: flex-start;
  gap: var(--spacing-xs);
  padding: 8px 12px;
  border-radius: 12px;
  border: 1px solid var(--border-color);
  background: var(--bg-surface);
  color: var(--text-secondary);
  cursor: pointer;
  font-size: 0.9rem;
  transition: background-color 0.3s ease, border-color 0.3s ease, box-shadow 0.3s ease, color 0.3s ease;
}

.filter-trigger:hover,
.filter-trigger:focus-visible {
  outline: none;
  border-color: var(--border-hover);
  background: var(--bg-surface-hover);
  color: var(--text-primary);
  box-shadow: var(--shadow-sm);
}

.filter-label {
  color: var(--text-secondary);
  transition: color 0.3s ease;

  white-space: nowrap;
  /* 强制文本不换行 */
  flex-shrink: 0;
  /* 在 Flex 布局中禁止被压缩 */
  display: inline-block;
  /* 确保它作为一个整体块处理 */
}

.filter-tag {
  display: inline-flex;
  align-items: center;
  padding: 4px 8px;
  background: var(--bg-surface-hover);
  border-radius: 4px;
  font-size: 0.85rem;
  color: var(--text-primary);
  border: 1px solid var(--border-color);
  transition: color 0.3s ease, background-color 0.3s ease, border-color 0.3s ease;
  flex: 0 1 auto;
  /* 允许收缩 */
  min-width: 0;
  /* 防止溢出 */
  max-width: 100%;
  /* 确保不超过父容器 */
}

.filter-tag-muted {
  color: var(--text-tertiary);
  background: var(--bg-surface-hover);
  border: 1px solid var(--bg-surface-hover);
}

.filter-text {
  /* max-width: 120px; */
  /* 移除固定最大宽度 */
  flex: 0 1 auto;
  /* 允许收缩 */
  min-width: 0;
  /* 防止溢出 */
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}



.filter-clear {
  border: none;
  background: transparent;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 16px;
  height: 16px;
  border-radius: 999px;
  color: var(--text-tertiary);
  padding: 0;
  margin-left: 4px;
  transition: color 0.3s ease, background-color 0.3s ease, border-color 0.3s ease;
}

.filter-clear:hover,
.filter-clear:focus-visible {
  outline: none;
  background: var(--border-color);
  color: var(--text-primary);
}

.filter-arrow {
  margin-left: auto;
  display: inline-flex;
  align-items: center;
  color: var(--text-tertiary);
}

/* 1. 容器：实现 search-form 和 filter-wrapper 响应式分布 */
.config-sidebar {
  display: flex;
  flex-wrap: wrap;
  /* 核心：自动换行 */
  align-items: center;
  gap: var(--spacing-md);
  padding: var(--spacing-md);

  .search-form {
    flex: 1;
    /* 填充剩余空间 */
    min-width: 260px;
    /* 触发换行的阈值 */
  }
}

/* 2. 下拉菜单基础样式 */
.filter-dropdown {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  min-width: 160px;
  background: var(--bg-surface);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 6px;
  z-index: 100;
  box-shadow: var(--shadow-lg);
}

.dropdown-large {
  min-width: 260px;
}

.dropdown-left {
  left: 0;
  right: auto;
}

.submenu-option {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 12px;
  border-radius: 6px;
  border: none;
  background: transparent;
  cursor: pointer;
  color: var(--text-secondary);
  font-size: 0.9rem;
  text-align: left;
}

.submenu-option:hover {
  background: var(--bg-surface-hover);
  color: var(--text-primary);
}

.submenu-option.is-selected {
  color: var(--accent-color);
  font-weight: 500;
  background: var(--bg-surface-hover);
  // background: rgba(var(--accent-color-rgb), 0.05);
}

.filter-option-name {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

// .submenu-search {
//   padding: 8px;
//   border-bottom: 1px solid var(--border-color);
//   margin-bottom: 4px;
// }

/* 4. 优化子菜单内部搜索框 */
.submenu-search {
  // padding: 4px;
  position: sticky;
  /* 搜索框固定在子菜单顶部 */
  top: 0;
  background: inherit;
  z-index: 1;
}

.submenu-search .search-input {
  width: 100%;
  font-size: 0.85rem;
  margin-bottom: 4px;
  border-radius: 6px;
}

.headbar .submenu-list-form {
  margin-bottom: 4px;
  min-width: 0;
}

.submenu-list {
  max-height: 240px;
  overflow-y: auto;
}

.dropdown-footer {
  padding-top: 4px;
  margin-top: 4px;
  border-top: 1px solid var(--border-color);
}

.filter-empty {
  padding: 8px 10px;
  font-size: 0.85rem;
}

.dropdown-fade-enter-active,
.dropdown-fade-leave-active {
  transition: opacity 0.18s ease-out, transform 0.18s ease-out;
}

.dropdown-fade-enter-from,
.dropdown-fade-leave-to {
  opacity: 0;
  transform: translateY(4px);
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
  overflow: visible; /* 关键：允许子元素溢出 */
}

.card-cover img {
  border-radius: inherit; /* 让图片继承圆角 */
  width: 100%;
  display: block;
}

.default-cover {
  width: 100%;
  height: 100%;
  border-radius: inherit; /* 继承圆角 */
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-surface-hover);
  color: var(--text-tertiary);
  transition: color 0.3s ease, background-color 0.3s ease;

  &.large {
    width: 120px;
    height: 120px;
    border-radius: 0.75rem;
  }
}

.status-overlay {
  position: absolute;

  padding: 2px 6px;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 600;
  // color: white;
  // backdrop-filter: blur(4px);

  // &.badge-success {
  //   background: color-mix(in srgb, var(--color-success), transparent 70%);
  // }

  // &.badge-primary {
  //   background: color-mix(in srgb, var(--color-primary), transparent 70%);
  // }

  // &.badge-error {
  //   background: color-mix(in srgb, var(--color-error), transparent 70%);
  // }

  // &.badge-warning {
  //   background: color-mix(in srgb, var(--color-warning), transparent 70%);
  // }

  // &.badge-secondary {
  //   background: rgba(0, 0, 0, 0.3);
  // }
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

.mt-xs {
  margin-top: var(--spacing-xs);
}

.ml-sm {
  margin-left: var(--spacing-sm);
}

.creator-info {
    // 最多显示两行
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  /* 标准属性，用于未来兼容性 */
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
