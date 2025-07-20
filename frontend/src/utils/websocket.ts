import type { WebSocketMessage } from '@/types/api'

export type WebSocketEventHandler = (data: any) => void

export interface WebSocketOptions {
  url?: string
  reconnectAttempts?: number
  reconnectInterval?: number
  heartbeatInterval?: number
  onOpen?: () => void
  onClose?: (event: CloseEvent) => void
  onError?: (event: Event) => void
  onMessage?: (message: WebSocketMessage) => void
}

export class WebSocketClient {
  private ws: WebSocket | null = null
  private url: string
  private options: Required<WebSocketOptions>
  private eventHandlers: Map<string, Set<WebSocketEventHandler>> = new Map()
  private reconnectTimer: number | null = null
  private heartbeatTimer: number | null = null
  private currentReconnectAttempts = 0
  private isManualClose = false

  constructor(options: WebSocketOptions = {}) {
    this.url = options.url || import.meta.env.VITE_WS_URL
    this.options = {
      url: this.url,
      reconnectAttempts: 5,
      reconnectInterval: 3000,
      heartbeatInterval: 30000,
      onOpen: () => {},
      onClose: () => {},
      onError: () => {},
      onMessage: () => {},
      ...options,
    }
  }

  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        this.ws = new WebSocket(this.url)

        this.ws.onopen = () => {
          // WebSocket connected
          this.currentReconnectAttempts = 0
          this.isManualClose = false
          this.startHeartbeat()
          this.options.onOpen()
          resolve()
        }

        this.ws.onclose = (event) => {
          // WebSocket disconnected
          this.stopHeartbeat()
          this.options.onClose(event)
          
          if (!this.isManualClose && this.shouldReconnect()) {
            this.scheduleReconnect()
          }
        }

        this.ws.onerror = (event) => {
          console.error('WebSocket error', event)
          this.options.onError(event)
          reject(new Error('WebSocket connection failed'))
        }

        this.ws.onmessage = (event) => {
          try {
            const message: WebSocketMessage = JSON.parse(event.data)
            this.handleMessage(message)
          } catch (error) {
            console.error('Failed to parse WebSocket message:', error)
          }
        }
      } catch (error) {
        reject(error)
      }
    })
  }

  disconnect(): void {
    this.isManualClose = true
    this.clearReconnectTimer()
    this.stopHeartbeat()
    
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
  }

  send(data: any): boolean {
    if (!this.isConnected()) {
      console.warn('WebSocket is not connected')
      return false
    }

    try {
      this.ws!.send(JSON.stringify(data))
      return true
    } catch (error) {
      console.error('Failed to send WebSocket message:', error)
      return false
    }
  }

  subscribe(eventType: string, handler: WebSocketEventHandler): () => void {
    if (!this.eventHandlers.has(eventType)) {
      this.eventHandlers.set(eventType, new Set())
    }
    
    this.eventHandlers.get(eventType)!.add(handler)

    // 返回取消订阅函数
    return () => {
      const handlers = this.eventHandlers.get(eventType)
      if (handlers) {
        handlers.delete(handler)
        if (handlers.size === 0) {
          this.eventHandlers.delete(eventType)
        }
      }
    }
  }

  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN
  }

  private handleMessage(message: WebSocketMessage): void {
    this.options.onMessage(message)

    // 触发特定类型的事件处理器
    const handlers = this.eventHandlers.get(message.type)
    if (handlers) {
      handlers.forEach(handler => {
        try {
          handler(message.data)
        } catch (error) {
          console.error('Error in WebSocket event handler:', error)
        }
      })
    }
  }

  private shouldReconnect(): boolean {
    return this.currentReconnectAttempts < this.options.reconnectAttempts
  }

  private scheduleReconnect(): void {
    if (this.reconnectTimer) {
      return
    }

    this.currentReconnectAttempts++
    // Scheduling reconnect attempt

    this.reconnectTimer = setTimeout(() => {
      this.reconnectTimer = null
      this.connect().catch(() => {
        // 连接失败，等待下次重试
      })
    }, this.options.reconnectInterval)
  }

  private clearReconnectTimer(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer)
      this.reconnectTimer = null
    }
  }

  private startHeartbeat(): void {
    this.stopHeartbeat()
    
    this.heartbeatTimer = setInterval(() => {
      if (this.isConnected()) {
        this.send({ type: 'ping', timestamp: Date.now() })
      }
    }, this.options.heartbeatInterval)
  }

  private stopHeartbeat(): void {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer)
      this.heartbeatTimer = null
    }
  }
}

// 创建全局 WebSocket 实例
let globalWebSocket: WebSocketClient | null = null

export const getWebSocket = (): WebSocketClient => {
  if (!globalWebSocket) {
    globalWebSocket = new WebSocketClient()
  }
  return globalWebSocket
}

// 股票价格更新相关的 WebSocket 工具
export const subscribeToStockPrices = (
  stockCodes: string[],
  handler: WebSocketEventHandler
): (() => void) => {
  const ws = getWebSocket()
  
  // 订阅价格更新事件
  const unsubscribe = ws.subscribe('price_update', handler)
  
  // 发送订阅请求
  if (ws.isConnected()) {
    ws.send({
      type: 'subscribe',
      data: { stockCodes }
    })
  }

  return () => {
    // 取消订阅
    unsubscribe()
    if (ws.isConnected()) {
      ws.send({
        type: 'unsubscribe',
        data: { stockCodes }
      })
    }
  }
}