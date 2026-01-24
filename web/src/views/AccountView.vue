<template>
  <div class="page">
    <!-- Main Content -->
    <main>
      <div class="container">
        <div class="dashboard-grid mb-2xl">
          <div class="dashboard-left">
            <!-- Current Account Section -->
            <section class="current-account-section">
              <div class="glass-card" :class="{ 'account-bg-cover': currentSession?.background_url }"
                :style="{ '--bg-image': currentSession ? `url(${currentSession.background_url})` : 'none' }">

                <div v-if="currentSession" class="account-card-overlay"></div>

                <div v-if="currentSession" class="current-account-info">
                  <div class="account-header">
                    <div class="avatar-container">
                      <div class="avatar avatar-xl">
                        <img :src="currentSession.avatar_url || ''" :alt="currentSession.nickname || '用户头像'"
                          @error="handleAvatarError" />
                      </div>
                      <div class="status-badge">
                        <div class="status-dot" :class="getStatusClass(currentSession.is_valid)"></div>
                        <span>{{ getStatusText(currentSession.is_valid) }}</span>
                      </div>
                    </div>


                    <div class="account-details">
                      <div class="account-info">
                        <h3 class="account-name">{{ currentSession.nickname || '未知用户' }}</h3>
                        <div class="account-meta">
                          <p class="account-id">ID: {{ currentSession.user_id }}</p>
                          <p class="login-type">
                            {{ getLoginTypeText(currentSession?.login_type) }}登录
                          </p>
                        </div>
                      </div>

                      <button class="btn btn-secondary btn-sm" @click="refreshAccountStatus" :disabled="isRefreshing">
                        <template v-if="isRefreshing">
                          <div class="loading-spinner"></div>
                        </template>
                        <template v-else>
                          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24">
                            <path fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"
                              stroke-width="2"
                              d="M20 11A8.1 8.1 0 0 0 4.5 9M4 5v4h4m-4 4a8.1 8.1 0 0 0 15.5 2m.5 4v-4h-4" />
                          </svg>
                          <span>登录状态</span>
                        </template>
                      </button>
                    </div>

                  </div>
                </div>

                <div v-else class="empty-state">
                  <div class="empty-icon">👤</div>
                  <h3>暂无登录账号</h3>
                  <p class="text-secondary">请使用下方方式登录您的网易云音乐账号</p>
                </div>
              </div>
            </section>

            <section class="sessions-section">
              <!-- Sessions List Section -->
              <div class="glass-card">
                <div class="section-header">
                  <h2 class="section-title">会话列表</h2>
                  <button class="btn btn-secondary btn-sm btn-subscribe" @click="refreshSessions"
                    :disabled="isRefreshingSessions">
                    <div v-if="isRefreshingSessions" class="loading-spinner"></div>

                    <template v-else>
                      <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24">
                        <path fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"
                          stroke-width="2"
                          d="M20 11A8.1 8.1 0 0 0 4.5 9M4 5v4h4m-4 4a8.1 8.1 0 0 0 15.5 2m.5 4v-4h-4" />
                      </svg>
                      <span>刷新</span>
                    </template>
                  </button>
                </div>

                <div v-if="sessions.length > 0" class="sessions-list">
                  <div v-for="session in sessions" :key="session.id" class="session-item"
                    :class="{ 'session-current': session.is_current }">
                    <div class="session-info">
                      <!-- <div class="session-avatar">
                    <div class="avatar avatar-md">
                      <img :src="session.avatar_url || ''" :alt="session.nickname || '用户头像'"
                        @error="handleAvatarError" />
                    </div>
                  </div> -->

                      <div class="session-details">
                        <h4 class="session-name">
                          ID: {{ session.account_id }}
                          <span v-if="session.is_current" class="current-badge">当前</span>
                        </h4>
                        <!-- <p class="session-id text-secondary">{{ session.account_id || session.user_id }}</p> -->
                        <p class="session-time text-tertiary">
                          最后使用: {{ formatTime(session.last_selected_at) }}
                        </p>
                      </div>
                    </div>

                    <div class="session-status">

                      <div class="status-indicator" :class="session.is_valid ? 'status-online' : 'status-offline'">
                        <div class="status-dot"></div>
                        <span>{{ getStatusText(session.is_valid) }}</span>
                      </div>

                      <p class="session-time text-tertiary">
                        {{ getLoginTypeText(session?.login_type) }}登录
                      </p>
                    </div>

                    <div class="session-actions">
                      <button v-if="!session.is_current && session.is_valid" class="btn btn-primary btn-sm"
                        @click="switchToSession(session.id)" :disabled="isSwitchingSession">
                        切换
                      </button>

                      <button v-if="session.is_valid" class="btn btn-danger btn-sm"
                        @click="invalidateSession(session.id)" :disabled="isInvalidatingSession">
                        失效
                      </button>
                    </div>
                  </div>
                </div>

                <div v-else class="empty-state">
                  <div class="empty-icon">🔐</div>
                  <h3>暂无会话</h3>
                  <p class="text-secondary">登录后会话信息将显示在这里</p>
                </div>
              </div>
            </section>
          </div>

          <!-- Login Methods Section -->
          <section class="login-methods-section">
            <div class="login-methods">
              <!-- QR Code Login -->
              <div class="glass-card">
                <div class="section-header">
                  <h2 class="section-title">二维码登录</h2>
                  <p class="text-tertiary">使用网易云音乐 App 扫码登录</p>
                </div>

                <div class="qr-login-container">
                  <div v-if="!qrCode.key" class="qr-actions">
                    <button class="btn btn-primary" @click="startQRLogin" :disabled="isStartingQR">
                      <div v-if="isStartingQR" class="loading-spinner"></div>
                      <span v-else>生成二维码</span>
                    </button>
                  </div>

                  <div v-else class="qr-display">
                    <div class="qr-code-wrapper">
                      <img :src="qrCode.qr_img" alt="登录二维码" class="qr-code-image" />
                      <div v-if="qrCode.status === 'waiting_confirm'" class="qr-overlay">
                        <div class="qr-expired">
                          <!-- <p>已扫码</p> -->
                          <p>请在手机上授权登录</p>
                        </div>
                      </div>
                      <div v-if="qrCode.status === 'expired'" class="qr-overlay">
                        <div class="qr-expired">
                          <p>二维码已过期</p>
                          <button class="btn btn-primary btn-sm" @click="startQRLogin">
                            重新生成
                          </button>
                        </div>
                      </div>
                    </div>

                    <div class="qr-status">
                      <div class="status-indicator" :class="getQRStatusClass(qrCode.status)">
                        <div v-if="qrCode.status === 'waiting_scan'" class="loading-spinner"></div>
                        <span>{{ getQRStatusText(qrCode.status) }}</span>
                      </div>

                      <button v-if="qrCode.status !== 'success'" class="btn btn-secondary btn-sm mt-sm"
                        @click="cancelQRLogin">
                        取消
                      </button>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Cookie Login -->
              <div class="glass-card">
                <div class="section-header">
                  <h2 class="section-title">Cookie 登录</h2>
                  <p class="text-tertiary">手动输入 Cookie 进行登录</p>
                </div>

                <div class="cookie-login-container">
                  <div class="cookie-input-group">
                    <textarea v-model="cookieInput" class="input cookie-textarea" placeholder="请粘贴完整的 Cookie 字符串..."
                      rows="4"></textarea>

                    <div class="cookie-actions mt-sm">
                      <button class="btn btn-primary" @click="loginWithCookie"
                        :disabled="!cookieInput.trim() || isLoggingInWithCookie">
                        <div v-if="isLoggingInWithCookie" class="loading-spinner"></div>
                        <span v-else>使用 Cookie 登录</span>
                      </button>

                      <button class="btn btn-secondary" @click="clearCookieInput">
                        清空
                      </button>
                    </div>
                  </div>

                  <div class="cookie-help mt-sm">
                    <details class="help-details">
                      <summary class="help-summary">如何获取 Cookie？</summary>
                      <div class="help-content">
                        <ol>
                          <li>在浏览器中打开网易云音乐网页版并登录</li>
                          <li>按 F12 打开开发者工具</li>
                          <li>切换到 Network 标签页</li>
                          <li>刷新页面，找到任意请求</li>
                          <li>在请求头中复制 Cookie 字段的值</li>
                        </ol>
                      </div>
                    </details>
                  </div>
                </div>
              </div>
            </div>
          </section>
        </div>

      </div>
    </main>

  </div>
