import { ref, type Ref } from 'vue'

export interface WebSocketMessage {
  type: string
  task_id?: string
  status?: string
  message?: string
  progress?: number
  timestamp: string
  data?: any
}

export interface ConnectionStatus {
  connected: boolean
  connecting: boolean
  lastConnected?: Date
  connectionCount: number
}

export class WebSocketClient {
  private ws: WebSocket | null = null
  private token: string
  private url: string
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5
  private reconnectDelay = 1000 // 初始重连延迟（毫秒）
  private maxReconnectDelay = 30000 // 最大重连延迟（毫秒）
  private heartbeatInterval: number | null = null
  private heartbeatTimer: number | null = null
  private connectionTimer: number | null = null
  
  // 响应式状态
  public connectionStatus: Ref<ConnectionStatus> = ref({
    connected: false,
    connecting: false,
    connectionCount: 0
  })
  
  // 事件监听器
  private messageHandlers: Map<string, Array<(message: WebSocketMessage) => void>> = new Map()
  private connectionHandlers: Array<(connected: boolean) => void> = []
  
  constructor(token: string, baseUrl: string = '') {
    this.token = token
    // 构建WebSocket URL
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = baseUrl || window.location.host
    this.url = `${protocol}//${host}/api/v1/ws?token=${encodeURIComponent(token)}`
  }
  
  /**
   * 连接WebSocket
   */
  public async connect(): Promise<boolean> {
    if (this.ws?.readyState === WebSocket.OPEN) {
      console.log('WebSocket已连接')
      return true
    }
    
    if (this.connectionStatus.value.connecting) {
      console.log('WebSocket正在连接中')
      return false
    }
    
    this.connectionStatus.value.connecting = true
    
    try {
      console.log('连接WebSocket:', this.url)
      this.ws = new WebSocket(this.url)
      
      this.ws.onopen = this.handleOpen.bind(this)
      this.ws.onmessage = this.handleMessage.bind(this)
      this.ws.onclose = this.handleClose.bind(this)
      this.ws.onerror = this.handleError.bind(this)
      
      // 设置连接超时
      this.connectionTimer = setTimeout(() => {
        if (this.ws?.readyState !== WebSocket.OPEN) {
          console.error('WebSocket连接超时')
          this.ws?.close()
        }
      }, 10000)
      
      return true
    } catch (error) {
      console.error('WebSocket连接失败:', error)
      this.connectionStatus.value.connecting = false
      return false
    }
  }
  
  /**
   * 断开连接
   */
  public disconnect(): void {
    console.log('主动断开WebSocket连接')
    this.reconnectAttempts = this.maxReconnectAttempts // 阻止重连
    
    if (this.heartbeatTimer) {
      clearTimeout(this.heartbeatTimer)
      this.heartbeatTimer = null
    }
    
    if (this.connectionTimer) {
      clearTimeout(this.connectionTimer)
      this.connectionTimer = null
    }
    
    if (this.ws) {
      this.ws.close(1000, 'User disconnected')
      this.ws = null
    }
    
    this.updateConnectionStatus(false)
  }
  
  /**
   * 发送消息
   */
  public send(message: object): boolean {
    if (this.ws?.readyState === WebSocket.OPEN) {
      try {
        this.ws.send(JSON.stringify(message))
        return true
      } catch (error) {
        console.error('发送WebSocket消息失败:', error)
        return false
      }
    } else {
      console.warn('WebSocket未连接，无法发送消息')
      return false
    }
  }
  
  /**
   * 订阅消息类型
   */
  public on(messageType: string, handler: (message: WebSocketMessage) => void): void {
    if (!this.messageHandlers.has(messageType)) {
      this.messageHandlers.set(messageType, [])
    }
    this.messageHandlers.get(messageType)!.push(handler)
  }
  
  /**
   * 取消订阅消息类型
   */
  public off(messageType: string, handler?: (message: WebSocketMessage) => void): void {
    if (!this.messageHandlers.has(messageType)) return
    
    if (handler) {
      const handlers = this.messageHandlers.get(messageType)!
      const index = handlers.indexOf(handler)
      if (index > -1) {
        handlers.splice(index, 1)
      }
    } else {
      this.messageHandlers.delete(messageType)
    }
  }
  
  /**
   * 监听连接状态变化
   */
  public onConnectionChange(handler: (connected: boolean) => void): void {
    this.connectionHandlers.push(handler)
  }
  
