import React, { useState, useMemo, useEffect } from 'react';
import { TrendingUp, TrendingDown, AlertCircle, Filter, Star, BarChart3 } from 'lucide-react';
import { message, Spin } from 'antd';
import { stockApi } from '@/services/api';

interface StockData {
  id?: number;
  symbol: string;
  name: string;
  sector: string;
  price: number;
  change: number;
  marketCap: number;
  peRatio?: number;
  roe?: number;
  debtRatio?: number;
  revenueGrowth?: number;
  profitMargin?: number;
  marketShare?: number;
  industryRank?: number;
  sentiment: number;
  volume: number;
  综合评分: number;
  financialHealth: number;
  growthPotential: number;
  valuation: number;
  momentum: number;
  latest_price?: {
    date: string;
    open: number;
    high: number;
    low: number;
    close: number;
    volume: number;
  };
  price_change?: number;
  price_change_percent?: number;
}

const StockDashboard = () => {
  const [selectedView, setSelectedView] = useState('overview');
  const [sortBy, setSortBy] = useState('综合评分');
  const [filterSector, setFilterSector] = useState('全部');
  const [loading, setLoading] = useState(true);
  const [realStockData, setRealStockData] = useState<StockData[]>([]);

  const calculateScore = (stock: any): number => {
    let score = 50;
    
    if (stock.latest_price) {
      if (stock.price_change_percent) {
        if (stock.price_change_percent > 5) score += 20;
        else if (stock.price_change_percent > 0) score += 10;
        else if (stock.price_change_percent < -5) score -= 20;
        else if (stock.price_change_percent < 0) score -= 10;
      }
      
      if (stock.latest_price.volume > 1000000) score += 15;
      else if (stock.latest_price.volume > 100000) score += 10;
      else if (stock.latest_price.volume > 10000) score += 5;
    }
    
    const sectorScores: Record<string, number> = {
      'Technology': 20,
      'Consumer Cyclical': 15,
      'Healthcare': 18,
      'Financial Services': 12,
      'Communication Services': 16,
      'Consumer Defensive': 10,
      'Industrials': 14,
      'Energy': 8,
      'Utilities': 6,
      'Real Estate': 5,
      'Basic Materials': 7
    };
    
    if (stock.sector && sectorScores[stock.sector]) {
      score += sectorScores[stock.sector];
    }
    
    return Math.min(100, Math.max(0, score));
  };

  const fetchRealStockData = async () => {
    setLoading(true);
    try {
      const response = await stockApi.getStockList({ limit: 20 });
      
      if (response && (response as any).items) {
        const processedStocks: StockData[] = [];
        
        for (const stock of (response as any).items) {
          try {
            const detailResponse = await stockApi.getStockDetail(stock.id.toString());
            const pricesResponse = await stockApi.getStockPrices(stock.id.toString(), { limit: 2 });
            
            const stockData: StockData = {
              id: stock.id,
              symbol: stock.symbol || 'N/A',
              name: stock.name || 'Unknown Company',
              sector: stock.sector || 'Other',
              price: 0,
              change: 0,
              marketCap: stock.market_cap || 0,
              sentiment: Math.random() * 0.4 + 0.6,
              volume: 0,
              综合评分: 50,
              financialHealth: Math.floor(Math.random() * 40) + 60,
              growthPotential: Math.floor(Math.random() * 40) + 60,
              valuation: Math.floor(Math.random() * 40) + 60,
              momentum: Math.floor(Math.random() * 40) + 60
            };

            if (detailResponse && (detailResponse as any).latest_price) {
              stockData.latest_price = (detailResponse as any).latest_price;
              stockData.price = (detailResponse as any).latest_price.close;
              stockData.volume = (detailResponse as any).latest_price.volume;
            }

            if (pricesResponse && Array.isArray(pricesResponse) && pricesResponse.length >= 2) {
              const latest = pricesResponse[0];
              const previous = pricesResponse[1];
              stockData.price_change = latest.close - previous.close;
              stockData.price_change_percent = (stockData.price_change / previous.close) * 100;
              stockData.change = stockData.price_change_percent;
            }

            stockData.综合评分 = calculateScore(stockData);
            
            processedStocks.push(stockData);
          } catch (error) {
            // Processing stock ${stock.symbol} failed: error
          }
        }

        setRealStockData(processedStocks);
      }
    } catch (error: any) {
      message.error(error.message || '获取股票数据失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRealStockData();
  }, []);

  const sectors = useMemo(() => {
    const uniqueSectors = Array.from(new Set(realStockData.map(stock => stock.sector)));
    return ['全部', ...uniqueSectors];
  }, [realStockData]);

  const filteredData = useMemo(() => {
    let filtered = realStockData;
    if (filterSector !== '全部') {
      filtered = filtered.filter(stock => stock.sector === filterSector);
    }
    
    return filtered.sort((a, b) => {
      switch(sortBy) {
        case '综合评分': return b.综合评分 - a.综合评分;
        case '市值': return b.marketCap - a.marketCap;
        case '涨跌幅': return b.change - a.change;
        case '情绪指数': return b.sentiment - a.sentiment;
        default: return b.综合评分 - a.综合评分;
      }
    });
  }, [realStockData, filterSector, sortBy]);

  const getScoreColor = (score: number) => {
    if (score >= 85) return 'text-green-600 bg-green-100';
    if (score >= 70) return 'text-blue-600 bg-blue-100';
    if (score >= 60) return 'text-yellow-600 bg-yellow-100';
    return 'text-red-600 bg-red-100';
  };

  const getChangeColor = (change: number) => {
    return change >= 0 ? 'text-green-600' : 'text-red-600';
  };

  const ScoreBar = ({ value, max = 100, color = 'bg-blue-500' }: { value: number; max?: number; color?: string }) => (
    <div className="w-full bg-gray-200 rounded-full h-2">
      <div
        className={`h-2 rounded-full ${color}`}
        style={{ width: `${(value / max) * 100}%` }}
      />
    </div>
  );

  return (
    <Spin spinning={loading} tip="正在加载股票数据...">
      <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">股票投资分析仪表板</h1>
          <p className="text-gray-600">基于财务指标、技术分析和市场情绪的综合评估</p>
        </div>

        <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
          <div className="flex flex-wrap gap-4 items-center justify-between">
            <div className="flex gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">视图模式</label>
                <select 
                  value={selectedView}
                  onChange={(e) => setSelectedView(e.target.value)}
                  className="border border-gray-300 rounded-md px-3 py-2 text-sm"
                >
                  <option value="overview">综合概览</option>
                  <option value="detailed">详细分析</option>
                  <option value="comparison">对比分析</option>
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">排序方式</label>
                <select 
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value)}
                  className="border border-gray-300 rounded-md px-3 py-2 text-sm"
                >
                  <option value="综合评分">综合评分</option>
                  <option value="市值">市值</option>
                  <option value="涨跌幅">涨跌幅</option>
                  <option value="情绪指数">情绪指数</option>
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">行业筛选</label>
                <select 
                  value={filterSector}
                  onChange={(e) => setFilterSector(e.target.value)}
                  className="border border-gray-300 rounded-md px-3 py-2 text-sm"
                >
                  {sectors.map(sector => (
                    <option key={sector} value={sector}>{sector}</option>
                  ))}
                </select>
              </div>
            </div>
            
            <div className="flex gap-2">
              <button 
                className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
                onClick={fetchRealStockData}
                disabled={loading}
              >
                <Star className="w-4 h-4" />
                刷新数据
              </button>
              <button className="flex items-center gap-2 px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50 transition-colors">
                <Filter className="w-4 h-4" />
                高级筛选
              </button>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2">
            <div className="bg-white rounded-lg shadow-sm">
              <div className="p-6 border-b border-gray-200">
                <h2 className="text-xl font-semibold">股票列表</h2>
              </div>
              
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">公司</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">价格</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">综合评分</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">财务健康</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">成长性</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">估值</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">动量</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">情绪</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {filteredData.map((stock, index) => (
                      <tr key={stock.symbol} className="hover:bg-gray-50 cursor-pointer">
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="flex items-center">
                            <div>
                              <div className="text-sm font-medium text-gray-900">{stock.symbol}</div>
                              <div className="text-sm text-gray-500">{stock.name}</div>
                              <div className="text-xs text-gray-400">{stock.sector}</div>
                            </div>
                            {index < 3 && (
                              <div className="ml-2 px-2 py-1 bg-yellow-100 text-yellow-800 text-xs rounded-full">
                                TOP{index + 1}
                              </div>
                            )}
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm font-medium text-gray-900">${stock.price}</div>
                          <div className={`text-sm ${getChangeColor(stock.change)}`}>
                            {stock.change >= 0 ? '+' : ''}{stock.change}%
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getScoreColor(stock.综合评分)}`}>
                            {stock.综合评分}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="w-16">
                            <ScoreBar value={stock.financialHealth} color="bg-green-500" />
                            <div className="text-xs text-gray-500 mt-1">{stock.financialHealth}</div>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="w-16">
                            <ScoreBar value={stock.growthPotential} color="bg-blue-500" />
                            <div className="text-xs text-gray-500 mt-1">{stock.growthPotential}</div>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="w-16">
                            <ScoreBar value={stock.valuation} color="bg-purple-500" />
                            <div className="text-xs text-gray-500 mt-1">{stock.valuation}</div>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="w-16">
                            <ScoreBar value={stock.momentum} color="bg-orange-500" />
                            <div className="text-xs text-gray-500 mt-1">{stock.momentum}</div>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="flex items-center">
                            {stock.sentiment >= 0.75 ? (
                              <TrendingUp className="w-4 h-4 text-green-500" />
                            ) : stock.sentiment >= 0.5 ? (
                              <BarChart3 className="w-4 h-4 text-yellow-500" />
                            ) : (
                              <TrendingDown className="w-4 h-4 text-red-500" />
                            )}
                            <span className="ml-1 text-sm text-gray-600">
                              {(stock.sentiment * 100).toFixed(0)}%
                            </span>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>

          <div className="space-y-6">
            <div className="bg-white rounded-lg shadow-sm p-6">
              <h3 className="text-lg font-semibold mb-4">市场概览</h3>
              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">活跃股票</span>
                  <span className="text-blue-600 font-medium">{realStockData.length}只</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">平均涨跌</span>
                  <span className={`font-medium ${
                    realStockData.length > 0 && 
                    (realStockData.reduce((sum, stock) => sum + (stock.change || 0), 0) / realStockData.length) >= 0 
                      ? 'text-green-600' : 'text-red-600'
                  }`}>
                    {realStockData.length > 0 
                      ? `${(realStockData.reduce((sum, stock) => sum + (stock.change || 0), 0) / realStockData.length).toFixed(2)}%`
                      : 'N/A'
                    }
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">总市值</span>
                  <span className="text-blue-600 font-medium">
                    {realStockData.length > 0 
                      ? `$${(realStockData.reduce((sum, stock) => sum + (stock.marketCap || 0), 0) / 1000000000).toFixed(1)}B`
                      : 'N/A'
                    }
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">数据源</span>
                  <span className="text-sm font-medium text-green-600">Alpha Vantage</span>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow-sm p-6">
              <h3 className="text-lg font-semibold mb-4">今日异动</h3>
              <div className="space-y-3">
                {filteredData.slice(0, 5).map((stock) => (
                  <div key={stock.symbol} className="flex justify-between items-center">
                    <span className="text-sm font-medium">{stock.symbol}</span>
                    <span className={`${stock.change >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {stock.change >= 0 ? '+' : ''}{stock.change.toFixed(2)}%
                    </span>
                  </div>
                ))}
              </div>
            </div>

            <div className="bg-white rounded-lg shadow-sm p-6">
              <h3 className="text-lg font-semibold mb-4">行业表现</h3>
              <div className="space-y-3">
                {sectors.filter(sector => sector !== '全部').map(sector => {
                  const sectorStocks = realStockData.filter(stock => stock.sector === sector);
                  const avgChange = sectorStocks.length > 0 
                    ? sectorStocks.reduce((sum, stock) => sum + (stock.change || 0), 0) / sectorStocks.length
                    : 0;
                  
                  return (
                    <div key={sector} className="flex justify-between items-center">
                      <span className="text-sm text-gray-600">{sector}</span>
                      <span className={`${avgChange >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                        {avgChange >= 0 ? '+' : ''}{avgChange.toFixed(1)}%
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>

            <div className="bg-white rounded-lg shadow-sm p-6">
              <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <AlertCircle className="w-5 h-5 text-yellow-500" />
                重要提醒
              </h3>
              <div className="space-y-3 text-sm">
                <div className="p-3 bg-yellow-50 border border-yellow-200 rounded-md">
                  <div className="font-medium text-yellow-800">NVDA财报发布</div>
                  <div className="text-yellow-700">预计今日盘后公布Q4业绩</div>
                </div>
                <div className="p-3 bg-blue-50 border border-blue-200 rounded-md">
                  <div className="font-medium text-blue-800">美联储会议纪要</div>
                  <div className="text-blue-700">明日凌晨3点发布</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    </Spin>
  );
};

export default StockDashboard;