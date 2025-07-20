import React, { useState, useMemo } from 'react'
import { 
  Card, 
  Table, 
  Tag, 
  Progress, 
  Space, 
  Select, 
  
  Row, 
  Col, 
  Statistic, 
  Badge,
  Tooltip,
  Input
} from 'antd'
import { 
  FireOutlined, 
  TrophyOutlined, 
  RiseOutlined, 
  FallOutlined,
  SearchOutlined,
  HeartOutlined,
  ThunderboltOutlined
} from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'

// 股票数据类型定义
interface StockData {
  code: string
  name: string
  price: number
  change: number
  changePercent: number
  comprehensiveScore: number
  financialHealth: number
  growthPotential: number
  valuationLevel: number
  marketMomentum: number
  sentimentIndex: number
  industry: string
  marketCap: number
  volume: number
  pe: number
  pb: number
  roe: number
  isTop: boolean
}

// 模拟数据
const mockStockData: StockData[] = [
  {
    code: '000001',
    name: '平安银行',
    price: 12.85,
    change: 0.23,
    changePercent: 1.82,
    comprehensiveScore: 88,
    financialHealth: 92,
    growthPotential: 75,
    valuationLevel: 89,
    marketMomentum: 85,
    sentimentIndex: 78,
    industry: '银行',
    marketCap: 2486.5,
    volume: 145632000,
    pe: 6.2,
    pb: 0.85,
    roe: 12.3,
    isTop: true
  },
  {
    code: '600519',
    name: '贵州茅台',
    price: 1678.50,
    change: -15.30,
    changePercent: -0.90,
    comprehensiveScore: 91,
    financialHealth: 95,
    growthPotential: 82,
    valuationLevel: 88,
    marketMomentum: 72,
    sentimentIndex: 85,
    industry: '白酒',
    marketCap: 21056.8,
    volume: 8562400,
    pe: 28.5,
    pb: 9.2,
    roe: 24.8,
    isTop: true
  },
  {
    code: '300750',
    name: '宁德时代',
    price: 185.26,
    change: 8.45,
    changePercent: 4.78,
    comprehensiveScore: 85,
    financialHealth: 88,
    growthPotential: 92,
    valuationLevel: 76,
    marketMomentum: 89,
    sentimentIndex: 91,
    industry: '电池',
    marketCap: 8146.4,
    volume: 98456200,
    pe: 45.2,
    pb: 5.8,
    roe: 18.6,
    isTop: true
  },
  {
    code: '002415',
    name: '海康威视',
    price: 32.45,
    change: 1.25,
    changePercent: 4.01,
    comprehensiveScore: 79,
    financialHealth: 85,
    growthPotential: 78,
    valuationLevel: 82,
    marketMomentum: 76,
    sentimentIndex: 71,
    industry: '安防',
    marketCap: 3024.8,
    volume: 76842000,
    pe: 18.9,
    pb: 2.1,
    roe: 15.2,
    isTop: false
  },
  {
    code: '000858',
    name: '五粮液',
    price: 128.36,
    change: -2.14,
    changePercent: -1.64,
    comprehensiveScore: 82,
    financialHealth: 89,
    growthPotential: 74,
    valuationLevel: 85,
    marketMomentum: 68,
    sentimentIndex: 76,
    industry: '白酒',
    marketCap: 5021.5,
    volume: 34562000,
    pe: 22.4,
    pb: 4.5,
    roe: 21.7,
    isTop: false
  }
]

