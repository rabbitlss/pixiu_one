import React, { useState, useEffect } from 'react'
import { Card, Row, Col, Statistic, Progress, Space, Badge, Alert, Tooltip } from 'antd'
import { 
  ArrowUpOutlined, 
  ArrowDownOutlined, 
  FireOutlined,
  ThunderboltOutlined,
  TrophyOutlined,
  EyeOutlined
} from '@ant-design/icons'
import ReactEChartsCore from 'echarts-for-react/lib/core'
import * as echarts from 'echarts/core'
import { LineChart, BarChart } from 'echarts/charts'
import {
  GridComponent,
  TooltipComponent,
  LegendComponent,
  DataZoomComponent
} from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'

// 注册ECharts组件
echarts.use([
  LineChart,
  BarChart,
  GridComponent,
  TooltipComponent,
  LegendComponent,
  DataZoomComponent,
  CanvasRenderer
])

// 市场数据类型定义
interface MarketData {
  name: string
  current: number
  change: number
  changePercent: number
  volume: number
  turnover: number
}

interface HotStock {
  code: string
  name: string
  price: number
  changePercent: number
  volume: number
  reason: string
  heat: number
}

interface IndustryData {
  name: string
  changePercent: number
  leadingStock: string
  volume: number
  heat: number
}

// 模拟市场数据
const mockMarketData: MarketData[] = [
  {
    name: '上证指数',
    current: 3258.51,
    change: 15.67,
    changePercent: 0.48,
    volume: 2856420000,
    turnover: 328546.8
  },
  {
    name: '深证成指',
    current: 10486.75,
    change: -32.15,
    changePercent: -0.31,
    volume: 3564280000,
    turnover: 425632.4
  },
  {
    name: '创业板指',
    current: 2145.82,
    change: 8.96,
    changePercent: 0.42,
    volume: 1856420000,
    turnover: 285634.7
  },
  {
    name: '科创50',
    current: 1024.36,
    change: -5.23,
    changePercent: -0.51,
    volume: 956420000,
    turnover: 156789.3
  }
]

// 模拟热门股票
const mockHotStocks: HotStock[] = [
  {
    code: '300750',
    name: '宁德时代',
    price: 185.26,
    changePercent: 4.78,
    volume: 98456200,
    reason: '新能源政策利好',
    heat: 95
  },
  {
    code: '600519',
    name: '贵州茅台',
    price: 1678.50,
    changePercent: -0.90,
    volume: 8562400,
    reason: '机构调研密集',
    heat: 88
  },
  {
    code: '000001',
    name: '平安银行',
    price: 12.85,
    changePercent: 1.82,
    volume: 145632000,
    reason: '业绩超预期',
    heat: 82
  },
  {
    code: '002415',
    name: '海康威视',
    price: 32.45,
    changePercent: 4.01,
    volume: 76842000,
    reason: 'AI概念热炒',
    heat: 79
  }
]

// 模拟行业数据
const mockIndustryData: IndustryData[] = [
  {
    name: '新能源',
    changePercent: 3.85,
    leadingStock: '宁德时代',
    volume: 458562000,
    heat: 92
  },
  {
    name: '人工智能',
    changePercent: 2.67,
    leadingStock: '海康威视',
    volume: 325684000,
    heat: 85
  },
  {
    name: '医疗健康',
    changePercent: 1.45,
    leadingStock: '药明康德',
    volume: 215632000,
    heat: 78
  },
  {
    name: '半导体',
    changePercent: -1.23,
    leadingStock: '中芯国际',
    volume: 356421000,
    heat: 71
  },
  {
    name: '白酒',
    changePercent: -0.85,
    leadingStock: '贵州茅台',
    volume: 125863000,
    heat: 68
  }
]

