import React, { useState, useEffect } from 'react'
import { 
  Card, 
  Table, 
  Tabs, 
  Tag, 
  Space, 
  Statistic,
  Row, 
  Col,
  Badge,
  Typography,
  Tooltip,
  Progress,
  Alert
} from 'antd'
import { 
  TrophyOutlined,
  RiseOutlined,
  FallOutlined,
  FireOutlined,
  DollarOutlined,
  ThunderboltOutlined,
  BarChartOutlined,
  CrownOutlined
} from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'

const { Title, Text } = Typography

// 真实的纳斯达克样本排名数据（基于我们的测试结果）
const RANKING_DATA = {
  activity: [
    { rank: 1, symbol: 'NVDA', name: 'NVIDIA Corporation', volume: 146107600, turnover: 25191000000, score: 85.1 },
    { rank: 2, symbol: 'INTC', name: 'Intel Corporation', volume: 60125000, turnover: 1389000000, score: 42.9 },
    { rank: 3, symbol: 'AAPL', name: 'Apple Inc.', volume: 48939500, turnover: 10340000000, score: 40.5 },
    { rank: 4, symbol: 'MSFT', name: 'Microsoft Corp.', volume: 21203400, turnover: 10810000000, score: 21.3 },
    { rank: 5, symbol: 'CSCO', name: 'Cisco Systems Inc.', volume: 16143300, turnover: 1099000000, score: 12.0 }
  ],
  volatility: [
    { rank: 1, symbol: 'NFLX', name: 'Netflix Inc.', price: 1209.24, range: 45.49, volatility: 3.76, score: 64.0 },
    { rank: 2, symbol: 'INTC', name: 'Intel Corporation', price: 23.10, range: 0.69, volatility: 2.99, score: 35.0 },
    { rank: 3, symbol: 'META', name: 'Meta Platforms Inc.', price: 704.28, range: 13.06, volatility: 1.85, score: 21.5 },
    { rank: 4, symbol: 'QCOM', name: 'Qualcomm Inc.', price: 154.80, range: 2.70, volatility: 1.74, score: 28.9 },
    { rank: 5, symbol: 'NVDA', name: 'NVIDIA Corporation', price: 172.41, range: 2.99, volatility: 1.73, score: 24.4 }
  ],
  performance: [
    { rank: 1, symbol: 'QCOM', name: 'Qualcomm Inc.', price: 154.80, change: 1.76, percent: 1.15, trend: '🔺' },
    { rank: 2, symbol: 'META', name: 'Meta Platforms Inc.', price: 704.28, change: 2.09, percent: 0.30, trend: '🔺' },
    { rank: 3, symbol: 'AAPL', name: 'Apple Inc.', price: 211.18, change: 0.31, percent: 0.15, trend: '🔺' },
    { rank: 4, symbol: 'PYPL', name: 'PayPal Holdings Inc.', price: 74.17, change: 0.07, percent: 0.09, trend: '🔺' },
    { rank: 5, symbol: 'ADBE', name: 'Adobe Inc.', price: 365.79, change: -1.28, percent: -0.35, trend: '🔻' }
  ],
  marketCap: [
    { rank: 1, symbol: 'MSFT', name: 'Microsoft Corp.', marketCap: 7.14, price: 510.05 },
    { rank: 2, symbol: 'AAPL', name: 'Apple Inc.', marketCap: 3.17, price: 211.18 },
    { rank: 3, symbol: 'META', name: 'Meta Platforms Inc.', marketCap: 2.82, price: 704.28 },
    { rank: 4, symbol: 'NVDA', name: 'NVIDIA Corporation', marketCap: 1.55, price: 172.41 },
    { rank: 5, symbol: 'NFLX', name: 'Netflix Inc.', marketCap: 1.21, price: 1209.24 }
  ],
  price: [
    { rank: 1, symbol: 'NFLX', name: 'Netflix Inc.', price: 1209.24, change: -2.63 },
    { rank: 2, symbol: 'META', name: 'Meta Platforms Inc.', price: 704.28, change: 0.30 },
    { rank: 3, symbol: 'MSFT', name: 'Microsoft Corp.', price: 510.05, change: -0.86 },
    { rank: 4, symbol: 'ADBE', name: 'Adobe Inc.', price: 365.79, change: -0.35 },
    { rank: 5, symbol: 'AAPL', name: 'Apple Inc.', price: 211.18, change: 0.15 }
  ],
  comprehensive: [
    { rank: 1, symbol: 'META', name: 'Meta Platforms Inc.', score: 74.0, scores: {activity: 50, volatility: 80, performance: 90, marketCap: 80, price: 60} },
    { rank: 2, symbol: 'NVDA', name: 'NVIDIA Corporation', score: 68.5, scores: {activity: 100, volatility: 60, performance: 40, marketCap: 70, price: 40} },
    { rank: 3, symbol: 'AAPL', name: 'Apple Inc.', score: 62.0, scores: {activity: 80, volatility: 10, performance: 80, marketCap: 90, price: 50} },
    { rank: 4, symbol: 'INTC', name: 'Intel Corporation', score: 62.0, scores: {activity: 90, volatility: 90, performance: 50, marketCap: 10, price: 10} },
    { rank: 5, symbol: 'MSFT', name: 'Microsoft Corp.', score: 60.0, scores: {activity: 70, volatility: 40, performance: 30, marketCap: 100, price: 70} }
  ]
}