</template>

<script lang="ts" setup>
import { ref, reactive, onMounted, onUnmounted } from 'vue'
// 直接导入服务类
import api from '@/api'
import { toast } from '@/utils/toast'
import type { UserProfile } from '@/api/ncm/user'

// ----------------------
// 类型定义
// ----------------------

interface Session {
  id: number
  user_id?: string
  account_id?: string
  login_type?: string
  nickname?: string
  avatar_url?: string
  last_selected_at?: string
  is_current?: boolean
  is_valid?: boolean
  background_url?: string
}

interface QRCode {
  key: string
  qr_img: string
  status: 'idle' | 'waiting_scan' | 'waiting_confirm' | 'success' | 'expired'
  message: string
}


interface ApiEnvelope<T> {
  code: number
  message?: string
  data?: T
}

function getEnvelope<T>(value: unknown): ApiEnvelope<T> | null {
  if (!value || typeof value !== 'object') return null
  const record = value as Record<string, unknown>
  if (typeof record.code !== 'number') return null
  return record as unknown as ApiEnvelope<T>
}

// ----------------------
// Reactive data
// ----------------------
const currentSession = ref<Session | null>(null)
const sessions = ref<Session[]>([])
const cookieInput = ref('')

// QR Code state
const qrCode = reactive<QRCode>({
  key: '',
  qr_img: '',
  status: 'idle',
  message: ''
})

