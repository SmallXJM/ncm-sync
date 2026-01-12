<template>
  <div class="page">
    <main>
      <div class="container">
        <header class="header">
          <h2 class="section-title">订阅管理</h2>
          <p class="text-secondary">共 {{ jobs.length }} 个订阅</p>
        </header>

        <div v-if="isLoading" class="text-center py-2xl">
          <div class="loading-spinner mx-auto mb-md" style="width: 32px; height: 32px;"></div>
          <p class="text-secondary">正在加载订阅列表...</p>
        </div>

        <div v-else-if="jobs.length > 0" class="job-list-container">
          <div class="list-header">
            <div>名称</div>
            <div>音质</div>
            <div>存储路径</div>
            <!-- <div>文件名模板</div> -->
            <!-- <div class="col-stats">任务统计</div> -->
            <div>状态</div>
            <div>操作</div>
          </div>

          <div class="job-list">
            <div v-for="job in jobs" :key="job.id" class="glass-card job-row">
              <div class="col-name">
                <h3 :title="job.job_name">{{ job.job_name }}</h3>
                <!-- <p class="text-secondary">{{ job.source_name || '未知' }}</p> -->
                <p class="text-secondary">{{ formatSourceType(job.source_type) }}</p>
              </div>

              <div class="col-quality">
                <span class="quality-badge">{{ formatQuality(job.target_quality) }}</span>
              </div>

              <div class="col-path">
                <span class="value mono" :title="job.storage_path">{{ job.storage_path }}</span>
              </div>

              <!-- <div class="col-template">
                <span class="value mono" :title="job.filename_template">{{ job.filename_template }}</span>
              </div> -->

              <!-- <div class="col-stats">
                <span>{{ job.completed_tasks }}/{{ job.total_tasks }}</span>
                <span v-if="job.failed_tasks > 0" class="text-error"> ({{ job.failed_tasks }})</span>
              </div> -->

              <div class="col-status">
                <!-- <span class="status-pill" :class="job.enabled ? 'status-pill--enabled' : 'status-pill--disabled'">
                  {{ job.enabled ? '已启用' : '已禁用' }}
                </span> -->
                <label class="switch is-disabled">
                  <input type="checkbox" v-model="job.enabled" disabled />
                  <span class="switch-track"></span>
                  <span class="switch-handle"></span>
                </label>
              </div>

              <div class="col-actions">
                <!-- 编辑按钮 -->
                <button class="btn btn-secondary btn-sm" @click="openEdit(job)">
                  <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24">
                    <g fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"
                      stroke-width="2">
                      <path d="M7 7H6a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h9a2 2 0 0 0 2-2v-1" />
                      <path d="M20.385 6.585a2.1 2.1 0 0 0-2.97-2.97L9 12v3h3zM16 5l3 3" />
                    </g>
                  </svg>
                </button>
                <!-- 删除按钮 -->
                <button class="btn btn-secondary btn-sm" @click="openEdit(job)">
                  <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24">
                    <g fill="none">
                      <path
                        d="m12.593 23.258l-.011.002l-.071.035l-.02.004l-.014-.004l-.071-.035q-.016-.005-.024.005l-.004.01l-.017.428l.005.02l.01.013l.104.074l.015.004l.012-.004l.104-.074l.012-.016l.004-.017l-.017-.427q-.004-.016-.017-.018m.265-.113l-.013.002l-.185.093l-.01.01l-.003.011l.018.43l.005.012l.008.007l.201.093q.019.005.029-.008l.004-.014l-.034-.614q-.005-.018-.02-.022m-.715.002a.02.02 0 0 0-.027.006l-.006.014l-.034.614q.001.018.017.024l.015-.002l.201-.093l.01-.008l.004-.011l.017-.43l-.003-.012l-.01-.01z" />
                      <path fill="currentColor"
                        d="M14.28 2a2 2 0 0 1 1.897 1.368L16.72 5H20a1 1 0 1 1 0 2l-.003.071l-.867 12.143A3 3 0 0 1 16.138 22H7.862a3 3 0 0 1-2.992-2.786L4.003 7.07L4 7a1 1 0 0 1 0-2h3.28l.543-1.632A2 2 0 0 1 9.721 2zm3.717 5H6.003l.862 12.071a1 1 0 0 0 .997.929h8.276a1 1 0 0 0 .997-.929zM10 10a1 1 0 0 1 .993.883L11 11v5a1 1 0 0 1-1.993.117L9 16v-5a1 1 0 0 1 1-1m4 0a1 1 0 0 1 1 1v5a1 1 0 1 1-2 0v-5a1 1 0 0 1 1-1m.28-6H9.72l-.333 1h5.226z" />
                    </g>
                  </svg>
                </button>
              </div>
            </div>
          </div>
        </div>

        <div v-else class="text-center py-2xl">
          <p class="text-secondary">暂无订阅数据</p>
        </div>
      </div>
    </main>

    <div class="drawer-backdrop" :class="{ visible: isDrawerOpen }" @click="closeDrawer"></div>
    <aside class="drawer" :class="{ visible: isDrawerOpen }">
      <div class="drawer-header">
        <div class="header-content">
          <h3>编辑订阅</h3>
          <div class="drawer-subtitle">
            <p class="help-text">正在编辑订阅「{{ editForm.job_name }}」</p>
          </div>
        </div>
        <button class="close-btn" @click="closeDrawer">×</button>
      </div>

      <div class="drawer-body" v-if="isDrawerOpen">
        <div class="form-group">
          <label>订阅名称</label>
          <input v-model="editForm.job_name" class="input w-full" type="text" />
        </div>

        <div class="form-group">
          <label>目标音质</label>
          <select v-model="editForm.target_quality" class="input w-full">
            <option value="dolby">杜比全景声 (Dolby)</option>
            <option value="jymaster">超清母带 (Jymaster)</option>
            <option value="sky">沉浸环绕声 (Sky)</option>
            <option value="jyeffect">高清环绕声 (Jyeffect)</option>
            <option value="hires">高解析度无损 (Hi-Res)</option>
            <option value="lossless">无损 (Lossless)</option>
            <option value="exhigh">极高 (Exhigh)</option>
            <option value="standard">标准 (Standard)</option>
          </select>
        </div>

        <div class="form-group">
          <div class="form-group row">
            <label>启用订阅</label>
            <label class="switch">
              <input type="checkbox" v-model="editForm.enabled" />
              <span class="switch-track"></span>
              <span class="switch-handle"></span>
            </label>
          </div>
        </div>

        <div class="form-group">
          <div class="form-group row">
            <label>嵌入标签</label>
            <label class="switch">
              <input type="checkbox" v-model="editForm.embed_metadata" />
              <span class="switch-track"></span>
              <span class="switch-handle"></span>
            </label>
          </div>
        </div>

        <div class="form-group">
          <div class="form-group row">
            <label>嵌入封面</label>
            <label class="switch">
              <input type="checkbox" v-model="editForm.embed_cover" />
              <span class="switch-track"></span>
              <span class="switch-handle"></span>
            </label>
          </div>
        </div>

        <div class="form-group">
          <div class="form-group row">
            <label>嵌入歌词</label>
            <label class="switch">
              <input type="checkbox" v-model="editForm.embed_lyrics" />
              <span class="switch-track"></span>
              <span class="switch-handle"></span>
            </label>
          </div>
        </div>

        <div class="form-group">
          <label>音乐名模板</label>
          <input v-model="editForm.filename_template" class="input w-full mono" type="text" />
        </div>

        <div class="form-group">
          <label>存储路径</label>
          <input v-model="editForm.storage_path" class="input w-full mono" type="text" />
        </div>
      </div>

      <div class="drawer-footer">
        <button class="btn btn-secondary" @click="closeDrawer">取消</button>
        <button class="btn btn-primary" @click="submitEdit" :disabled="isSaving">
          {{ isSaving ? '保存中...' : '保存' }}
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

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import api from '@/api'
import type { DownloadJobItem, UpdateJobParams } from '@/api/ncm/download'

