<template>
  <div class="page">
    <!-- Header -->
    <header class="page-header">
      <div class="container">
        <h1 class="page-title">账号管理</h1>
        <p class="page-subtitle">管理您的网易云音乐账号和登录会话</p>
      </div>
    </header>

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
                    <img 
                      :src="currentAccount.avatar_url || '/default-avatar.png'" 
                      :alt="currentAccount.nickname || '用户头像'"
                      @error="handleAvatarError"
                    />
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
                    <button 
                      class="btn btn-secondary btn-sm"
                      @click="refreshAccountStatus"
                      :disabled="isRefreshing"
                    >
                      <div v-if="isRefreshing" class="loading-spinner"></div>
                      <span v-else>刷新状态</span>
                    </button>
                    
                    <button 
                      class="btn btn-danger btn-sm"
                      @click="logout"
                      :disabled="isLoggingOut"
                    >
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
                    <button 
                      class="btn btn-primary"
                      @click="startQRLogin"
                      :disabled="isStartingQR"
                    >
                      <div v-if="isStartingQR" class="loading-spinner"></div>
                      <span v-else>生成二维码</span>
                    </button>
                  </div>
                  
                  <div v-else class="qr-display">
                    <div class="qr-code-wrapper">
                      <img 
                        :src="qrCode.qr_img" 
                        alt="登录二维码"
                        class="qr-code-image"
                      />
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
                      
                      <button 
                        v-if="qrCode.status !== 'success'"
                        class="btn btn-secondary btn-sm mt-sm"
                        @click="cancelQRLogin"
                      >
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
                    <textarea
                      v-model="cookieInput"
                      class="input cookie-textarea"
                      placeholder="请粘贴完整的 Cookie 字符串..."
                      rows="4"
                    ></textarea>
                    
                    <div class="cookie-actions mt-sm">
                      <button 
                        class="btn btn-primary"
                        @click="loginWithCookie"
                        :disabled="!cookieInput.trim() || isLoggingInWithCookie"
                      >
                        <div v-if="isLoggingInWithCookie" class="loading-spinner"></div>
                        <span v-else>使用 Cookie 登录</span>
                      </button>
                      
                      <button 
                        class="btn btn-secondary"
                        @click="clearCookieInput"
                      >
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
              <button 
                class="btn btn-secondary btn-sm"
                @click="refreshSessions"
                :disabled="isRefreshingSessions"
              >
                <div v-if="isRefreshingSessions" class="loading-spinner"></div>
                <span v-else>刷新</span>
              </button>
            </div>
            
            <div v-if="sessions.length > 0" class="sessions-list">
              <div 
                v-for="session in sessions"
                :key="session.session_id"
                class="session-item"
                :class="{ 'session-current': session.is_current }"
              >
                <div class="session-info">
                  <div class="session-avatar">
                    <div class="avatar avatar-md">
                      <img 
                        :src="session.avatar_url || '/default-avatar.png'" 
                        :alt="session.nickname || '用户头像'"
                        @error="handleAvatarError"
                      />
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
                  <button 
                    v-if="!session.is_current && session.is_valid"
                    class="btn btn-primary btn-sm"
                    @click="switchToSession(session.session_id)"
                    :disabled="isSwitchingSession"
                  >
                    切换
                  </button>
                  
                  <button 
                    class="btn btn-danger btn-sm"
                    @click="invalidateSession(session.session_id)"
                    :disabled="isInvalidatingSession"
                  >
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

    <!-- Toast Notifications -->
    <div v-if="toast.show" class="toast" :class="toast.type">
      <div class="toast-content">
        <span>{{ toast.message }}</span>
        <button class="toast-close" @click="hideToast">×</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted } from 'vue'
// 直接导入服务类
import api from '@/api'

// Reactive data
const currentAccount = ref(null)
const currentSession = ref(null)
const sessions = ref([])
const cookieInput = ref('')