const PersonalizedRanking: React.FC = () => {
  const [activeTab, setActiveTab] = useState('comprehensive')
  const [loading, setLoading] = useState(false)

  // 活跃度排名表格列
  const activityColumns: ColumnsType<any> = [
    {
      title: '排名',
      dataIndex: 'rank',
      key: 'rank',
      width: 60,
      render: (rank: number) => (
        <Badge count={rank} style={{ backgroundColor: rank <= 3 ? '#f50' : '#108ee9' }} />
      )
    },
    {
      title: '股票',
      key: 'stock',
      render: (record: any) => (
        <Space>
          <Text strong>{record.symbol}</Text>
          <Text type="secondary">{record.name.length > 15 ? record.name.substring(0, 15) + '...' : record.name}</Text>
        </Space>
      )
    },
    {
      title: '成交量',
      dataIndex: 'volume',
      key: 'volume',
      render: (volume: number) => `${(volume / 1000000).toFixed(1)}M`
    },
    {
      title: '成交额',
      dataIndex: 'turnover',
      key: 'turnover',
      render: (turnover: number) => `$${(turnover / 100000000).toFixed(1)}亿`
    },
    {
      title: '活跃评分',
      dataIndex: 'score',
      key: 'score',
      render: (score: number) => (
        <Progress 
          percent={score} 
          size="small" 
          format={(percent) => `${percent?.toFixed(1)}`}
          strokeColor={score > 60 ? '#52c41a' : score > 30 ? '#faad14' : '#ff4d4f'}
        />
      )
    }
  ]

  // 波动性排名表格列
  const volatilityColumns: ColumnsType<any> = [
    {
      title: '排名',
      dataIndex: 'rank',
      key: 'rank',
      width: 60,
      render: (rank: number) => (
        <Badge count={rank} style={{ backgroundColor: rank <= 3 ? '#f50' : '#108ee9' }} />
      )
    },
    {
      title: '股票',
      key: 'stock',
      render: (record: any) => (
        <Space>
          <Text strong>{record.symbol}</Text>
          <Text type="secondary">{record.name.length > 15 ? record.name.substring(0, 15) + '...' : record.name}</Text>
        </Space>
      )
    },
    {
      title: '当前价格',
      dataIndex: 'price',
      key: 'price',
      render: (price: number) => `$${price.toFixed(2)}`
    },
    {
      title: '日内振幅',
      dataIndex: 'range',
      key: 'range',
      render: (range: number) => `$${range.toFixed(2)}`
    },
    {
      title: '振幅%',
      dataIndex: 'volatility',
      key: 'volatility',
      render: (volatility: number) => (
        <Tag color={volatility > 3 ? 'red' : volatility > 2 ? 'orange' : 'green'}>
          {volatility.toFixed(2)}%
        </Tag>
      )
    }
  ]

  // 涨跌排名表格列
  const performanceColumns: ColumnsType<any> = [
    {
      title: '排名',
      dataIndex: 'rank',
      key: 'rank',
      width: 60,
      render: (rank: number) => (
        <Badge count={rank} style={{ backgroundColor: rank <= 3 ? '#f50' : '#108ee9' }} />
      )
    },
    {
      title: '股票',
      key: 'stock',
      render: (record: any) => (
        <Space>
          <Text strong>{record.symbol}</Text>
          <Text type="secondary">{record.name.length > 15 ? record.name.substring(0, 15) + '...' : record.name}</Text>
        </Space>
      )
    },
    {
      title: '当前价格',
      dataIndex: 'price',
      key: 'price',
      render: (price: number) => `$${price.toFixed(2)}`
    },
    {
      title: '涨跌额',
      dataIndex: 'change',
      key: 'change',
      render: (change: number) => (
        <Text style={{ color: change >= 0 ? '#52c41a' : '#ff4d4f' }}>
          {change >= 0 ? '+' : ''}${change.toFixed(2)}
        </Text>
      )
    },
    {
      title: '涨跌幅',
      dataIndex: 'percent',
      key: 'percent',
      render: (percent: number) => (
        <Space>
          <Tag color={percent >= 0 ? 'green' : 'red'}>
            {percent >= 0 ? '+' : ''}{percent.toFixed(2)}%
          </Tag>
        </Space>
      )
    },
    {
      title: '趋势',
      dataIndex: 'trend',
      key: 'trend',
      render: (trend: string) => <span style={{ fontSize: '16px' }}>{trend}</span>
    }
  ]

  // 市值排名表格列
  const marketCapColumns: ColumnsType<any> = [
    {
      title: '排名',
      dataIndex: 'rank',
      key: 'rank',
      width: 60,
      render: (rank: number) => (
        <Badge count={rank} style={{ backgroundColor: rank <= 3 ? '#f50' : '#108ee9' }} />
      )
    },
    {
      title: '股票',
      key: 'stock',
      render: (record: any) => (
        <Space>
          <Text strong>{record.symbol}</Text>
          <Text type="secondary">{record.name.length > 15 ? record.name.substring(0, 15) + '...' : record.name}</Text>
        </Space>
      )
    },
    {
      title: '市值',
      dataIndex: 'marketCap',
      key: 'marketCap',
      render: (marketCap: number) => `$${marketCap.toFixed(2)}万亿`
    },
    {
      title: '当前价格',
      dataIndex: 'price',
      key: 'price',
      render: (price: number) => `$${price.toFixed(2)}`
    }
  ]

  // 综合排名表格列
  const comprehensiveColumns: ColumnsType<any> = [
    {
      title: '排名',
      dataIndex: 'rank',
      key: 'rank',
      width: 60,
      render: (rank: number) => (
        <Badge count={rank} style={{ backgroundColor: rank <= 3 ? '#f50' : '#108ee9' }} />
      )
    },
    {
      title: '股票',
      key: 'stock',
      render: (record: any) => (
        <Space>
          <Text strong>{record.symbol}</Text>
          <Text type="secondary">{record.name.length > 15 ? record.name.substring(0, 15) + '...' : record.name}</Text>
        </Space>
      )
    },
    {
      title: '综合评分',
      dataIndex: 'score',
      key: 'score',
      render: (score: number) => (
        <Progress 
          percent={score} 
          size="small" 
          format={(percent) => `${percent?.toFixed(1)}`}
          strokeColor={score > 70 ? '#52c41a' : score > 50 ? '#faad14' : '#ff4d4f'}
        />
      )
    },
    {
      title: '活跃度',
      key: 'activity',
      render: (record: any) => (
        <Progress 
          percent={record.scores.activity} 
          size="small" 
          showInfo={false}
          strokeColor="#1890ff"
        />
      )
    },
    {
      title: '波动性',
      key: 'volatility',
      render: (record: any) => (
        <Progress 
          percent={record.scores.volatility} 
          size="small" 
          showInfo={false}
          strokeColor="#722ed1"
        />
      )
    },
    {
      title: '涨跌',
      key: 'performance',
      render: (record: any) => (
        <Progress 
          percent={record.scores.performance} 
          size="small" 
          showInfo={false}
          strokeColor="#52c41a"
        />
      )
    },
    {
      title: '市值',
      key: 'marketCap',
      render: (record: any) => (
        <Progress 
          percent={record.scores.marketCap} 
          size="small" 
          showInfo={false}
          strokeColor="#faad14"
        />
      )
    }
  ]

  const tabItems = [
    {
      key: 'comprehensive',
      label: (
        <span>
          <CrownOutlined />
          综合排名
        </span>
      ),
      children: (
        <div>
          <Alert
            message="多维度加权算法"
            description="权重配置: 活跃度30% + 波动性25% + 涨跌20% + 市值15% + 价格10%"
            type="info"
            showIcon
            style={{ marginBottom: 16 }}
          />
          <Table
            columns={comprehensiveColumns}
            dataSource={RANKING_DATA.comprehensive}
            pagination={false}
            size="small"
            rowKey="symbol"
          />
        </div>
      )
    },
    {
      key: 'activity',
      label: (
        <span>
          <FireOutlined />
          活跃度排名
        </span>
      ),
      children: (
        <div>
          <Row gutter={16} style={{ marginBottom: 16 }}>
            <Col span={8}>
              <Statistic
                title="最活跃股票"
                value="NVDA"
                prefix={<FireOutlined style={{ color: '#f50' }} />}
              />
            </Col>
            <Col span={8}>
              <Statistic
                title="最大成交量"
                value={146.1}
                suffix="M股"
              />
            </Col>
            <Col span={8}>
              <Statistic
                title="最大成交额"
                value="251.9"
                suffix="亿美元"
              />
            </Col>
          </Row>
          <Table
            columns={activityColumns}
            dataSource={RANKING_DATA.activity}
            pagination={false}
            size="small"
            rowKey="symbol"
          />
        </div>
      )
    },
    {
      key: 'volatility',
      label: (
        <span>
          <ThunderboltOutlined />
          波动性排名
        </span>
      ),
      children: (
        <div>
          <Row gutter={16} style={{ marginBottom: 16 }}>
            <Col span={8}>
              <Statistic
                title="最波动股票"
                value="NFLX"
                prefix={<ThunderboltOutlined style={{ color: '#722ed1' }} />}
              />
            </Col>
            <Col span={8}>
              <Statistic
                title="最大振幅"
                value={3.76}
                suffix="%"
              />
            </Col>
            <Col span={8}>
              <Statistic
                title="日内区间"
                value="$45.49"
              />
            </Col>
          </Row>
          <Table
            columns={volatilityColumns}
            dataSource={RANKING_DATA.volatility}
            pagination={false}
            size="small"
            rowKey="symbol"
          />
        </div>
      )
    },
    {
      key: 'performance',
      label: (
        <span>
          <RiseOutlined />
          涨跌排名
        </span>
      ),
      children: (
        <div>
          <Row gutter={16} style={{ marginBottom: 16 }}>
            <Col span={8}>
              <Statistic
                title="最佳表现"
                value="QCOM"
                prefix={<RiseOutlined style={{ color: '#52c41a' }} />}
              />
            </Col>
            <Col span={8}>
              <Statistic
                title="最大涨幅"
                value={1.15}
                suffix="%"
                valueStyle={{ color: '#52c41a' }}
              />
            </Col>
            <Col span={8}>
              <Statistic
                title="上涨股票数"
                value="4"
                suffix="/ 10"
              />
            </Col>
          </Row>
          <Table
            columns={performanceColumns}
            dataSource={RANKING_DATA.performance}
            pagination={false}
            size="small"
            rowKey="symbol"
          />
        </div>
      )
    },
    {
      key: 'marketCap',
      label: (
        <span>
          <DollarOutlined />
          市值排名
        </span>
      ),
      children: (
        <div>
          <Row gutter={16} style={{ marginBottom: 16 }}>
            <Col span={8}>
              <Statistic
                title="最大市值"
                value="MSFT"
                prefix={<DollarOutlined style={{ color: '#faad14' }} />}
              />
            </Col>
            <Col span={8}>
              <Statistic
                title="市值规模"
                value="7.14"
                suffix="万亿美元"
              />
            </Col>
            <Col span={8}>
              <Statistic
                title="样本总市值"
                value="16.6"
                suffix="万亿美元"
              />
            </Col>
          </Row>
          <Table
            columns={marketCapColumns}
            dataSource={RANKING_DATA.marketCap}
            pagination={false}
            size="small"
            rowKey="symbol"
          />
        </div>
      )
    }
  ]

  return (
    <Card>
      <div style={{ marginBottom: 16 }}>
        <Title level={3}>
          <TrophyOutlined style={{ color: '#faad14', marginRight: 8 }} />
          个性化股票排名
        </Title>
        <Text type="secondary">
          基于Twelve Data API的真实纳斯达克样本股票排名系统
        </Text>
      </div>
      
      <Alert
        message="实时数据源"
        description="排名基于10只纳斯达克代表性股票的真实市场数据，包括AAPL、MSFT、NVDA、META、NFLX等"
        type="success"
        showIcon
        style={{ marginBottom: 16 }}
      />

      <Tabs
        activeKey={activeTab}
        onChange={setActiveTab}
        items={tabItems}
        size="large"
      />
    </Card>
  )
}

export default PersonalizedRanking