const MarketOverview: React.FC = () => {
  const [currentTime, setCurrentTime] = useState(new Date())

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date())
    }, 1000)
    return () => clearInterval(timer)
  }, [])

  // 获取市场情绪
  const getMarketSentiment = () => {
    const upCount = mockMarketData.filter(item => item.changePercent > 0).length
    const totalCount = mockMarketData.length
    const ratio = upCount / totalCount

    if (ratio >= 0.75) return { text: '强势', color: '#ff4d4f', icon: <FireOutlined /> }
    if (ratio >= 0.5) return { text: '乐观', color: '#52c41a', icon: <ArrowUpOutlined /> }
    if (ratio >= 0.25) return { text: '谨慎', color: '#faad14', icon: <ThunderboltOutlined /> }
    return { text: '悲观', color: '#1890ff', icon: <ArrowDownOutlined /> }
  }

  const sentiment = getMarketSentiment()

  // 趋势图表配置
  const getTrendChartOption = () => {
    const times = Array.from({ length: 24 }, (_, i) => 
      `${String(9 + Math.floor(i / 4)).padStart(2, '0')}:${String((i % 4) * 15).padStart(2, '0')}`
    )
    const data = times.map(() => 3200 + Math.random() * 100 - 50)

    return {
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'cross' }
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '3%',
        containLabel: true
      },
      xAxis: {
        type: 'category',
        data: times.slice(-12),
        axisLabel: { fontSize: 10 }
      },
      yAxis: {
        type: 'value',
        scale: true,
        axisLabel: { fontSize: 10 }
      },
      series: [{
        name: '上证指数',
        type: 'line',
        data: data.slice(-12),
        smooth: true,
        lineStyle: { color: '#1890ff', width: 2 },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(24,144,255,0.3)' },
            { offset: 1, color: 'rgba(24,144,255,0.1)' }
          ])
        }
      }]
    }
  }

  // 行业热度图表配置
  const getIndustryChartOption = () => {
    return {
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'shadow' }
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '3%',
        top: '3%',
        containLabel: true
      },
      xAxis: {
        type: 'value',
        axisLabel: { fontSize: 10 }
      },
      yAxis: {
        type: 'category',
        data: mockIndustryData.map(item => item.name),
        axisLabel: { fontSize: 10 }
      },
      series: [{
        name: '涨跌幅',
        type: 'bar',
        data: mockIndustryData.map(item => ({
          value: item.changePercent,
          itemStyle: {
            color: item.changePercent >= 0 ? '#ff4d4f' : '#52c41a'
          }
        })),
        barWidth: '60%'
      }]
    }
  }

  return (
    <div>
      {/* 市场状态栏 */}
      <Alert
        message={
          <Space>
            <span>市场时间: {currentTime.toLocaleTimeString()}</span>
            <span>|</span>
            <span>市场情绪: </span>
            <Space size={4}>
              {sentiment.icon}
              <span style={{ color: sentiment.color, fontWeight: 'bold' }}>
                {sentiment.text}
              </span>
            </Space>
          </Space>
        }
        type="info"
        showIcon={false}
        style={{ marginBottom: 16 }}
      />

      {/* 主要指数 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
        {mockMarketData.map((market) => (
          <Col key={market.name} xs={12} sm={6}>
            <Card size="small">
              <Statistic
                title={market.name}
                value={market.current}
                precision={2}
                valueStyle={{
                  color: market.changePercent >= 0 ? '#ff4d4f' : '#52c41a',
                  fontSize: '18px'
                }}
                prefix={
                  market.changePercent >= 0 ? (
                    <ArrowUpOutlined />
                  ) : (
                    <ArrowDownOutlined />
                  )
                }
                suffix={
                  <Space direction="vertical" size={0}>
                    <span style={{ 
                      fontSize: '12px',
                      color: market.changePercent >= 0 ? '#ff4d4f' : '#52c41a'
                    }}>
                      {market.changePercent >= 0 ? '+' : ''}{market.changePercent.toFixed(2)}%
                    </span>
                    <span style={{ fontSize: '10px', color: '#666' }}>
                      成交: {(market.volume / 100000000).toFixed(0)}亿
                    </span>
                  </Space>
                }
              />
            </Card>
          </Col>
        ))}
      </Row>

      <Row gutter={[16, 16]}>
        {/* 市场趋势 */}
        <Col xs={24} lg={12}>
          <Card title="市场走势" size="small" extra={<Badge status="processing" text="实时" />}>
            <ReactEChartsCore
              echarts={echarts}
              option={getTrendChartOption()}
              style={{ height: '250px' }}
            />
          </Card>
        </Col>

        {/* 行业热度 */}
        <Col xs={24} lg={12}>
          <Card title="行业表现" size="small">
            <ReactEChartsCore
              echarts={echarts}
              option={getIndustryChartOption()}
              style={{ height: '250px' }}
            />
          </Card>
        </Col>

        {/* 热门股票 */}
        <Col xs={24} lg={12}>
          <Card title="热门关注" size="small" extra={<FireOutlined style={{ color: '#ff4d4f' }} />}>
            <Space direction="vertical" size={8} style={{ width: '100%' }}>
              {mockHotStocks.map((stock, index) => (
                <div key={stock.code} style={{
                  padding: '8px 12px',
                  border: '1px solid #f0f0f0',
                  borderRadius: '6px',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center'
                }}>
                  <Space>
                    <Badge 
                      count={index + 1} 
                      style={{ 
                        backgroundColor: index < 3 ? '#faad14' : '#d9d9d9',
                        color: index < 3 ? '#fff' : '#666'
                      }} 
                    />
                    <Space direction="vertical" size={0}>
                      <span style={{ fontWeight: 'bold' }}>{stock.name}</span>
                      <span style={{ fontSize: '12px', color: '#666' }}>
                        {stock.reason}
                      </span>
                    </Space>
                  </Space>
                  <Space direction="vertical" size={0} style={{ textAlign: 'right' }}>
                    <span style={{
                      color: stock.changePercent >= 0 ? '#ff4d4f' : '#52c41a',
                      fontWeight: 'bold'
                    }}>
                      {stock.changePercent >= 0 ? '+' : ''}{stock.changePercent.toFixed(2)}%
                    </span>
                    <Tooltip title={`热度: ${stock.heat}`}>
                      <Progress 
                        percent={stock.heat} 
                        size="small" 
                        showInfo={false}
                        strokeColor="#ff4d4f"
                        style={{ width: 60 }}
                      />
                    </Tooltip>
                  </Space>
                </div>
              ))}
            </Space>
          </Card>
        </Col>

        {/* 行业轮动 */}
        <Col xs={24} lg={12}>
          <Card title="行业轮动" size="small" extra={<TrophyOutlined style={{ color: '#52c41a' }} />}>
            <Space direction="vertical" size={8} style={{ width: '100%' }}>
              {mockIndustryData.map((industry) => (
                <div key={industry.name} style={{
                  padding: '8px 12px',
                  border: '1px solid #f0f0f0',
                  borderRadius: '6px',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center'
                }}>
                  <Space>
                    <span style={{ 
                      color: industry.changePercent >= 0 ? '#ff4d4f' : '#52c41a',
                      fontSize: '18px'
                    }}>
                      {industry.changePercent >= 0 ? <ArrowUpOutlined /> : <ArrowDownOutlined />}
                    </span>
                    <Space direction="vertical" size={0}>
                      <span style={{ fontWeight: 'bold' }}>{industry.name}</span>
                      <span style={{ fontSize: '12px', color: '#666' }}>
                        龙头: {industry.leadingStock}
                      </span>
                    </Space>
                  </Space>
                  <Space direction="vertical" size={0} style={{ textAlign: 'right' }}>
                    <span style={{
                      color: industry.changePercent >= 0 ? '#ff4d4f' : '#52c41a',
                      fontWeight: 'bold'
                    }}>
                      {industry.changePercent >= 0 ? '+' : ''}{industry.changePercent.toFixed(2)}%
                    </span>
                    <Space size={4}>
                      <EyeOutlined style={{ fontSize: '12px', color: '#999' }} />
                      <span style={{ fontSize: '12px', color: '#999' }}>
                        {industry.heat}
                      </span>
                    </Space>
                  </Space>
                </div>
              ))}
            </Space>
          </Card>
        </Col>
      </Row>
    </div>
  )
}

export default MarketOverview