// Loading states
const isRefreshing = ref(false)
const isStartingQR = ref(false)
const isLoggingInWithCookie = ref(false)
const isRefreshingSessions = ref(false)
const isSwitchingSession = ref(false)
const isInvalidatingSession = ref(false)


// QR polling timer
let qrPollingTimer: number | null = null

// ----------------------
// Lifecycle hooks
// ----------------------
onMounted(async () => {
  await loadUserProfile()
  loadSessions()
})

onUnmounted(() => {
  if (qrPollingTimer) clearInterval(qrPollingTimer)
})


async function loadUserProfile(): Promise<void> {

  // Fetch profile for additional info
  try {
    const profileResult = await api.user.getUserProfile()
    const profile = getEnvelope<UserProfile>(profileResult.success ? profileResult.data : null)?.data
    const sessionResult = await api.user.getCurrentSession()
    const session = getEnvelope<Session>(sessionResult.success ? sessionResult.data : null)?.data
    // Update session display info
    if (profile && session) {
      currentSession.value = {
        id: session?.id || 0,
        user_id: session?.user_id,
        login_type: session?.login_type || '',
        nickname: profile?.nickname || '',
        avatar_url: profile?.avatarUrl || '',
        is_valid: session?.is_valid,
        background_url: profile?.backgroundUrl || ''
      }
    }
  } catch (error) {
    console.error('Failed to load current account:', error)
    toast.show('加载当前账号失败', 'error')
  }
}

async function loadSessions(): Promise<void> {
  try {
    isRefreshingSessions.value = true
    const result = await api.user.listAllSessions()
    const sessionsList = getEnvelope<Session[]>(result.success ? result.data : null)?.data

    if (result.success && sessionsList) {
      // Mark current session
      const currentId = currentSession.value?.id
      // console.log('Current Session ID:', currentId)

      sessions.value = sessionsList.map(s => {
        const isCurrent = currentId !== undefined && s.id === currentId
        // If it's current, use the info we just fetched
        if (isCurrent && currentSession.value) {
          return {
            ...s,
            is_current: true,
            nickname: currentSession.value.nickname,
            avatar_url: currentSession.value.avatar_url
          }
        }
        return {
          ...s,
          is_current: isCurrent
        }
      })
    }
  } catch (error) {
    console.error('Failed to load sessions:', error)
    toast.show('加载会话列表失败', 'error')
  } finally {
    isRefreshingSessions.value = false
  }
}

async function refreshAccountStatus(): Promise<void> {
  try {
    isRefreshing.value = true
    const result = await api.user.getLoginStatus()
    const payload = getEnvelope<unknown>(result.success ? result.data : null)
    if (result.success && payload?.code === 200) {
      await loadUserProfile()
      toast.show('状态刷新成功', 'success')
    } else {
      toast.show('状态刷新失败', 'error')
    }
  } catch (error) {
    console.error('Failed to refresh status:', error)
    toast.show('状态刷新失败', 'error')
  } finally {
    isRefreshing.value = false
  }
}