const StockRanking: React.FC = () => {
  const [searchText, setSearchText] = useState('')
  const [selectedIndustry, setSelectedIndustry] = useState<string>('all')
  const [sortBy, setSortBy] = useState<string>('comprehensiveScore')

  // 获取评分颜色
  const getScoreColor = (score: number) => {
    if (score >= 85) return '#52c41a' // 绿色
    if (score >= 70) return '#1890ff' // 蓝色
    if (score >= 60) return '#faad14' // 黄色
    return '#ff4d4f' // 红色
  }

  // 获取评分等级
  const getScoreLevel = (score: number) => {
    if (score >= 85) return { text: '优秀', color: 'success' }
    if (score >= 70) return { text: '良好', color: 'processing' }
    if (score >= 60) return { text: '一般', color: 'warning' }
    return { text: '较差', color: 'error' }
  }

  // 获取情绪图标
  const getSentimentIcon = (score: number) => {
    if (score >= 80) return <FireOutlined style={{ color: '#ff4d4f' }} />
    if (score >= 60) return <HeartOutlined style={{ color: '#faad14' }} />
    return <ThunderboltOutlined style={{ color: '#1890ff' }} />
  }

  // 行业列表
  const industries = ['all', ...Array.from(new Set(mockStockData.map(item => item.industry)))]

  // 过滤和排序数据
  const filteredData = useMemo(() => {
    const data = mockStockData.filter(item => {
      const matchSearch = item.name.includes(searchText) || item.code.includes(searchText)
      const matchIndustry = selectedIndustry === 'all' || item.industry === selectedIndustry
      return matchSearch && matchIndustry
    })

    return data.sort((a, b) => {
      switch (sortBy) {
        case 'comprehensiveScore':
          return b.comprehensiveScore - a.comprehensiveScore
        case 'changePercent':
          return b.changePercent - a.changePercent
        case 'marketCap':
          return b.marketCap - a.marketCap
        case 'sentimentIndex':
          return b.sentimentIndex - a.sentimentIndex
        default:
          return b.comprehensiveScore - a.comprehensiveScore
      }
    })
  }, [searchText, selectedIndustry, sortBy])

  // 表格列定义
  const columns: ColumnsType<StockData> = [
    {
      title: '排名',
      key: 'rank',
      width: 60,
      render: (_, __, index) => (
        <Space>
          {index < 3 && <TrophyOutlined style={{ color: '#faad14' }} />}
          <span style={{ fontWeight: index < 3 ? 'bold' : 'normal' }}>
            {index + 1}
          </span>
        </Space>
      )
    },
    {
      title: '股票',
      key: 'stock',
      width: 200,
      render: (_, record) => (
        <Space direction="vertical" size={0}>
          <Space>
            <span style={{ fontWeight: 'bold' }}>{record.name}</span>
            {record.isTop && <Badge count="TOP" style={{ backgroundColor: '#52c41a' }} />}
          </Space>
          <span style={{ color: '#666', fontSize: '12px' }}>{record.code}</span>
        </Space>
      )
    },
    {
      title: '现价',
      key: 'price',
      width: 120,
      render: (_, record) => (
        <Space direction="vertical" size={0}>
          <span style={{ fontWeight: 'bold', fontSize: '16px' }}>
            ¥{record.price.toFixed(2)}
          </span>
          <Space size={4}>
            {record.change >= 0 ? (
              <RiseOutlined style={{ color: '#ff4d4f' }} />
            ) : (
              <FallOutlined style={{ color: '#52c41a' }} />
            )}
            <span style={{ 
              color: record.change >= 0 ? '#ff4d4f' : '#52c41a',
              fontSize: '12px'
            }}>
              {record.change >= 0 ? '+' : ''}{record.changePercent.toFixed(2)}%
            </span>
          </Space>
        </Space>
      )
    },
    {
      title: '综合评分',
      key: 'comprehensiveScore',
      width: 120,
      render: (_, record) => {
        const level = getScoreLevel(record.comprehensiveScore)
        return (
          <Space direction="vertical" size={0}>
            <span style={{ 
              fontWeight: 'bold', 
              color: getScoreColor(record.comprehensiveScore),
              fontSize: '18px'
            }}>
              {record.comprehensiveScore}
            </span>
            <Tag color={level.color as any}>{level.text}</Tag>
          </Space>
        )
      }
    },
    {
      title: '各维度表现',
      key: 'dimensions',
      width: 300,
      render: (_, record) => (
        <Space direction="vertical" size={4} style={{ width: '100%' }}>
          <Tooltip title={`财务健康: ${record.financialHealth}分`}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <span style={{ width: 60, fontSize: '12px' }}>财务</span>
              <Progress 
                percent={record.financialHealth} 
                size="small" 
                showInfo={false}
                strokeColor={getScoreColor(record.financialHealth)}
              />
            </div>
          </Tooltip>
          <Tooltip title={`成长潜力: ${record.growthPotential}分`}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <span style={{ width: 60, fontSize: '12px' }}>成长</span>
              <Progress 
                percent={record.growthPotential} 
                size="small" 
                showInfo={false}
                strokeColor={getScoreColor(record.growthPotential)}
              />
            </div>
          </Tooltip>
          <Tooltip title={`估值水平: ${record.valuationLevel}分`}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <span style={{ width: 60, fontSize: '12px' }}>估值</span>
              <Progress 
                percent={record.valuationLevel} 
                size="small" 
                showInfo={false}
                strokeColor={getScoreColor(record.valuationLevel)}
              />
            </div>
          </Tooltip>
          <Tooltip title={`市场动量: ${record.marketMomentum}分`}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <span style={{ width: 60, fontSize: '12px' }}>动量</span>
              <Progress 
                percent={record.marketMomentum} 
                size="small" 
                showInfo={false}
                strokeColor={getScoreColor(record.marketMomentum)}
              />
            </div>
          </Tooltip>
        </Space>
      )
    },
    {
      title: '情绪指数',
      key: 'sentiment',
      width: 100,
      render: (_, record) => (
        <Space direction="vertical" size={0} style={{ textAlign: 'center' }}>
          <div style={{ fontSize: '20px' }}>
            {getSentimentIcon(record.sentimentIndex)}
          </div>
          <span style={{ fontSize: '12px', fontWeight: 'bold' }}>
            {record.sentimentIndex}
          </span>
        </Space>
      )
    },
    {
      title: '基本面',
      key: 'fundamentals',
      width: 150,
      render: (_, record) => (
        <Space direction="vertical" size={0}>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px' }}>
            <span>PE:</span>
            <span style={{ fontWeight: 'bold' }}>{record.pe}</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px' }}>
            <span>PB:</span>
            <span style={{ fontWeight: 'bold' }}>{record.pb}</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px' }}>
            <span>ROE:</span>
            <span style={{ fontWeight: 'bold' }}>{record.roe}%</span>
          </div>
        </Space>
      )
    }
  ]

  return (
    <div>
      {/* 控制面板 */}
      <Card style={{ marginBottom: 16 }}>
        <Row gutter={16} align="middle">
          <Col span={6}>
            <Input
              placeholder="搜索股票名称或代码"
              prefix={<SearchOutlined />}
              value={searchText}
              onChange={(e) => setSearchText(e.target.value)}
            />
          </Col>
          <Col span={4}>
            <Select
              value={selectedIndustry}
              onChange={setSelectedIndustry}
              style={{ width: '100%' }}
              placeholder="选择行业"
            >
              <Select.Option value="all">全部行业</Select.Option>
              {industries.slice(1).map(industry => (
                <Select.Option key={industry} value={industry}>
                  {industry}
                </Select.Option>
              ))}
            </Select>
          </Col>
          <Col span={4}>
            <Select
              value={sortBy}
              onChange={setSortBy}
              style={{ width: '100%' }}
              placeholder="排序方式"
            >
              <Select.Option value="comprehensiveScore">综合评分</Select.Option>
              <Select.Option value="changePercent">涨跌幅</Select.Option>
              <Select.Option value="marketCap">市值</Select.Option>
              <Select.Option value="sentimentIndex">情绪指数</Select.Option>
            </Select>
          </Col>
          <Col span={10}>
            <Row gutter={8}>
              <Col span={6}>
                <Statistic
                  title="总股票数"
                  value={filteredData.length}
                  valueStyle={{ fontSize: '16px' }}
                />
              </Col>
              <Col span={6}>
                <Statistic
                  title="优秀评级"
                  value={filteredData.filter(item => item.comprehensiveScore >= 85).length}
                  valueStyle={{ fontSize: '16px', color: '#52c41a' }}
                />
              </Col>
              <Col span={6}>
                <Statistic
                  title="上涨股票"
                  value={filteredData.filter(item => item.changePercent > 0).length}
                  valueStyle={{ fontSize: '16px', color: '#ff4d4f' }}
                />
              </Col>
              <Col span={6}>
                <Statistic
                  title="热度股票"
                  value={filteredData.filter(item => item.sentimentIndex >= 80).length}
                  valueStyle={{ fontSize: '16px', color: '#faad14' }}
                />
              </Col>
            </Row>
          </Col>
        </Row>
      </Card>

      {/* 股票排行榜 */}
      <Card title="股票综合排行榜" extra={<Tag color="blue">实时更新</Tag>}>
        <Table
          columns={columns}
          dataSource={filteredData}
          rowKey="code"
          pagination={{
            pageSize: 20,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total) => `共 ${total} 只股票`
          }}
          scroll={{ x: 1200 }}
          size="small"
        />
      </Card>
    </div>
  )
}

export default StockRanking