import React, { useState, useEffect } from 'react'
import { 
  Typography, 
  Card, 
  Row, 
  Col, 
  Statistic, 
  Table, 
  Tag, 
  Space, 
  Button, 
  message,
  Spin,
  Alert,
  Progress
} from 'antd'
import { 
  ReloadOutlined, 
  TrophyOutlined, 
  RiseOutlined, 
  FallOutlined,
  DatabaseOutlined,
  ApiOutlined
} from '@ant-design/icons'
import { stockApi } from '@/services/api'
import type { Stock } from '@/types/api'
import type { ColumnsType } from 'antd/es/table'

const { Title, Text } = Typography

interface StockWithPrices extends Stock {
  latest_price?: {
    date: string
    open: number
    high: number
    low: number
    close: number
    volume: number
  }
  price_change?: number
  price_change_percent?: number
  prices?: any[]
}

const AlphaVantageData: React.FC = () => {
  const [stocks, setStocks] = useState<StockWithPrices[]>([])
  const [loading, setLoading] = useState(true)
  const [stats, setStats] = useState({
    totalStocks: 0,
    totalRecords: 0,
    totalVolume: 0,
    avgChange: 0
  })

  const fetchAlphaVantageData = async () => {
    setLoading(true)
    try {
      // 获取股票列表
      const response = await stockApi.getStockList({ limit: 100 })
      
      if (response && (response as any).items) {
        const stocksWithPrices: StockWithPrices[] = []
        let totalRecords = 0
        let totalVolume = 0
        let totalChange = 0
        let changeCount = 0

        // 为每只股票获取详细价格数据
        for (const stock of (response as any).items) {
          try {
            const detailResponse = await stockApi.getStockDetail(stock.id.toString())
            if (detailResponse) {
              const stockWithPrice = { ...stock, ...detailResponse }
              
              // 获取价格历史
              const pricesResponse = await stockApi.getStockPrices(stock.id.toString(), { limit: 20 })
              if (pricesResponse && Array.isArray(pricesResponse)) {
                stockWithPrice.prices = pricesResponse
                totalRecords += pricesResponse.length

                // 计算价格变化
                if (pricesResponse.length >= 2) {
                  const latest = pricesResponse[0]
                  const previous = pricesResponse[1]
                  stockWithPrice.price_change = latest.close - previous.close
                  stockWithPrice.price_change_percent = (stockWithPrice.price_change / previous.close) * 100
                  
                  totalChange += stockWithPrice.price_change_percent
                  changeCount++
                }

                // 计算总交易量
                if (stockWithPrice.latest_price) {
                  totalVolume += stockWithPrice.latest_price.volume || 0
                }
              }
              
              stocksWithPrices.push(stockWithPrice)
            }
          } catch (error) {
            // 获取股票数据失败: error
          }
        }

        setStocks(stocksWithPrices)
        setStats({
          totalStocks: stocksWithPrices.length,
          totalRecords,
          totalVolume,
          avgChange: changeCount > 0 ? totalChange / changeCount : 0
        })
      }
    } catch (error: any) {
      message.error(error.message || '获取Alpha Vantage数据失败')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchAlphaVantageData()
  }, [])

  const formatNumber = (num: number) => {
    if (num >= 1000000000) {
      return (num / 1000000000).toFixed(1) + 'B'
    } else if (num >= 1000000) {
      return (num / 1000000).toFixed(1) + 'M'
    } else if (num >= 1000) {
      return (num / 1000).toFixed(1) + 'K'
    }
    return num.toLocaleString()
  }

  const formatPrice = (price: number) => {
    return `$${price.toFixed(2)}`
  }

  const formatChange = (change: number, percent: number) => {
    const isPositive = change >= 0
    const color = isPositive ? '#52c41a' : '#ff4d4f'
    const icon = isPositive ? <RiseOutlined /> : <FallOutlined />
    const sign = isPositive ? '+' : ''
    
    return (
      <Space style={{ color }}>
        {icon}
        <span>{sign}{formatPrice(change)}</span>
        <span>({sign}{percent.toFixed(2)}%)</span>
      </Space>
    )
  }

  const getSectorColor = (sector: string) => {
    const colors: Record<string, string> = {
      'Technology': 'blue',
      'Consumer Cyclical': 'green',
      'Healthcare': 'red',
      'Financial Services': 'orange',
      'Communication Services': 'purple',
      'Consumer Defensive': 'cyan',
      'Industrials': 'magenta',
      'Energy': 'volcano',
      'Utilities': 'geekblue',
      'Real Estate': 'gold',
      'Basic Materials': 'lime'
    }
    return colors[sector] || 'default'
  }

  const columns: ColumnsType<StockWithPrices> = [
    {
      title: '股票信息',
      key: 'stock_info',
      width: 200,
      render: (_, record) => (
        <div>
          <div style={{ fontWeight: 'bold', fontSize: '16px', color: '#1890ff' }}>
            {record.symbol}
          </div>
          <div style={{ fontSize: '12px', color: '#666', marginTop: '2px' }}>
            {record.name}
          </div>
          <div style={{ marginTop: '4px' }}>
            <Tag color="processing">{record.exchange}</Tag>
            <Tag color={getSectorColor(record.sector)}>{record.sector}</Tag>
          </div>
        </div>
      ),
    },
    {
      title: '最新价格',
      key: 'latest_price',
      width: 120,
      sorter: (a, b) => (a.latest_price?.close || 0) - (b.latest_price?.close || 0),
      render: (_, record) => (
        <div style={{ textAlign: 'right' }}>
          <div style={{ fontSize: '18px', fontWeight: 'bold', color: '#262626' }}>
            {record.latest_price ? formatPrice(record.latest_price.close) : 'N/A'}
          </div>
          <div style={{ fontSize: '12px', color: '#666' }}>
            {record.latest_price ? new Date(record.latest_price.date).toLocaleDateString('zh-CN') : ''}
          </div>
        </div>
      ),
    },
    {
      title: '涨跌幅',
      key: 'change',
      width: 150,
      sorter: (a, b) => (a.price_change_percent || 0) - (b.price_change_percent || 0),
      render: (_, record) => (
        <div style={{ textAlign: 'right' }}>
          {record.price_change !== undefined && record.price_change_percent !== undefined ? 
            formatChange(record.price_change, record.price_change_percent) : 
            <Text type="secondary">无数据</Text>
          }
        </div>
      ),
    },
    {
      title: '当日成交量',
      key: 'volume',
      width: 120,
      sorter: (a, b) => (a.latest_price?.volume || 0) - (b.latest_price?.volume || 0),
      render: (_, record) => (
        <div style={{ textAlign: 'right' }}>
          <div style={{ fontWeight: 'bold' }}>
            {record.latest_price ? formatNumber(record.latest_price.volume) : 'N/A'}
          </div>
        </div>
      ),
    },
    {
      title: '当日范围',
      key: 'day_range',
      width: 150,
      render: (_, record) => (
        <div>
          {record.latest_price ? (
            <div>
              <div style={{ fontSize: '12px', color: '#666' }}>
                最低: {formatPrice(record.latest_price.low)}
              </div>
              <div style={{ fontSize: '12px', color: '#666' }}>
                最高: {formatPrice(record.latest_price.high)}
              </div>
              <Progress 
                percent={((record.latest_price.close - record.latest_price.low) / 
                         (record.latest_price.high - record.latest_price.low)) * 100}
                size="small"
                showInfo={false}
                strokeColor="#1890ff"
              />
            </div>
          ) : (
            <Text type="secondary">无数据</Text>
          )}
        </div>
      ),
    },
    {
      title: 'Alpha Vantage 数据记录',
      key: 'data_records',
      width: 120,
      render: (_, record) => (
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: '16px', fontWeight: 'bold', color: '#52c41a' }}>
            {record.prices ? record.prices.length : 0}
          </div>
          <div style={{ fontSize: '12px', color: '#666' }}>条记录</div>
        </div>
      ),
    },
  ]

  return (
    <div>
      <div style={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center',
        marginBottom: 24 
      }}>
        <div>
          <Title level={2} style={{ margin: 0, display: 'flex', alignItems: 'center' }}>
            <ApiOutlined style={{ marginRight: 8, color: '#1890ff' }} />
            Alpha Vantage 真实数据展示
          </Title>
          <Text type="secondary">来自 Alpha Vantage API 的真实股票市场数据</Text>
        </div>
        <Button 
          type="primary"
          icon={<ReloadOutlined />} 
          onClick={fetchAlphaVantageData}
          loading={loading}
          size="large"
        >
          刷新数据
        </Button>
      </div>

      <Alert
        message="数据源信息"
        description={
          <div>
            <Text strong>API 提供商:</Text> Alpha Vantage Financial APIs &nbsp;|&nbsp;
            <Text strong>API Key:</Text> FS08JV...BUGZ &nbsp;|&nbsp;
            <Text strong>数据更新:</Text> 实时获取最新交易数据 &nbsp;|&nbsp;
            <Text strong>覆盖范围:</Text> 2025年6-7月真实交易记录
          </div>
        }
        type="info"
        showIcon
        style={{ marginBottom: 24 }}
      />

      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="活跃股票数量"
              value={stats.totalStocks}
              prefix={<DatabaseOutlined style={{ color: '#1890ff' }} />}
              suffix="只"
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="数据记录总数"
              value={stats.totalRecords}
              prefix={<TrophyOutlined style={{ color: '#52c41a' }} />}
              suffix="条"
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="总成交量"
              value={formatNumber(stats.totalVolume)}
              prefix={<RiseOutlined style={{ color: '#fa8c16' }} />}
              valueStyle={{ color: '#fa8c16' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="平均涨跌幅"
              value={stats.avgChange}
              precision={2}
              suffix="%"
              prefix={stats.avgChange >= 0 ? <RiseOutlined /> : <FallOutlined />}
              valueStyle={{ color: stats.avgChange >= 0 ? '#52c41a' : '#ff4d4f' }}
            />
          </Card>
        </Col>
      </Row>

      <Card 
        title={
          <div style={{ display: 'flex', alignItems: 'center' }}>
            <DatabaseOutlined style={{ marginRight: 8 }} />
            实时股票数据详情
            <Tag color="green" style={{ marginLeft: 8 }}>Alpha Vantage API</Tag>
          </div>
        }
      >
        <Spin spinning={loading}>
          <Table
            columns={columns}
            dataSource={stocks}
            rowKey="id"
            pagination={{
              total: stocks.length,
              pageSize: 10,
              showSizeChanger: true,
              showQuickJumper: true,
              showTotal: (total, range) => 
                `第 ${range[0]}-${range[1]} 条/共 ${total} 条 Alpha Vantage 数据记录`,
            }}
            scroll={{ x: 1200 }}
            rowClassName={(record) => 
              record.price_change_percent && record.price_change_percent > 0 ? 'positive-row' : 
              record.price_change_percent && record.price_change_percent < 0 ? 'negative-row' : ''
            }
          />
        </Spin>
      </Card>

      <style>{`
        .positive-row {
          background-color: rgba(82, 196, 26, 0.05) !important;
        }
        .negative-row {
          background-color: rgba(255, 77, 79, 0.05) !important;
        }
      `}</style>
    </div>
  )
}

export default AlphaVantageData