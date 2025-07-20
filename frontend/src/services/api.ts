import { get, post, put, del } from '@/utils/request'
import type {
  Stock,
  StockDetail,
  Company,
  TradingAdvice,
  TechnicalIndicator,
  AuthResponse,
  LoginRequest,
  RegisterRequest,
} from '@/types/api'

// 认证相关 API
export const authApi = {
  // 用户登录
  login: (data: LoginRequest) => {
    return post<AuthResponse>('/api/v1/auth/login', data)
  },

  // 用户注册
  register: (data: RegisterRequest) => {
    return post<AuthResponse>('/api/v1/auth/register', data)
  },

  // 刷新token
  refreshToken: () => {
    return post<AuthResponse>('/api/v1/auth/refresh')
  },

  // 退出登录
  logout: () => {
    return post('/api/v1/auth/logout')
  },

  // 修改密码
  changePassword: (data: { current_password: string; new_password: string }) => {
    return post('/api/v1/auth/change-password', data)
  },
}

// 股票相关 API
export const stockApi = {
  // 获取股票列表
  getStockList: (params?: {
    skip?: number
    limit?: number
    search?: string
  }) => {
    return get<{ items: Stock[], total: number, skip: number, limit: number }>('/api/v1/stocks/', { params })
  },

  // 获取股票详情
  getStockDetail: (stockId: string) => {
    return get<StockDetail>(`/api/v1/stocks/${stockId}`)
  },

  // 获取股票价格历史
  getStockPrices: (stockId: string, params?: {
    start_date?: string
    end_date?: string
    limit?: number
  }) => {
    return get(`/api/v1/stocks/${stockId}/prices`, { params })
  },

  // 获取股票技术指标
  getStockIndicators: (stockId: string) => {
    return get<TechnicalIndicator[]>(`/api/v1/stocks/${stockId}/indicators`)
  },

  // 批量获取股票价格
  getStockPricesBulk: (stockId: string, data: any) => {
    return post(`/api/v1/stocks/${stockId}/prices/bulk`, data)
  },
}

// 公司相关 API
export const companyApi = {
  // 获取公司列表
  getCompanyList: (params: {
    skip?: number
    limit?: number
    search?: string
    industry?: string
    sector?: string
    country?: string
    min_market_cap?: number
    max_market_cap?: number
  }) => {
    return get<{
      items: Company[]
      total: number
      page: number
      size: number
      pages: number
    }>('/api/v1/companies/', { params })
  },

  // 获取公司详情
  getCompanyDetail: (id: string) => {
    return get<Company>(`/api/v1/companies/${id}`)
  },

  // 根据股票代码获取公司信息
  getCompanyByStock: (stockCode: string) => {
    return get<Company>(`/api/v1/companies/by-stock/${stockCode}`)
  },
}

// 分析相关 API
export const analysisApi = {
  // 获取技术指标
  getTechnicalIndicators: (stockCode: string) => {
    return get<TechnicalIndicator[]>(`/analysis/technical/${stockCode}`)
  },

  // 获取交易建议
  getTradingAdvice: (stockCode: string) => {
    return get<TradingAdvice[]>(`/analysis/advice/${stockCode}`)
  },

  // 获取市场概览
  getMarketOverview: () => {
    return get('/analysis/market-overview')
  },

  // 获取行业分析
  getIndustryAnalysis: (industry?: string) => {
    return get('/analysis/industry', { params: { industry } })
  },
}

// 用户相关 API
export const userApi = {
  // 获取用户信息
  getUserInfo: () => {
    return get('/user/profile')
  },

  // 更新用户信息
  updateUserInfo: (data: any) => {
    return put('/user/profile', data)
  },

  // 获取用户偏好
  getUserPreferences: () => {
    return get('/user/preferences')
  },

  // 更新用户偏好
  updateUserPreferences: (data: any) => {
    return put('/user/preferences', data)
  },

  // 获取关注的股票
  getWatchlist: () => {
    return get<Stock[]>('/user/watchlist')
  },

  // 添加股票到关注列表
  addToWatchlist: (stockCode: string) => {
    return post('/user/watchlist', { stockCode })
  },

  // 从关注列表移除股票
  removeFromWatchlist: (stockCode: string) => {
    return del(`/user/watchlist/${stockCode}`)
  },
}

// 系统相关 API
export const systemApi = {
  // 获取系统状态
  getSystemStatus: () => {
    return get('/system/status')
  },

  // 获取系统配置
  getSystemConfig: () => {
    return get('/system/config')
  },

  // 更新系统配置
  updateSystemConfig: (data: any) => {
    return put('/system/config', data)
  },

  // 获取数据统计
  getDataStatistics: () => {
    return get('/system/statistics')
  },
}