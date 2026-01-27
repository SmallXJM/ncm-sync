import { ref, readonly, type Ref } from 'vue'
import { toast } from '@/utils/toast'

/**
 * WebSocket 连接状态
 */
export type WebSocketConnectionState = 'idle' | 'connecting' | 'open' | 'closed' | 'error'

/**
 * 支持的订阅频道类型
 *
 * 后端目前约定：
 * - "tasks"     下载任务列表
 * - "sysInfo"   系统信息
 * - "scheduler" 调度器运行状态
 *
 * 预留 string 方便后续扩展模块。
 */
export type WsChannel = 'tasks' | 'sysInfo' | 'scheduler' | string

/**
 * WebSocket 原始消息的键值映射
 *
 * 后端每条推送消息形如：
 * - {"tasks": {...}}
 * - {"sysInfo": {...}}
 * - {"scheduler": {...}}
 * 也可能在后续扩展新的键。
 */
export type WsMessageMap = Record<string, unknown>

/**
 * WebSocket 服务对外暴露的响应式状态
 */
export interface WebSocketServiceState {
  /**
   * 当前连接状态
   */
  connectionState: Ref<WebSocketConnectionState>

  /**
   * 最近一次错误（如果有）
   */
  lastError: Ref<Error | null>

  /**
   * 当前重连次数
   */
  reconnectAttempts: Ref<number>

  /**
   * 面向用户的状态提示文案
   */
  userMessage: Ref<string | null>

  /**
   * 是否可以通过按钮手动发起重连
   */
  canManualReconnect: Ref<boolean>

  /**
   * 最近一次收到消息的时间戳（毫秒）
   */
  lastMessageAt: Ref<number | null>

  /**
   * 已缓存的频道数据快照
   *
   * - tasks:   下载任务视图
   * - sysInfo: 系统信息视图
   * - scheduler: 调度器状态视图
   * - raw:    原始键值映射（方便不定结构的数据）
   */
  data: {
    tasks: Ref<unknown | null>
    sysInfo: Ref<unknown | null>
    scheduler: Ref<unknown | null>
    raw: Ref<WsMessageMap>
  }
}

/**
 * WebSocket 错误回调类型
 */
export type WebSocketErrorListener = (error: Error) => void

/**
 * 单页（路由）订阅配置
 *
 * 通过 key（一般使用路由 name）区分不同页面的订阅需求：
 * - 页面进入时调用 enterPage(key, channels)
 * - 页面离开时调用 leavePage(key)
 */
export interface PageSubscription {
  key: string
  channels: WsChannel[]
}

/**
 * WebSocket 客户端服务（单例）
 *
 * 负责：
 * - 长连接管理（自动重连、心跳）
 * - 订阅 / 退订协议发送
 * - 消息分发到响应式状态
 */
class WebSocketClientService {
  /**
   * 后端 WebSocket 路径
   *
   * 对应后端：
   *   @ncm_ws_service('/ws/ncm')
   */
  private readonly endpointPath = '/ws/ncm'

  private socket: WebSocket | null = null

  private connectionStateRef = ref<WebSocketConnectionState>('idle')
  private lastErrorRef = ref<Error | null>(null)
  private reconnectAttemptsRef = ref(0)
  private lastMessageAtRef = ref<number | null>(null)

  private userMessageRef = ref<string | null>(null)
  private canManualReconnectRef = ref(false)

  private heartbeatTimer: number | null = null
  private reconnectTimer: number | null = null
  private manualClose = false

  private readonly maxReconnectAttempts = 10
  private readonly heartbeatIntervalMs = 30000

  /**
   * 不可恢复的关闭代码（需要用户干预，例如鉴权失败）
   */
  private readonly unrecoverableCloseCodes = new Set<number>([4001, 1008])

  constructor() {
    if (typeof window !== 'undefined' && typeof window.addEventListener === 'function') {
      window.addEventListener('online', this.handleOnline)
    }
  }

  /**
   * 当前已生效的订阅集合（去重后结果）
   */
  private readonly activeSubscriptions = new Set<WsChannel>()