interface Toast {
  show: boolean
  message: string
  type: 'info' | 'success' | 'warning' | 'error'
}

interface EditFormState {
  job_id: number | null
  job_name: string
  target_quality: string
  embed_metadata: boolean
  embed_cover: boolean
  embed_lyrics: boolean
  filename_template: string
  storage_path: string
  enabled: boolean
}

const isLoading = ref(false)
const isSaving = ref(false)
const jobs = ref<DownloadJobItem[]>([])
const isDrawerOpen = ref(false)

const toast = reactive<Toast>({
  show: false,
  message: '',
  type: 'info',
})

const editForm = reactive<EditFormState>({
  job_id: null,
  job_name: '',
  target_quality: 'hires',
  embed_metadata: true,
  embed_cover: true,
  embed_lyrics: true,
  filename_template: '{artist} - {title}',
  storage_path: '',
  enabled: true,
})

function formatSourceType(value: string) {
  const map: Record<string, string> = {
    playlist: '歌单',
    album: '专辑',
    artist: '艺术家',
  }
  return map[value] || value
}

onMounted(async () => {
  await fetchJobs()
})

async function fetchJobs() {
  if (isLoading.value) return
  isLoading.value = true
  try {
    const res = await api.download.getJobList()
    if (res.success && res.data.code === 200 && res.data.data) {
      jobs.value = res.data.data.jobs || []
    } else if (!res.success) {
      showToast('获取订阅列表失败: ' + res.error, 'error')
    } else {
      showToast('获取订阅列表失败: ' + (res.data.message || '未知错误'), 'error')
    }
  } catch (e) {
    const err = e as Error
    showToast('获取订阅列表失败: ' + err.message, 'error')
  } finally {
    isLoading.value = false
  }
}