async function startQRLogin(): Promise<void> {
  try {
    isStartingQR.value = true
    const result = await api.user.startQrLogin()
    const payload = getEnvelope<{ qr_key: string; qr_img: string }>(result.success ? result.data : null)
    if (result.success && payload?.code === 200 && payload.data) {
      qrCode.key = payload.data.qr_key
      qrCode.qr_img = payload.data.qr_img
      qrCode.status = 'waiting_scan'
      qrCode.message = '等待扫码'
      startQRPolling()
      toast.show('二维码生成成功，请使用网易云音乐 App 扫码', 'success')
    } else {
      toast.show('生成二维码失败', 'error')
    }
  } catch (error) {
    console.error('Failed to start QR login:', error)
    toast.show('生成二维码失败', 'error')
  } finally {
    isStartingQR.value = false
  }
}

function startQRPolling(): void {
  if (qrPollingTimer) clearInterval(qrPollingTimer)

  qrPollingTimer = window.setInterval(async () => {
    try {
      const result = await api.user.checkQrLogin(qrCode.key)
      const payload = getEnvelope<{ status: QRCode['status']; message?: string }>(result.success ? result.data : null)
      // console.log('QR Login Check:', payload)
      if (result.success && payload?.data) {
        const status: QRCode['status'] = payload.data.status
        qrCode.status = status
        // console.log('qrCode.status', qrCode.status)

        if (status === 'success') {
          clearInterval(qrPollingTimer!)
          qrPollingTimer = null
          toast.show('登录成功！', 'success')
          await loadUserProfile()
          await loadSessions()
          setTimeout(() => {
            qrCode.key = ''
            qrCode.qr_img = ''
            qrCode.status = 'idle'
          }, 2000)
        } else if (status === 'expired') {
          clearInterval(qrPollingTimer!)
          qrPollingTimer = null
          toast.show('二维码已过期，请重新生成', 'warning')
          if (payload.data.message) qrCode.message = payload.data.message
        }
      }
    } catch (error) {
      console.error('QR polling error:', error)
    }
  }, 2000)
}

function cancelQRLogin(): void {
  if (qrPollingTimer) {
    clearInterval(qrPollingTimer)
    qrPollingTimer = null
  }
  qrCode.key = ''
  qrCode.qr_img = ''
  qrCode.status = 'idle'
  toast.show('已取消二维码登录', 'info')
}

async function loginWithCookie(): Promise<void> {
  if (!cookieInput.value.trim()) {
    toast.show('请输入 Cookie', 'warning')
    return
  }
  try {
    isLoggingInWithCookie.value = true
    const result = await api.user.uploadSession(cookieInput.value.trim())
    const payload = getEnvelope<unknown>(result.success ? result.data : null)
    if (result.success && payload?.code === 200) {
      toast.show('Cookie 登录成功！', 'success')
      cookieInput.value = ''
      await loadUserProfile()
      await loadSessions()
    } else {
      toast.show((payload?.message as string | undefined) || 'Cookie 登录失败', 'error')
    }
  } catch (error) {
    console.error('Failed to login with cookie:', error)
    toast.show('Cookie 登录失败', 'error')
  } finally {
    isLoggingInWithCookie.value = false
  }
}

function clearCookieInput(): void {
  cookieInput.value = ''
}

async function switchToSession(sessionId: number): Promise<void> {
  try {
    isSwitchingSession.value = true
    const result = await api.user.switchSession(sessionId)
    const payload = getEnvelope<unknown>(result.success ? result.data : null)
    if (result.success && payload?.code === 200) {
      toast.show('切换账号成功', 'success')
      await loadUserProfile()
      await loadSessions()
    } else {
      toast.show((payload?.message as string | undefined) || '切换账号失败', 'error')
    }
  } catch (error) {
    console.error('Failed to switch session:', error)
    toast.show('切换账号失败', 'error')
  } finally {
    isSwitchingSession.value = false
  }
}

async function invalidateSession(id: number): Promise<void> {
  if (!confirm('确定要使此会话失效吗？')) return

  try {
    isInvalidatingSession.value = true
    const result = await api.user.invalidateSession(id)
    const payload = getEnvelope<unknown>(result.success ? result.data : null)
    if (result.success && payload?.code === 200) {
      toast.show('会话已失效', 'success')
      // 先获取最新当前会话
      const current = sessions.value.find(s => s.is_current && s.id === id)
      if (current) {
        await loadUserProfile()
      }
      // 然后加载会话列表，确保当前最新状态
      await loadSessions()

    } else {
      toast.show((payload?.message as string | undefined) || '操作失败', 'error')
    }
  } catch (error) {
    console.error('Failed to invalidate session:', error)
    toast.show('操作失败', 'error')
  } finally {
    isInvalidatingSession.value = false
  }
}