  /**
   * 页面级别的订阅配置
   */
  private readonly pageSubscriptions = new Map<string, Set<WsChannel>>()

  /**
   * 在连接尚未建立时待发送的消息队列
   */
  private readonly pendingMessages: object[] = []

  /**
   * 错误监听器集合
   */
  private readonly errorListeners = new Set<WebSocketErrorListener>()

  /**
   * 响应式数据缓存
   */
  private readonly state: WebSocketServiceState = {
    connectionState: this.connectionStateRef,
    lastError: this.lastErrorRef,
    reconnectAttempts: this.reconnectAttemptsRef,
    lastMessageAt: this.lastMessageAtRef,
    userMessage: this.userMessageRef,
    canManualReconnect: this.canManualReconnectRef,
    data: {
      tasks: ref<unknown | null>(null),
      sysInfo: ref<unknown | null>(null),
      scheduler: ref<unknown | null>(null),
      raw: ref<WsMessageMap>({}),
    },
  }

  /**
   * 获取只读形式的响应式状态
   */
  get reactiveState(): WebSocketServiceState {
    return {
      connectionState: readonly(this.connectionStateRef),
      lastError: readonly(this.lastErrorRef),
      reconnectAttempts: readonly(this.reconnectAttemptsRef),
      lastMessageAt: readonly(this.lastMessageAtRef),
      userMessage: readonly(this.userMessageRef),
      canManualReconnect: readonly(this.canManualReconnectRef),
      data: {
        tasks: readonly(this.state.data.tasks),
        sysInfo: readonly(this.state.data.sysInfo),
        scheduler: readonly(this.state.data.scheduler),
        raw: readonly(this.state.data.raw),
      },
    }
  }

  /**
   * 对外暴露的只读数据别名，便于解构使用
   */
  get data() {
    return this.reactiveState.data
  }

  /**
   * 注册错误监听器，返回取消函数
   */
  onError(listener: WebSocketErrorListener): () => void {
    this.errorListeners.add(listener)
    return () => {
      this.errorListeners.delete(listener)
    }
  }

  /**
   * 触发错误事件并更新状态
   */
  private notifyError(error: Error) {
    this.lastErrorRef.value = error
    this.connectionStateRef.value = 'error'
    this.errorListeners.forEach((listener) => {
      try {
        listener(error)
      } catch {
        // 忽略监听器自身的错误
      }
    })
  }

  /**
   * 主动建立连接（通常无需手动调用，订阅时会自动触发）
   */
  connect(): void {
    if (this.socket && (this.socket.readyState === WebSocket.OPEN || this.socket.readyState === WebSocket.CONNECTING)) {
      return
    }

    if (typeof window === 'undefined') {
      return
    }

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = window.location.host
    const url = `${protocol}//${host}${this.endpointPath}`

    this.manualClose = false
    this.connectionStateRef.value = 'connecting'

    try {
      this.socket = new WebSocket(url)
    } catch (err) {
      const error = err instanceof Error ? err : new Error(String(err))
      this.notifyError(error)
      this.scheduleReconnect()
      return
    }

    this.socket.onopen = () => {
      const wasReconnecting = this.reconnectAttemptsRef.value > 0

      this.connectionStateRef.value = 'open'
      this.reconnectAttemptsRef.value = 0
      this.lastErrorRef.value = null
      this.userMessageRef.value = null
      this.canManualReconnectRef.value = false

      this.flushPendingMessages()

      if (wasReconnecting && this.activeSubscriptions.size > 0) {
        this.activeSubscriptions.forEach((ch) => {
          this.send({ subscribe: ch })
        })
      }

      this.startHeartbeat()
    }

    this.socket.onmessage = (event) => {
      this.lastMessageAtRef.value = Date.now()
      this.handleMessage(event.data)
    }

    this.socket.onerror = () => {
      this.notifyError(new Error('WebSocket error'))
    }

    this.socket.onclose = (event) => {
      this.stopHeartbeat()
      this.connectionStateRef.value = 'closed'

      if (this.manualClose) {
        this.reconnectAttemptsRef.value = 0
        this.canManualReconnectRef.value = false
        return
      }

      const code = (event && (event as CloseEvent).code) || 1005
      if (this.unrecoverableCloseCodes.has(code)) {
        this.connectionStateRef.value = 'error'
        // this.userMessageRef.value = '连接鉴权失败，请检查登录状态'
        this.canManualReconnectRef.value = true
        toast.error('连接鉴权失败，请检查登录状态')
        return
      }

      // this.userMessageRef.value = '连接断开，正在尝试重连...'
      this.scheduleReconnect()
    }
  }

