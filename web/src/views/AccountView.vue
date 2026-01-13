<template>
  <div class="page">
    <!-- Main Content -->
    <main>
      <div class="container">
        <!-- Current Account Section -->
        <section class="mb-2xl">
          <div class="glass-card">
            <h2 class="section-title mb-lg">当前账号</h2>

            <div v-if="currentAccount" class="current-account-info">
              <div class="account-header">
                <div class="avatar-container">
                  <div class="avatar avatar-xl">
                    <img :src="currentAccount.avatar_url || '/default-avatar.png'"
                      :alt="currentAccount.nickname || '用户头像'" @error="handleAvatarError" />
                  </div>
                  <div class="status-badge">
                    <div class="status-dot" :class="getStatusClass(currentAccount.status)"></div>
                    <span>{{ getStatusText(currentAccount.status) }}</span>
                  </div>
                </div>

                <div class="account-details">
                  <h3 class="account-name">{{ currentAccount.nickname || '未知用户' }}</h3>
                  <p class="account-id text-secondary">ID: {{ currentAccount.account_id }}</p>
                  <p class="login-type text-tertiary">
                    登录方式: {{ getLoginTypeText(currentSession?.login_type) }}
                  </p>

                  <div class="account-actions mt-md">
                    <button class="btn btn-secondary btn-sm" @click="refreshAccountStatus" :disabled="isRefreshing">
                      <div v-if="isRefreshing" class="loading-spinner"></div>
                      <span v-else>刷新状态</span>
                    </button>

                    <button class="btn btn-danger btn-sm" @click="logout" :disabled="isLoggingOut">
                      <div v-if="isLoggingOut" class="loading-spinner"></div>
                      <span v-else>退出登录</span>
                    </button>
                  </div>
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

        <!-- Login Methods Section -->
        <section class="mb-2xl">
          <div class="glass-card">
            <h2 class="section-title mb-lg">登录方式</h2>

            <div class="login-methods">
              <!-- QR Code Login -->
              <div class="login-method">
                <div class="method-header">
                  <h3>二维码登录</h3>
                  <p class="text-secondary">使用网易云音乐 App 扫码登录</p>
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
              <div class="login-method">
                <div class="method-header">
                  <h3>Cookie 登录</h3>
                  <p class="text-secondary">手动输入 Cookie 进行登录</p>
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
          </div>
        </section>

        <!-- Sessions List Section -->
        <section>
          <div class="glass-card">
            <div class="section-header">
              <h2 class="section-title">会话列表</h2>
              <button class="btn btn-secondary btn-sm" @click="refreshSessions" :disabled="isRefreshingSessions">
                <div v-if="isRefreshingSessions" class="loading-spinner"></div>
                <span v-else>刷新</span>
              </button>
            </div>

            <div v-if="sessions.length > 0" class="sessions-list">
              <div v-for="session in sessions" :key="session.session_id" class="session-item"
                :class="{ 'session-current': session.is_current }">
                <div class="session-info">
                  <div class="session-avatar">
                    <div class="avatar avatar-md">
                      <img :src="session.avatar_url || '/default-avatar.png'" :alt="session.nickname || '用户头像'"
                        @error="handleAvatarError" />
                    </div>
                  </div>

                  <div class="session-details">
                    <h4 class="session-name">
                      {{ session.nickname || '未知用户' }}
                      <span v-if="session.is_current" class="current-badge">当前</span>
                    </h4>
                    <p class="session-id text-secondary">{{ session.account?.account_id }}</p>
                    <p class="session-time text-tertiary">
                      最后使用: {{ formatTime(session.last_selected_at) }}
                    </p>
                  </div>
                </div>

                <div class="session-status">
                  <div class="status-indicator" :class="session.is_valid ? 'status-online' : 'status-offline'">
                    <div class="status-dot"></div>
                    <span>{{ session.is_valid ? '有效' : '已失效' }}</span>
                  </div>
                </div>

                <div class="session-actions">
                  <button v-if="!session.is_current && session.is_valid" class="btn btn-primary btn-sm"
                    @click="switchToSession(session.session_id)" :disabled="isSwitchingSession">
                    切换
                  </button>

                  <button class="btn btn-danger btn-sm" @click="invalidateSession(session.session_id)"
                    :disabled="isInvalidatingSession">
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
    </main>

  </div>
</template>

<script lang="ts" setup>
import { ref, reactive, onMounted, onUnmounted } from 'vue'
// 直接导入服务类
import api from '@/api'
import { toast } from '@/utils/toast'

// ----------------------
// 类型定义
// ----------------------
interface Account {
  account_id: string
  nickname?: string
  avatar_url?: string
  status: 'active' | 'disabled' | 'banned' | string
}