function openEdit(job: DownloadJobItem) {
  editForm.job_id = job.id
  editForm.job_name = job.job_name
  editForm.target_quality = job.target_quality
  editForm.embed_metadata = job.embed_metadata
  editForm.embed_cover = job.embed_cover
  editForm.embed_lyrics = job.embed_lyrics
  editForm.filename_template = job.filename_template
  editForm.storage_path = job.storage_path
  editForm.enabled = job.enabled
  isDrawerOpen.value = true
}

function closeDrawer() {
  isDrawerOpen.value = false
}

function formatQuality(value: string) {
  const map: Record<string, string> = {
    standard: '标准',
    exhigh: '极高',
    lossless: '无损',
    hires: 'Hi-Res',
    jyeffect: '高清环绕声',
    sky: '沉浸环绕声',
    jymaster: '超清母带',
    dolby: '杜比全景声',
  }
  return map[value] || value
}

async function submitEdit() {
  if (!editForm.job_id) {
    showToast('无效的订阅 ID', 'error')
    return
  }
  if (!editForm.storage_path.trim()) {
    showToast('存储路径不能为空', 'warning')
    return
  }
  if (!editForm.filename_template.trim()) {
    showToast('音乐名模板不能为空', 'warning')
    return
  }

  const payload: UpdateJobParams = {
    job_id: editForm.job_id,
    job_name: editForm.job_name,
    target_quality: editForm.target_quality,
    embed_metadata: editForm.embed_metadata,
    embed_cover: editForm.embed_cover,
    embed_lyrics: editForm.embed_lyrics,
    filename_template: editForm.filename_template,
    storage_path: editForm.storage_path,
    enabled: editForm.enabled,
  }

  isSaving.value = true
  try {
    const res = await api.download.updateJob(payload)
    if (res.success && res.data.code === 200) {
      showToast('订阅更新成功', 'success')
      closeDrawer()
      await fetchJobs()
    } else if (!res.success) {
      showToast('订阅更新失败: ' + res.error, 'error')
    } else {
      showToast('订阅更新失败: ' + (res.data.message || '未知错误'), 'error')
    }
  } catch (e) {
    const err = e as Error
    showToast('订阅更新失败: ' + err.message, 'error')
  } finally {
    isSaving.value = false
  }
}

function showToast(message: string, type: Toast['type'] = 'info') {
  toast.message = message
  toast.type = type
  toast.show = true
  setTimeout(() => hideToast(), 5000)
}

function hideToast() {
  toast.show = false
}
</script>

<style scoped lang="scss">
.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-lg);
  margin-top: var(--spacing-lg);
  margin-bottom: var(--spacing-lg);
}

/* 定义统一的列宽比例 */
/* 这里的顺序对应：订阅名称、音质、存储路径、状态、操作 */
/* 使用 minmax 确保最小宽度，max-content 适应内容 */
$grid-config: minmax(200px, auto) max-content max-content max-content max-content;

.job-list-container {
  margin-top: var(--spacing-lg);
  /* 屏幕太小时允许横向滚动 */
  overflow-x: auto;
  
  /* 桌面端使用 Subgrid 实现跨行对齐 */
  @media (min-width: 769px) {
    display: grid;
    grid-template-columns: $grid-config;
    /* 使用 row-gap 代替原本 .job-list 的 gap */
    row-gap: var(--spacing-sm);
  }
}

