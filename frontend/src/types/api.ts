// 通用响应类型
export interface ApiResponse<T = any> {
  success: boolean
  data: T
  message?: string
  code?: string | number
}

// 分页参数
export interface PaginationParams {
  page: number
  pageSize: number
}

// 分页响应
export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  pageSize: number
  totalPages: number
}

// 股票相关类型
export interface Stock {
  id: string
  code: string
  name: string
  currentPrice: number
  changeAmount: number
  changePercent: number
  volume: number
  marketCap: number
  pe?: number
  pb?: number
  updatedAt: string
}

export interface StockPrice {
  timestamp: string
  open: number
  high: number
  low: number
  close: number
  volume: number
}

export interface StockDetail extends Stock {
  description?: string
  industry?: string
  sector?: string
  employees?: number
  website?: string
  prices: StockPrice[]
  technicalIndicators?: {
    ma5: number
    ma10: number
    ma20: number
    rsi: number
    macd: number
  }
}

// 公司相关类型
export interface Company {
  id: string
  stockCode: string
  name: string
  industry: string
  sector: string
  description: string
  employees: number
  website: string
  marketCap: number
  pe: number
  pb: number
  roe: number
  createdAt: string
  updatedAt: string
}

// 分析相关类型
export interface TechnicalIndicator {
  name: string
  value: number
  signal: 'buy' | 'sell' | 'hold'
  description: string
}

export interface TradingAdvice {
  id: string
  stockCode: string
  type: 'buy' | 'sell' | 'hold'
  confidence: number
  reason: string
  targetPrice?: number
  stopLoss?: number
  createdAt: string
}

// WebSocket 消息类型
export interface WebSocketMessage {
  type: 'price_update' | 'market_status' | 'trading_advice'
  data: any
  timestamp: string
}

// 错误类型
export interface ApiError {
  message: string
  code?: string | number
  details?: any
}