interface Session {
  session_id: string
  login_type?: string
  nickname?: string
  avatar_url?: string
  last_selected_at?: string
  is_current?: boolean
  is_valid?: boolean
  account?: Account
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
const currentAccount = ref<Account | null>(null)
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
const isLoggingOut = ref(false)
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
onMounted(() => {
  loadCurrentAccount()
  loadSessions()
})

onUnmounted(() => {
  if (qrPollingTimer) clearInterval(qrPollingTimer)
})

// ----------------------
// Methods
// ----------------------
async function loadCurrentAccount(): Promise<void> {
  try {
    const result = await api.user.getCurrentUser()
    const payload = getEnvelope<{ account: Account; session: Session }>(result.success ? result.data : null)
    if (result.success && payload?.code === 200 && payload.data) {
      currentAccount.value = payload.data.account
      currentSession.value = payload.data.session
    } else {
      currentAccount.value = null
      currentSession.value = null
    }
  } catch (error) {
    console.error('Failed to load current account:', error)
    toast.show('加载当前账号失败', 'error')
  }
}

async function loadSessions(): Promise<void> {
  try {
    isRefreshingSessions.value = true
    const result = await api.user.getSessionsList()
    const payload = getEnvelope<{ sessions: Session[]; current_session_id: string }>(result.success ? result.data : null)
    if (result.success && payload?.code === 200 && payload.data) {
      const currentSessionId = payload.data.current_session_id
      sessions.value = payload.data.sessions.map((session: Session) => ({
        ...session,
        is_current: session.session_id === currentSessionId,
      }))
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
    const result = await api.auth.checkStatus()
    const payload = getEnvelope<unknown>(result.success ? result.data : null)
    if (result.success && payload?.code === 200) {
      await loadCurrentAccount()
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

async function logout(): Promise<void> {
  if (!confirm('确定要退出当前账号吗？')) return

  try {
    isLoggingOut.value = true
    const current = sessions.value.find(s => s.is_current)
    if (current) {
      await invalidateSession(current.session_id)
    }

    currentAccount.value = null
    currentSession.value = null
    toast.show('已退出登录', 'success')
  } catch (error) {
    console.error('Failed to logout:', error)
    toast.show('退出登录失败', 'error')
  } finally {
    isLoggingOut.value = false
  }
}

async function startQRLogin(): Promise<void> {
  try {
    isStartingQR.value = true
    const result = await api.auth.startQRLogin()
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
      const result = await api.auth.checkQRLogin(qrCode.key)
      const payload = getEnvelope<{ status: QRCode['status']; message?: string }>(result.success ? result.data : null)
      if (result.success && payload?.code === 200 && payload.data) {
        const status: QRCode['status'] = payload.data.status
        qrCode.status = status

        if (status === 'success') {
          clearInterval(qrPollingTimer!)
          qrPollingTimer = null
          toast.show('登录成功！', 'success')
          await loadCurrentAccount()
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
    const result = await api.auth.loginWithCookie(cookieInput.value.trim())
    const payload = getEnvelope<unknown>(result.success ? result.data : null)
    if (result.success && payload?.code === 200) {
      toast.show('Cookie 登录成功！', 'success')
      cookieInput.value = ''
      await loadCurrentAccount()
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

async function switchToSession(sessionId: string): Promise<void> {
  try {
    isSwitchingSession.value = true
    const result = await api.user.switchSession(sessionId)
    const payload = getEnvelope<unknown>(result.success ? result.data : null)
    if (result.success && payload?.code === 200) {
      toast.show('切换账号成功', 'success')
      await loadCurrentAccount()
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

async function invalidateSession(sessionId: string): Promise<void> {
  if (!confirm('确定要使此会话失效吗？')) return

  try {
    isInvalidatingSession.value = true
    const result = await api.user.invalidateSession(sessionId)
    const payload = getEnvelope<unknown>(result.success ? result.data : null)
    if (result.success && payload?.code === 200) {
      toast.show('会话已失效', 'success')
      await loadSessions()
      const current = sessions.value.find(s => s.is_current && s.session_id === sessionId)
      if (current) {
        await loadCurrentAccount()
      }
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
  target.src = '/default-avatar.png'
}

function getStatusClass(status: Account['status']): string {
  switch (status) {
    case 'active': return 'status-online'
    case 'disabled': 
    case 'banned': return 'status-offline'
    default: return 'status-pending'
  }
}

function getStatusText(status: Account['status']): string {
  switch (status) {
    case 'active': return '正常'
    case 'disabled': return '已禁用'
    case 'banned': return '已封禁'
    default: return '未知'
  }
}

function getLoginTypeText(type: string | undefined): string {
  switch (type) {
    case 'qr': return '二维码'
    case 'phone': return '手机号'
    case 'email': return '邮箱'
    case 'cookie_upload': return 'Cookie'
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