  /**
   * 主动断开连接（一般在应用销毁时调用）
   */
  disconnect(): void {
    this.manualClose = true
    this.stopHeartbeat()
    if (this.reconnectTimer != null) {
      window.clearTimeout(this.reconnectTimer)
      this.reconnectTimer = null
    }
    if (this.socket) {
      try {
        this.socket.close()
      } catch {
        // 忽略关闭错误
      } finally {
        this.socket = null
      }
    }
    this.connectionStateRef.value = 'closed'
  }

  /**
   * 确保连接已创建
   *
   * - 若当前为 idle/closed，会尝试建立新连接。
   * - 若正在连接/已连接，什么也不做。
   */
  private ensureConnected() {
    if (this.connectionStateRef.value === 'idle' || this.connectionStateRef.value === 'closed') {
      this.connect()
    }
  }

  /**
   * 启动心跳定时器（简单的 ping 消息）
   */
  private startHeartbeat() {
    if (this.heartbeatTimer != null) {
      window.clearInterval(this.heartbeatTimer)
    }
    this.heartbeatTimer = window.setInterval(() => {
      if (this.socket && this.socket.readyState === WebSocket.OPEN) {
        this.send({ ping: true })
      }
    }, this.heartbeatIntervalMs)
  }

  /**
   * 停止心跳定时器
   */
  private stopHeartbeat() {
    if (this.heartbeatTimer != null) {
      window.clearInterval(this.heartbeatTimer)
      this.heartbeatTimer = null
    }
  }

  /**
   * 安排一次重连尝试
   */
  private scheduleReconnect() {
    if (typeof window === 'undefined') return
    if (this.manualClose) return
    if (this.reconnectAttemptsRef.value >= this.maxReconnectAttempts) {
      this.userMessageRef.value = '连接已断开'
      this.canManualReconnectRef.value = true
      // toast.error('连接重连失败，请重试')
      return
    }
    if (this.reconnectTimer != null) {
      return
    }

    // this.userMessageRef.value = '连接失败'

    const nextAttempt = this.reconnectAttemptsRef.value + 1
    this.reconnectAttemptsRef.value = nextAttempt
    const delay = this.getReconnectDelayMs(nextAttempt)

    this.reconnectTimer = window.setTimeout(() => {
      // this.userMessageRef.value = `尝试重连中`
      this.reconnectTimer = null
      this.connect()
    }, delay)
  }

  /**
   * 根据不同阶段返回重连间隔
   */
  private getReconnectDelayMs(attempt: number): number {
    if (attempt <= 3) return 2000
    if (attempt <= 6) return 5000
    return 15000
  }

  /**
   * 网络恢复时尝试重连
   */
  private handleOnline = () => {
    if (typeof window === 'undefined') return
    if (this.manualClose) return
    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      return
    }
    if (this.connectionStateRef.value === 'open' || this.connectionStateRef.value === 'connecting') {
      return
    }

    this.reconnectAttemptsRef.value = 0
    this.userMessageRef.value = null
    this.canManualReconnectRef.value = false