.list-header {
  /* 移动端隐藏逻辑保持不变 */
  display: none;
  
  @media (min-width: 769px) {
    /* 设为 Grid Item 并跨越所有列 */
    grid-column: 1 / -1;
    /* 启用 Subgrid 继承父容器列定义 */
    display: grid;
    grid-template-columns: subgrid;
    
    padding: 0 var(--spacing-lg);
    color: var(--text-tertiary);
    font-size: 0.875rem;
    font-weight: 500;

    div {
      padding: 0 var(--spacing-xs);
    }
  }
}

.job-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
  
  /* 桌面端移除布局容器身份，使子元素直接参与父 Grid */
  @media (min-width: 769px) {
    display: contents;
  }
}

.job-row {
  /* 基础样式 */
  padding: var(--spacing-md) var(--spacing-lg);
  transition: transform 0.2s;
  
  &:hover {
    transform: translateY(-2px);
    background: var(--bg-surface-hover);
  }

  /* 通用列处理 */
  >div {
    padding: 0 var(--spacing-xs);
    min-width: 0; /* 触发省略号的关键 */
  }

  /* 桌面端布局 */
  @media (min-width: 769px) {
    /* 设为 Grid Item 并跨越所有列 */
    grid-column: 1 / -1;
    /* 启用 Subgrid 继承父容器列定义 */
    display: grid;
    grid-template-columns: subgrid;
    align-items: center;
    gap: var(--spacing-sm);
  }
}

/* 文本省略处理 */
.col-name h3,
.col-path .value,
.col-template .value {
  display: block;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.col-name {
  h3 {
    font-size: 0.95rem;
    margin: 0;
  }

  p {
    font-size: 0.75rem;
    margin: 0;
  }
}

.col-quality {
  .quality-badge {
    font-size: 0.8rem;
    // padding: 2px 8px;
    background: var(--bg-secondary);
    border-radius: 4px;
    text-align: left;
    

  }
}

.mono {
  font-family: var(--font-mono);
  font-size: 0.85rem;
  opacity: 0.8;
}

/* 状态药丸微调 */
.status-pill {
  white-space: nowrap;
  justify-content: center;
}

.col-actions {
  text-align: left;
  .btn {
    margin-right: var(--spacing-xs);
  }
}

/* 适配移动端：如果是手机，改回卡片流 */
@media (max-width: 768px) {
  .list-header {
    display: none;
  }

  .job-row {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: var(--spacing-md);

    .col-path,
    .col-template {
      grid-column: span 2;
    }

    /* 文本省略处理 */
    .col-name h3,
    .col-path .value,
    .col-template .value {
      /* 保留换行符，同时允许文本在到达容器边缘时自动换行 */
      white-space: pre-wrap;
      /* 字数过多时强制折断单词 */
      word-break: break-word;
    }

    .col-quality,
    .col-actions {
      text-align: right;
    }
  }
}

.mono {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace;
}

.job-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: var(--spacing-sm);
}

.status-pill {
  display: inline-flex;
  align-items: center;
  padding: 2px 10px;
  border-radius: 999px;
  font-size: 0.75rem;
  font-weight: 500;
}

.status-pill--enabled {
  background: rgba(34, 197, 94, 0.1);
  color: var(--color-success);
}

.status-pill--disabled {
  background: rgba(148, 163, 184, 0.15);
  color: var(--text-secondary);
}

.text-error {
  color: var(--color-error);
}

.drawer-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(4px);
  z-index: 100;
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.3s ease;
}

.drawer-backdrop.visible {
  opacity: 1;
  pointer-events: auto;
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
}

.drawer.visible {
  transform: translateX(0);
}

.drawer-header {
  padding: var(--spacing-lg);
  border-bottom: 1px solid var(--border-color);
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.drawer-header .header-content {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.drawer-header h3 {
  font-size: 1.25rem;
  font-weight: 600;
  margin: 0;
  line-height: 1.2;
}

.drawer-subtitle .help-text {
  font-size: 0.875rem;
  color: var(--text-secondary);
}

.close-btn {
  font-size: 1.5rem;
  line-height: 1;
  background: none;
  border: none;
  cursor: pointer;
  color: var(--text-secondary);
  padding: 4px;
  margin-top: -4px;
}

.close-btn:hover {
  color: var(--text-primary);
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
}

.form-group label {
  font-weight: 500;
  color: var(--text-primary);
}

.form-group.row {
  flex-direction: row;
  justify-content: space-between;
  align-items: center;
}
</style>
