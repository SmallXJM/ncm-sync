import { ref, readonly, type Ref } from 'vue'

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
   *   @ncm_ws_service("/ncm/download/ws")
   */
  private readonly endpointPath = '/ws/ncm/download'

  private socket: WebSocket | null = null

  private connectionStateRef = ref<WebSocketConnectionState>('idle')
  private lastErrorRef = ref<Error | null>(null)
  private reconnectAttemptsRef = ref(0)
  private lastMessageAtRef = ref<number | null>(null)

  private heartbeatTimer: number | null = null
  private reconnectTimer: number | null = null
  private manualClose = false

  private readonly maxReconnectAttempts = 3
  private readonly reconnectDelayMs = 5000
  private readonly heartbeatIntervalMs = 30000

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
      this.connectionStateRef.value = 'open'
      this.reconnectAttemptsRef.value = 0
      this.lastErrorRef.value = null

      this.flushPendingMessages()

      // if (this.activeSubscriptions.size > 0) {
      //   for (const ch of this.activeSubscriptions) {
      //     this.send({ subscribe: ch })
      //   }
      // }

      this.startHeartbeat()
    }

    this.socket.onmessage = (event) => {
      this.lastMessageAtRef.value = Date.now()
      this.handleMessage(event.data)
    }

    this.socket.onerror = () => {
      this.notifyError(new Error('WebSocket error'))
    }

    this.socket.onclose = () => {
      this.stopHeartbeat()
      this.connectionStateRef.value = 'closed'
      if (!this.manualClose) {
        this.scheduleReconnect()
      }
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
    if (this.reconnectAttemptsRef.value >= this.maxReconnectAttempts) {
      return
    }
    if (this.reconnectTimer != null) {
      return
    }

    this.reconnectAttemptsRef.value += 1
    this.reconnectTimer = window.setTimeout(() => {
      this.reconnectTimer = null
      this.connect()
    }, this.reconnectDelayMs)
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
