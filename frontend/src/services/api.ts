import { get, post, put, del } from '@/utils/request'
import type {
  Stock,
  StockDetail,
  Company,
  PaginationParams,
  PaginatedResponse,
  TradingAdvice,
  TechnicalIndicator,
} from '@/types/api'

// 股票相关 API
export const stockApi = {
  // 获取股票列表
  getStockList: (params: PaginationParams & {
    search?: string
    industry?: string
    sortBy?: string
    sortOrder?: 'asc' | 'desc'
  }) => {
    return get<PaginatedResponse<Stock>>('/stocks', { params })
  },

  // 获取股票详情
  getStockDetail: (code: string) => {
    return get<StockDetail>(`/stocks/${code}`)
  },

  // 获取股票价格历史
  getStockPrices: (code: string, params: {
    startDate?: string
    endDate?: string
    interval?: '1m' | '5m' | '15m' | '1h' | '1d'
  }) => {
    return get(`/stocks/${code}/prices`, { params })
  },

  // 获取热门股票
  getHotStocks: (limit = 10) => {
    return get<Stock[]>('/stocks/hot', { params: { limit } })
  },

  // 搜索股票
  searchStocks: (keyword: string, limit = 20) => {
    return get<Stock[]>('/stocks/search', { 
      params: { keyword, limit } 
    })
  },
}

// 公司相关 API
export const companyApi = {
  // 获取公司列表
  getCompanyList: (params: PaginationParams & {
    search?: string
    industry?: string
    sector?: string
  }) => {
    return get<PaginatedResponse<Company>>('/companies', { params })
  },

  // 获取公司详情
  getCompanyDetail: (id: string) => {
    return get<Company>(`/companies/${id}`)
  },

  // 根据股票代码获取公司信息
  getCompanyByStock: (stockCode: string) => {
    return get<Company>(`/companies/by-stock/${stockCode}`)
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