  /**
   * 订阅任务更新
   */
  public subscribeToTask(taskId: string): void {
    this.send({
      type: 'subscribe',
      task_id: taskId
    })
  }
  
  /**
   * 发送心跳
   */
  public ping(): void {
    this.send({ type: 'ping' })
  }
  
  /**
   * 获取连接状态
   */
  public getStatus(): void {
    this.send({ type: 'get_status' })
  }
  
  // 私有方法
  private handleOpen(event: Event): void {
    console.log('WebSocket连接成功')
    
    if (this.connectionTimer) {
      clearTimeout(this.connectionTimer)
      this.connectionTimer = null
    }
    
    this.reconnectAttempts = 0
    this.reconnectDelay = 1000
    this.updateConnectionStatus(true)
    
    // 开始心跳检测
    this.startHeartbeat()
    
    // 获取连接状态
    this.getStatus()
  }
  
  private handleMessage(event: MessageEvent): void {
    try {
      const message: WebSocketMessage = JSON.parse(event.data)
      console.log('收到WebSocket消息:', message)
      
      // 处理心跳响应
      if (message.type === 'pong' || message.type === 'heartbeat') {
        return
      }
      
      // 分发消息给对应的处理器
      const handlers = this.messageHandlers.get(message.type) || []
      handlers.forEach(handler => {
        try {
          handler(message)
        } catch (error) {
          console.error('消息处理器错误:', error)
        }
      })
      
      // 分发给通用处理器
      const allHandlers = this.messageHandlers.get('*') || []
      allHandlers.forEach(handler => {
        try {
          handler(message)
        } catch (error) {
          console.error('通用消息处理器错误:', error)
        }
      })
      
    } catch (error) {
      console.error('解析WebSocket消息失败:', error)
    }
  }
  
  private handleClose(event: CloseEvent): void {
    console.log('WebSocket连接关闭:', event.code, event.reason)
    
    this.updateConnectionStatus(false)
    this.stopHeartbeat()
    
    // 如果不是主动断开，尝试重连
    if (event.code !== 1000 && this.reconnectAttempts < this.maxReconnectAttempts) {
      this.scheduleReconnect()
    }
  }
  
  private handleError(event: Event): void {
    console.error('WebSocket错误:', event)
    this.updateConnectionStatus(false)
  }
  
  private updateConnectionStatus(connected: boolean): void {
    const wasConnected = this.connectionStatus.value.connected
    
    this.connectionStatus.value.connected = connected
    this.connectionStatus.value.connecting = false
    
    if (connected) {
      this.connectionStatus.value.lastConnected = new Date()
      this.connectionStatus.value.connectionCount++
    }
    
    // 通知连接状态变化
    if (wasConnected !== connected) {
      this.connectionHandlers.forEach(handler => {
        try {
          handler(connected)
        } catch (error) {
          console.error('连接状态处理器错误:', error)
        }
      })
    }
  }
  
  private scheduleReconnect(): void {
    const delay = Math.min(
      this.reconnectDelay * Math.pow(2, this.reconnectAttempts),
      this.maxReconnectDelay
    )
    
    console.log(`${delay}ms后尝试重连 (第${this.reconnectAttempts + 1}次)`)
    
    setTimeout(() => {
      this.reconnectAttempts++
      this.connect()
    }, delay)
  }
  
  private startHeartbeat(): void {
    // 停止现有的心跳
    this.stopHeartbeat()
    
    // 每30秒发送一次心跳
    this.heartbeatTimer = setInterval(() => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        this.ping()
      }
    }, 30000)
  }
  
  private stopHeartbeat(): void {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer)
      this.heartbeatTimer = null
    }
  }
}

// 全局WebSocket实例
let globalWebSocketClient: WebSocketClient | null = null

/**
 * 创建或获取全局WebSocket客户端
 */
export function useWebSocket(token?: string): WebSocketClient | null {
  if (!globalWebSocketClient && token) {
    globalWebSocketClient = new WebSocketClient(token)
  }
  return globalWebSocketClient
}

/**
 * 清理全局WebSocket客户端
 */
export function clearWebSocket(): void {
  if (globalWebSocketClient) {
    globalWebSocketClient.disconnect()
    globalWebSocketClient = null
  }
}

export default WebSocketClient