    this.connect()
  }

  /**
   * 用户手动触发重连
   */
  retryConnect(): void {
    if (typeof window === 'undefined') return
    this.manualClose = false
    this.reconnectAttemptsRef.value = 0
    this.userMessageRef.value = '尝试重连中'
    this.canManualReconnectRef.value = false

    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      return
    }

    this.connect()
  }

  /**
   * 发送消息，如果未连接则进入等待队列
   */
  private send(message: object) {
    this.ensureConnected()

    const payload = JSON.stringify(message)

    if (!this.socket || this.socket.readyState !== WebSocket.OPEN) {
      this.pendingMessages.push(message)
      return
    }

    try {
      this.socket.send(payload)
    } catch (err) {
      const error = err instanceof Error ? err : new Error(String(err))
      this.notifyError(error)
    }
  }

  /**
   * 发送积压的消息
   */
  private flushPendingMessages() {
    if (!this.socket || this.socket.readyState !== WebSocket.OPEN) {
      return
    }

    while (this.pendingMessages.length > 0) {
      const message = this.pendingMessages.shift()
      if (!message) continue
      try {
        this.socket.send(JSON.stringify(message))
      } catch (err) {
        const error = err instanceof Error ? err : new Error(String(err))
        this.notifyError(error)
        break
      }
    }
  }

  /**
   * 处理从服务器收到的原始消息
   */
  private handleMessage(raw: unknown) {
    if (typeof raw !== 'string') {
      return
    }

    let data: unknown
    try {
      data = JSON.parse(raw)
    } catch (err) {
      const error = err instanceof Error ? err : new Error(String(err))
      this.notifyError(error)
      return
    }

    if (!data || typeof data !== 'object') {
      return
    }

    const record = data as Record<string, unknown>

    // 更新原始映射缓存（浅合并）
    this.state.data.raw.value = {
      ...this.state.data.raw.value,
      ...record,
    }

    // 针对已知频道做专门映射，方便视图层使用
    if (Object.prototype.hasOwnProperty.call(record, 'tasks')) {
      this.state.data.tasks.value = record.tasks as unknown
    }
    if (Object.prototype.hasOwnProperty.call(record, 'sysInfo')) {
      this.state.data.sysInfo.value = record.sysInfo as unknown
    }
    if (Object.prototype.hasOwnProperty.call(record, 'scheduler')) {
      this.state.data.scheduler.value = record.scheduler as unknown
    }
  }

  /**
   * 将通用入参规范化为数组形式
   */
  private normalizeChannels(input: WsChannel | WsChannel[]): WsChannel[] {
    if (Array.isArray(input)) return input
    return [input]
  }

  /**
   * 订阅一个或多个频道
   *
   * - 会自动建立连接
   * - 会维护 activeSubscriptions 集合
   * - 通过 {"subscribe": "<name>"} 消息通知后端
   */
  subscribe(channels: WsChannel | WsChannel[]): void {
    const list = this.normalizeChannels(channels)

    if (list.length === 0) return

    list.forEach((ch) => this.activeSubscriptions.add(ch))

    list.forEach((ch) => {
      this.send({ subscribe: ch })
    })
  }

  /**
   * 退订一个或多个频道
   */
  unsubscribe(channels: WsChannel | WsChannel[]): void {
    const list = this.normalizeChannels(channels)

    if (list.length === 0) return

    list.forEach((ch) => this.activeSubscriptions.delete(ch))

    list.forEach((ch) => {
      this.send({ unsubscribe: ch })
    })
  }

  /**
   * 订阅所有已知频道
   */
  subscribeAll(): void {
    this.send({ subscribe: 'all' })
  }

  /**
   * 退订所有频道
   */
  unsubscribeAll(): void {
    this.activeSubscriptions.clear()
    this.send({ unsubscribe: 'all' })
  }

  /**
   * 页面进入时调用：
   * - 会记录页面与频道之间的映射关系
   * - 会对需要的频道发起订阅
   */
  enterPage(key: string, channels: WsChannel | WsChannel[]): void {
    const list = this.normalizeChannels(channels)
    if (list.length === 0) return

    const set = new Set<WsChannel>(list)
    this.pageSubscriptions.set(key, set)

    this.subscribe(list)
  }

  /**
   * 页面离开时调用：
   * - 根据之前记录的配置退订频道
   */
  leavePage(key: string): void {
    const set = this.pageSubscriptions.get(key)
    if (!set) return

    this.pageSubscriptions.delete(key)

    const channels = Array.from(set)
    if (channels.length > 0) {
      this.unsubscribe(channels)
    }
  }
}

/**
 * 单例实例
 */
export const wsClient = new WebSocketClientService()

export default wsClient