async function refreshSessions(): Promise<void> {
  await loadSessions()
  toast.show('会话列表已刷新', 'success')
}

// ----------------------
// Utility functions
// ----------------------
function handleAvatarError(event: Event) {
  const target = event.target as HTMLImageElement
  target.src = ''
}

function getStatusClass(status: Session['is_valid']): string {
  switch (status) {
    case true: return 'status-online'
    case false: return 'status-offline'
    default: return 'status-pending'
  }
}

function getStatusText(status: Session['is_valid']): string {
  switch (status) {
    case true: return '正常'
    case false: return '已失效'
    default: return '未知'
  }
}

function getLoginTypeText(type: string | undefined): string {
  switch (type) {
    case 'qr': return '二维码'
    case 'phone': return '手机号'
    case 'email': return '邮箱'
    case 'cookie_upload': return 'Cookie'
    case 'manual': return '手动'
    default: return '未知'
  }
}

function getQRStatusClass(status: QRCode['status']): string {
  switch (status) {
    case 'waiting_scan':
    case 'waiting_confirm': return 'status-pending'
    case 'success': return 'status-online'
    case 'expired': return 'status-offline'
    default: return 'status-pending'
  }
}

function getQRStatusText(status: QRCode['status']): string {
  switch (status) {
    case 'waiting_scan': return '等待扫码'
    case 'waiting_confirm': return '待确认'
    case 'success': return '登录成功'
    case 'expired': return '已过期'
    default: return '未知状态'
  }
}

function formatTime(timeString?: string): string {
  if (!timeString) return '从未'
  const time = new Date(timeString)
  const now = new Date()
  const diff = now.getTime() - time.getTime()

  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return `${Math.floor(diff / 60000)} 分钟前`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)} 小时前`
  if (diff < 604800000) return `${Math.floor(diff / 86400000)} 天前`

  return time.toLocaleDateString()
}

</script>


<style scoped>
/* 网格布局：桌面端并列，移动端垂直 */
.dashboard-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  /* 1:1 等分 */
  gap: var(--spacing-lg);
  /* 间距 */
  align-items: stretch;
}

/* 确保两个卡片高度一致 */
.full-height {
  display: flex;
  flex-direction: column;
}

/* 针对登录方式内部的优化：改为垂直排列以适应半宽容器 */
.login-methods {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
}

/* 响应式适配：平板或手机端改为单列 */
@media (max-width: 1024px) {
  .dashboard-grid {
    grid-template-columns: 1fr;
  }
}


.account-background {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-size: cover;
  background-position: center;
  filter: blur(10px);
  z-index: -1;
}


.cookie-textarea {
  min-height: 120px;
}

/* 网格基础布局 */
.dashboard-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--spacing-lg);
  align-items: start;
  /* 改为 start，防止左侧卡片被强行拉伸过长 */
}

/* 左侧容器：控制两个卡片的上下间距 */
.dashboard-left {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
  /* 这里设置两个卡片之间的垂直间距 */
}

/* 右侧容器：如果希望右侧卡片高度自动撑满，匹配左侧两个卡片总和 */
.full-height {
  height: 100%;
  min-height: 500px;
  /* 设置一个最小高度保证美观 */
}

/* 移动端适配 */
@media (max-width: 1024px) {
  .dashboard-grid {
    grid-template-columns: 1fr;
  }

  .dashboard-left {
    order: 1;
    /* 移动端可以让账号信息排在最前 */
  }

  .login-methods-section {
    order: 2;
    /* 登录方式排第二 */
  }
}

/* 会话列表内部样式优化 */
.sessions-list {
  max-height: 400px;
  /* 限制高度，超出显示滚动条 */
  overflow-y: auto;
  /* 增加左右和底部的 padding，数值通常略大于阴影的扩散半径 (blur-radius) */
  padding: 0.5rem;
  margin: -0.5rem;

  padding-bottom: 1.1rem;

  /* 使用负外边距抵消 padding，保持视觉上的对齐 */
  padding-right: 8px;
  /* 为滚动条预留空间 */
}

</style>