// QR Code state
const qrCode = reactive({
  key: '',
  qr_img: '',
  status: 'idle', // idle, waiting_scan, waiting_confirm, success, expired
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

// Toast notification
const toast = reactive({
  show: false,
  message: '',
  type: 'info' // info, success, warning, error
})

// QR polling timer
let qrPollingTimer = null

// Lifecycle
onMounted(() => {
  loadCurrentAccount()
  loadSessions()
})

onUnmounted(() => {
  if (qrPollingTimer) {
    clearInterval(qrPollingTimer)
  }
})

// Methods
async function loadCurrentAccount() {
  try {
    const result = await api.user.getCurrentUser()
    
    if (result.success && result.data.code === 200 && result.data.data) {
      currentAccount.value = result.data.data.account
      currentSession.value = result.data.data.session
    } else {
      currentAccount.value = null
      currentSession.value = null
    }
  } catch (error) {
    console.error('Failed to load current account:', error)
    showToast('加载当前账号失败', 'error')
  }
}

async function loadSessions() {
  try {
    isRefreshingSessions.value = true
    const result = await api.user.getSessionsList()
    
    if (result.success && result.data.code === 200) {
      sessions.value = result.data.data.sessions.map(session => ({
        ...session,
        is_current: session.session_id === result.data.data.current_session_id
      }))
    }
  } catch (error) {
    console.error('Failed to load sessions:', error)
    showToast('加载会话列表失败', 'error')
  } finally {
    isRefreshingSessions.value = false
  }
}

async function refreshAccountStatus() {
  try {
    isRefreshing.value = true
    const result = await api.auth.checkStatus()
    
    if (result.success && result.data.code === 200) {
      await loadCurrentAccount()
      showToast('状态刷新成功', 'success')
    } else {
      showToast('状态刷新失败', 'error')
    }
  } catch (error) {
    console.error('Failed to refresh status:', error)
    showToast('状态刷新失败', 'error')
  } finally {
    isRefreshing.value = false
  }
}

async function logout() {
  if (!confirm('确定要退出当前账号吗？')) return
  
  try {
    isLoggingOut.value = true
    // Invalidate current session
    const currentSession = sessions.value.find(s => s.is_current)
    if (currentSession) {
      await invalidateSession(currentSession.session_id)
    }
    
    currentAccount.value = null
    currentSession.value = null
    showToast('已退出登录', 'success')
  } catch (error) {
    console.error('Failed to logout:', error)
    showToast('退出登录失败', 'error')
  } finally {
    isLoggingOut.value = false
  }
}

async function startQRLogin() {
  try {
    isStartingQR.value = true
    const result = await api.auth.startQRLogin()
    
    if (result.success && result.data.code === 200) {
      qrCode.key = result.data.data.qr_key
      qrCode.qr_img = result.data.data.qr_img
      qrCode.status = 'waiting_scan'
      qrCode.message = '等待扫码'
      
      // Start polling
      startQRPolling()
      showToast('二维码生成成功，请使用网易云音乐 App 扫码', 'success')
    } else {
      showToast('生成二维码失败', 'error')
    }
  } catch (error) {
    console.error('Failed to start QR login:', error)
    showToast('生成二维码失败', 'error')
  } finally {
    isStartingQR.value = false
  }
}

function startQRPolling() {
  if (qrPollingTimer) {
    clearInterval(qrPollingTimer)
  }
  
  qrPollingTimer = setInterval(async () => {
    try {
      const result = await api.auth.checkQRLogin(qrCode.key)
      
      if (result.success) {
        const status = result.data.data.status
        qrCode.status = status
        
        if (status === 'success') {
          clearInterval(qrPollingTimer)
          qrPollingTimer = null
          
          showToast('登录成功！', 'success')
          await loadCurrentAccount()
          await loadSessions()
          
          // Reset QR code
          setTimeout(() => {
            qrCode.key = ''
            qrCode.qr_img = ''
            qrCode.status = 'idle'
          }, 2000)
        } else if (status === 'expired') {
          clearInterval(qrPollingTimer)
          qrPollingTimer = null
          showToast('二维码已过期，请重新生成', 'warning')
        }
      }
    } catch (error) {
      console.error('QR polling error:', error)
    }
  }, 2000)
}

function cancelQRLogin() {
  if (qrPollingTimer) {
    clearInterval(qrPollingTimer)
    qrPollingTimer = null
  }
  
  qrCode.key = ''
  qrCode.qr_img = ''
  qrCode.status = 'idle'
  
  showToast('已取消二维码登录', 'info')
}

async function loginWithCookie() {
  if (!cookieInput.value.trim()) {
    showToast('请输入 Cookie', 'warning')
    return
  }
  
  try {
    isLoggingInWithCookie.value = true
    const result = await api.auth.loginWithCookie(cookieInput.value.trim())
    
    if (result.success && result.data.code === 200) {
      showToast('Cookie 登录成功！', 'success')
      cookieInput.value = ''
      await loadCurrentAccount()
      await loadSessions()
    } else {
      showToast(result.data?.message || 'Cookie 登录失败', 'error')
    }
  } catch (error) {
    console.error('Failed to login with cookie:', error)
    showToast('Cookie 登录失败', 'error')
  } finally {
    isLoggingInWithCookie.value = false
  }
}

function clearCookieInput() {
  cookieInput.value = ''
}

async function switchToSession(sessionId) {
  try {
    isSwitchingSession.value = true
    const result = await api.user.switchSession(sessionId)
    
    if (result.success && result.data.code === 200) {
      showToast('切换账号成功', 'success')
      await loadCurrentAccount()
      await loadSessions()
    } else {
      showToast(result.data?.message || '切换账号失败', 'error')
    }
  } catch (error) {
    console.error('Failed to switch session:', error)
    showToast('切换账号失败', 'error')
  } finally {
    isSwitchingSession.value = false
  }
}

async function invalidateSession(sessionId) {
  if (!confirm('确定要使此会话失效吗？')) return
  
  try {
    isInvalidatingSession.value = true
    const result = await api.user.invalidateSession(sessionId)
    
    if (result.success && result.data.code === 200) {
      showToast('会话已失效', 'success')
      await loadSessions()
      
      // If current session was invalidated, reload current account
      const currentSession = sessions.value.find(s => s.is_current && s.session_id === sessionId)
      if (currentSession) {
        await loadCurrentAccount()
      }
    } else {
      showToast(result.data?.message || '操作失败', 'error')
    }
  } catch (error) {
    console.error('Failed to invalidate session:', error)
    showToast('操作失败', 'error')
  } finally {
    isInvalidatingSession.value = false
  }
}

async function refreshSessions() {
  await loadSessions()
  showToast('会话列表已刷新', 'success')
}

// Utility functions
function handleAvatarError(event) {
  event.target.src = '/default-avatar.png'
}

function getStatusClass(status) {
  switch (status) {
    case 'active': return 'status-online'
    case 'disabled': return 'status-offline'
    case 'banned': return 'status-offline'
    default: return 'status-pending'
  }
}

function getStatusText(status) {
  switch (status) {
    case 'active': return '正常'
    case 'disabled': return '已禁用'
    case 'banned': return '已封禁'
    default: return '未知'
  }
}

function getLoginTypeText(type) {
  switch (type) {
    case 'qr': return '二维码'
    case 'phone': return '手机号'
    case 'email': return '邮箱'
    case 'cookie_upload': return 'Cookie'
    default: return '未知'
  }
}

function getQRStatusClass(status) {
  switch (status) {
    case 'waiting_scan': return 'status-pending'
    case 'waiting_confirm': return 'status-pending'
    case 'success': return 'status-online'
    case 'expired': return 'status-offline'
    default: return 'status-pending'
  }
}

function getQRStatusText(status) {
  switch (status) {
    case 'waiting_scan': return '等待扫码'
    case 'waiting_confirm': return '待确认'
    case 'success': return '登录成功'
    case 'expired': return '已过期'
    default: return '未知状态'
  }
}

function formatTime(timeString) {
  if (!timeString) return '从未'
  
  const time = new Date(timeString)
  const now = new Date()
  const diff = now - time
  
  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return `${Math.floor(diff / 60000)} 分钟前`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)} 小时前`
  if (diff < 604800000) return `${Math.floor(diff / 86400000)} 天前`
  
  return time.toLocaleDateString()
}

function showToast(message, type = 'info') {
  toast.message = message
  toast.type = type
  toast.show = true
  
  setTimeout(() => {
    hideToast()
  }, 5000)
}

function hideToast() {
  toast.show = false
}
</script>

