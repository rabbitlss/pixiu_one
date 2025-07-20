import React, { useState, useEffect } from 'react'
import {
  Typography,
  Card,
  Row,
  Col,
  Table,
  Select,
  Button,
  Space,
  Statistic,
  Progress,
  Tag,
  Alert,
  Tabs,
  message,
  Spin,
  Empty
} from 'antd'
import {
  SwapOutlined,
  ArrowUpOutlined,
  ArrowDownOutlined,
  DollarOutlined,
  BankOutlined,
  BarChartOutlined,
  GlobalOutlined,
  StarOutlined,
  ThunderboltOutlined,
  SafetyOutlined
} from '@ant-design/icons'
// Charts will be implemented with simple Ant Design components for now
import { companyApi } from '@/services/api'

const { Title, Text } = Typography
const { Option } = Select
const { TabPane } = Tabs

interface CompanyData {
  id: number
  company_name: string
  ticker_symbol: string
  sector: string
  industry: string
  country: string
  full_time_employees: number
  business_summary: string
  latest_financial_metrics?: any
  latest_market_position?: any
  recent_corporate_actions?: any[]
  latest_esg_metrics?: any
  recent_analyst_ratings?: any[]
}

const CompanyComparison: React.FC = () => {
  const [companies, setCompanies] = useState<CompanyData[]>([])
  const [selectedCompanies, setSelectedCompanies] = useState<number[]>([])
  const [loading, setLoading] = useState(false)
  const [comparisonData, setComparisonData] = useState<CompanyData[]>([])

  // 获取公司列表
  const fetchCompanies = async () => {
    try {
      const response = await companyApi.getCompanyList({ skip: 0, limit: 100 })
      if (response.data?.items) {
        setCompanies(response.data.items as any)
      }
    } catch (error: any) {
      message.error('获取公司列表失败')
    }
  }

  // 获取公司详细信息
  const fetchCompanyDetails = async (companyIds: number[]) => {
    setLoading(true)
    try {
      const promises = companyIds.map(id => companyApi.getCompanyDetail(id.toString()))
      const responses = await Promise.all(promises)
      const details = responses.map(response => response.data)
      setComparisonData(details as any)
    } catch (error: any) {
      message.error('获取公司详细信息失败')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchCompanies()
  }, [])

  useEffect(() => {
    if (selectedCompanies.length > 0) {
      fetchCompanyDetails(selectedCompanies)
    } else {
      setComparisonData([])
    }
  }, [selectedCompanies])

  // 格式化数字
  const formatNumber = (num: number, unit = '') => {
    if (!num) return 'N/A'
    if (num >= 1e12) return `${(num / 1e12).toFixed(1)}T${unit}`
    if (num >= 1e9) return `${(num / 1e9).toFixed(1)}B${unit}`
    if (num >= 1e6) return `${(num / 1e6).toFixed(1)}M${unit}`
    if (num >= 1e3) return `${(num / 1e3).toFixed(1)}K${unit}`
    return `${num.toLocaleString()}${unit}`
  }

  // 获取趋势图标
  const getTrendIcon = (value: number, isPositive = true) => {
    if (!value) return null
    const color = (isPositive && value > 0) || (!isPositive && value < 0) ? '#52c41a' : '#ff4d4f'
    const Icon = value > 0 ? ArrowUpOutlined : ArrowDownOutlined
    return <Icon style={{ color, marginLeft: 4 }} />
  }

  // 获取评级颜色
  const getRatingColor = (value: number, type: 'performance' | 'risk' = 'performance') => {
    if (type === 'performance') {
      if (value >= 80) return '#52c41a'
      if (value >= 60) return '#faad14'
      if (value >= 40) return '#fa8c16'
      return '#ff4d4f'
    } else {
      if (value <= 20) return '#52c41a'
      if (value <= 40) return '#faad14'
      if (value <= 60) return '#fa8c16'
      return '#ff4d4f'
    }
  }

  // 基本信息对比表格
  const getBasicInfoColumns = () => [
    {
      title: '指标',
      dataIndex: 'metric',
      key: 'metric',
      width: 120,
      render: (text: string) => <Text strong>{text}</Text>
    },
    ...comparisonData.map((company, index) => ({
      title: (
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontWeight: 'bold', color: '#1890ff' }}>
            {company.ticker_symbol}
          </div>
          <div style={{ fontSize: '12px', color: '#666' }}>
            {company.company_name}
          </div>
        </div>
      ),
      dataIndex: `company_${index}`,
      key: `company_${index}`,
      width: 150,
      align: 'center' as const
    }))
  ]

  const getBasicInfoData = () => {
    if (comparisonData.length === 0) return []

    const metrics = [
      { key: 'sector', label: '板块' },
      { key: 'industry', label: '行业' },
      { key: 'country', label: '国家' },
      { key: 'employees', label: '员工数' },
      { key: 'revenue', label: '年收入' },
      { key: 'net_income', label: '净利润' },
      { key: 'total_assets', label: '总资产' },
      { key: 'market_cap', label: '市值' }
    ]

    return metrics.map(metric => {
      const row: any = { metric: metric.label }
      comparisonData.forEach((company, index) => {
        let value: any = 'N/A'
        
        switch (metric.key) {
          case 'sector':
            value = <Tag color="blue">{company.sector || 'N/A'}</Tag>
            break
          case 'industry':
            value = <Tag color="green">{company.industry || 'N/A'}</Tag>
            break
          case 'country':
            value = <Tag color="orange">{company.country || 'N/A'}</Tag>
            break
          case 'employees':
            value = company.full_time_employees ? formatNumber(company.full_time_employees, '人') : 'N/A'
            break
          case 'revenue':
            value = company.latest_financial_metrics?.revenue ? 
              `$${formatNumber(company.latest_financial_metrics.revenue)}` : 'N/A'
            break
          case 'net_income':
            value = company.latest_financial_metrics?.net_income ?
              `$${formatNumber(company.latest_financial_metrics.net_income)}` : 'N/A'
            break
          case 'total_assets':
            value = company.latest_financial_metrics?.total_assets ?
              `$${formatNumber(company.latest_financial_metrics.total_assets)}` : 'N/A'
            break
          case 'market_cap':
            value = company.latest_market_position?.market_cap ?
              `$${formatNumber(company.latest_market_position.market_cap)}` : 'N/A'
            break
        }
        
        row[`company_${index}`] = value
      })
      return row
    })
  }

  // 财务指标对比卡片
  const renderFinancialMetrics = () => {
    if (comparisonData.length === 0) return null

    const metrics = [
      { key: 'return_on_equity', label: '股本回报率', unit: '%', icon: <ArrowUpOutlined />, isGood: true },
      { key: 'return_on_assets', label: '资产回报率', unit: '%', icon: <BarChartOutlined />, isGood: true },
      { key: 'price_to_earnings', label: '市盈率', unit: '', icon: <DollarOutlined />, isGood: false },
      { key: 'price_to_book', label: '市净率', unit: '', icon: <BankOutlined />, isGood: false },
      { key: 'debt_to_equity', label: '负债权益比', unit: '', icon: <SafetyOutlined />, isGood: false },
      { key: 'revenue_growth', label: '收入增长率', unit: '%', icon: <ThunderboltOutlined />, isGood: true }
    ]

    return (
      <Row gutter={[16, 16]}>
        {metrics.map(metric => (
          <Col span={24} key={metric.key}>
            <Card size="small" title={
              <Space>
                {metric.icon}
                {metric.label}
              </Space>
            }>
              <Row gutter={[16, 8]}>
                {comparisonData.map((company, index) => {
                  const value = company.latest_financial_metrics?.[metric.key]
                  const formattedValue = value ? `${value.toFixed(2)}${metric.unit}` : 'N/A'
                  
                  return (
                    <Col span={24 / comparisonData.length} key={index}>
                      <Statistic
                        title={company.ticker_symbol}
                        value={formattedValue}
                        valueStyle={{
                          color: value ? getRatingColor(
                            metric.isGood ? value : (100 - value),
                            'performance'
                          ) : '#666'
                        }}
                        suffix={value && getTrendIcon(value, metric.isGood)}
                      />
                    </Col>
                  )
                })}
              </Row>
            </Card>
          </Col>
        ))}
      </Row>
    )
  }

  // 收入趋势图
  const renderRevenueTrend = () => {
    if (comparisonData.length === 0) return null

    return (
      <Card title="收入对比" extra={<Tag color="blue">2024年</Tag>}>
        <Row gutter={[16, 16]}>
          {comparisonData.map((company, index) => {
            const revenue = company.latest_financial_metrics?.revenue || 0
            return (
              <Col span={24 / comparisonData.length} key={index}>
                <Statistic
                  title={company.ticker_symbol}
                  value={formatNumber(revenue, '$')}
                  valueStyle={{ 
                    color: '#1890ff',
                    fontSize: '24px'
                  }}
                  prefix={<DollarOutlined />}
                />
              </Col>
            )
          })}
        </Row>
      </Card>
    )
  }

  // 业务概述对比
  const renderBusinessOverview = () => {
    if (comparisonData.length === 0) return null

    return (
      <Row gutter={[16, 16]}>
        {comparisonData.map((company, index) => (
          <Col span={24 / comparisonData.length} key={index}>
            <Card
              title={
                <Space>
                  <GlobalOutlined />
                  {company.company_name}
                </Space>
              }
              extra={<Tag color="processing">{company.ticker_symbol}</Tag>}
            >
              <div style={{ marginBottom: 16 }}>
                <Text type="secondary">业务概述</Text>
                <div style={{ marginTop: 8, fontSize: '14px', lineHeight: 1.5 }}>
                  {company.business_summary ? 
                    company.business_summary.substring(0, 200) + '...' : 
                    '暂无业务概述信息'
                  }
                </div>
              </div>
              
              {company.latest_esg_metrics && (
                <div>
                  <Text type="secondary">ESG评分</Text>
                  <Row gutter={[8, 8]} style={{ marginTop: 8 }}>
                    <Col span={8}>
                      <div style={{ textAlign: 'center' }}>
                        <Progress
                          type="circle"
                          size={60}
                          percent={company.latest_esg_metrics.esg_score_environment || 0}
                          strokeColor="#52c41a"
                        />
                        <div style={{ fontSize: '12px', marginTop: 4 }}>环境</div>
                      </div>
                    </Col>
                    <Col span={8}>
                      <div style={{ textAlign: 'center' }}>
                        <Progress
                          type="circle"
                          size={60}
                          percent={company.latest_esg_metrics.esg_score_social || 0}
                          strokeColor="#1890ff"
                        />
                        <div style={{ fontSize: '12px', marginTop: 4 }}>社会</div>
                      </div>
                    </Col>
                    <Col span={8}>
                      <div style={{ textAlign: 'center' }}>
                        <Progress
                          type="circle"
                          size={60}
                          percent={company.latest_esg_metrics.esg_score_governance || 0}
                          strokeColor="#fa8c16"
                        />
                        <div style={{ fontSize: '12px', marginTop: 4 }}>治理</div>
                      </div>
                    </Col>
                  </Row>
                </div>
              )}
            </Card>
          </Col>
        ))}
      </Row>
    )
  }

  // 分析师评级对比
  const renderAnalystRatings = () => {
    if (comparisonData.length === 0) return null

    return (
      <Row gutter={[16, 16]}>
        {comparisonData.map((company, index) => {
          const rating = company.recent_analyst_ratings?.[0]
          
          return (
            <Col span={24 / comparisonData.length} key={index}>
              <Card
                title={company.ticker_symbol}
                extra={rating?.rating && (
                  <Tag color={
                    rating.rating.includes('Buy') ? 'green' :
                    rating.rating.includes('Hold') ? 'orange' : 'red'
                  }>
                    {rating.rating}
                  </Tag>
                )}
              >
                {rating ? (
                  <Space direction="vertical" style={{ width: '100%' }}>
                    <Statistic
                      title="目标价"
                      value={rating.target_price}
                      prefix="$"
                      precision={2}
                      valueStyle={{ color: '#3f8600' }}
                    />
                    <Statistic
                      title="当前价"
                      value={rating.current_price}
                      prefix="$"
                      precision={2}
                    />
                    {rating.analyst_firm && (
                      <div>
                        <Text type="secondary">分析师: </Text>
                        <Text>{rating.analyst_firm}</Text>
                      </div>
                    )}
                  </Space>
                ) : (
                  <Empty description="暂无分析师评级" />
                )}
              </Card>
            </Col>
          )
        })}
      </Row>
    )
  }

  return (
    <div style={{ padding: '0 24px' }}>
      <div style={{ marginBottom: 24 }}>
        <Title level={2} style={{ margin: 0, display: 'flex', alignItems: 'center' }}>
          <SwapOutlined style={{ marginRight: 8, color: '#1890ff' }} />
          公司对比分析
        </Title>
        <Text type="secondary">选择公司进行多维度对比分析，快速获取关键信息</Text>
      </div>

      <Card style={{ marginBottom: 24 }}>
        <Space>
          <Text strong>选择对比公司:</Text>
          <Select
            mode="multiple"
            placeholder="选择要对比的公司"
            style={{ minWidth: 400 }}
            value={selectedCompanies}
            onChange={setSelectedCompanies}
            maxTagCount={3}
          >
            {companies.map(company => (
              <Option key={company.id} value={company.id}>
                {company.ticker_symbol} - {company.company_name}
              </Option>
            ))}
          </Select>
          <Button 
            type="primary" 
            icon={<SwapOutlined />}
            disabled={selectedCompanies.length < 2}
          >
            开始对比
          </Button>
        </Space>
      </Card>

      {selectedCompanies.length < 2 && (
        <Alert
          message="请选择至少2个公司进行对比"
          description="选择多个公司可以进行更全面的对比分析"
          type="info"
          showIcon
          style={{ marginBottom: 24 }}
        />
      )}

      <Spin spinning={loading}>
        {comparisonData.length >= 2 ? (
          <Tabs defaultActiveKey="overview" size="large">
            <TabPane 
              tab={
                <span>
                  <GlobalOutlined />
                  概览对比
                </span>
              } 
              key="overview"
            >
              <Space direction="vertical" size="large" style={{ width: '100%' }}>
                <Table
                  columns={getBasicInfoColumns()}
                  dataSource={getBasicInfoData()}
                  pagination={false}
                  bordered
                  size="small"
                  rowKey="metric"
                />
                {renderBusinessOverview()}
              </Space>
            </TabPane>

            <TabPane 
              tab={
                <span>
                  <BarChartOutlined />
                  财务指标
                </span>
              } 
              key="financial"
            >
              <Space direction="vertical" size="large" style={{ width: '100%' }}>
                {renderFinancialMetrics()}
                {renderRevenueTrend()}
              </Space>
            </TabPane>

            <TabPane 
              tab={
                <span>
                  <StarOutlined />
                  分析师评级
                </span>
              } 
              key="ratings"
            >
              {renderAnalystRatings()}
            </TabPane>
          </Tabs>
        ) : selectedCompanies.length > 0 ? (
          <Empty description="请选择至少2个公司进行对比" />
        ) : (
          <Empty description="请选择公司开始对比分析" />
        )}
      </Spin>
    </div>
  )
}

export default CompanyComparison