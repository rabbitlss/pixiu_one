import React from 'react'
import { Card, Row, Col, Statistic, Space, Typography } from 'antd'
import { ArrowUpOutlined, ArrowDownOutlined } from '@ant-design/icons'

const { Title } = Typography

const Dashboard: React.FC = () => {
  // TODO: 从API获取真实数据
  const mockData = {
    totalStocks: 4832,
    activeStocks: 4205,
    avgPrice: 23.45,
    priceChange: 2.3,
    marketCap: '45.2万亿',
    marketCapChange: -1.2,
  }

  return (
    <div>
      <Title level={2}>仪表盘</Title>
      
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="股票总数"
              value={mockData.totalStocks}
              precision={0}
              valueStyle={{ color: '#3f8600' }}
            />
          </Card>
        </Col>
        
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="活跃股票"
              value={mockData.activeStocks}
              precision={0}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="平均股价"
              value={mockData.avgPrice}
              precision={2}
              valueStyle={{ 
                color: mockData.priceChange >= 0 ? '#3f8600' : '#cf1322' 
              }}
              prefix="¥"
              suffix={
                <Space>
                  {mockData.priceChange >= 0 ? (
                    <ArrowUpOutlined style={{ color: '#3f8600' }} />
                  ) : (
                    <ArrowDownOutlined style={{ color: '#cf1322' }} />
                  )}
                  <span style={{ 
                    color: mockData.priceChange >= 0 ? '#3f8600' : '#cf1322',
                    fontSize: 12
                  }}>
                    {Math.abs(mockData.priceChange)}%
                  </span>
                </Space>
              }
            />
          </Card>
        </Col>
        
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="总市值"
              value={mockData.marketCap}
              valueStyle={{ 
                color: mockData.marketCapChange >= 0 ? '#3f8600' : '#cf1322' 
              }}
              suffix={
                <Space>
                  {mockData.marketCapChange >= 0 ? (
                    <ArrowUpOutlined style={{ color: '#3f8600' }} />
                  ) : (
                    <ArrowDownOutlined style={{ color: '#cf1322' }} />
                  )}
                  <span style={{ 
                    color: mockData.marketCapChange >= 0 ? '#3f8600' : '#cf1322',
                    fontSize: 12
                  }}>
                    {Math.abs(mockData.marketCapChange)}%
                  </span>
                </Space>
              }
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]}>
        <Col xs={24} lg={16}>
          <Card title="市场趋势" size="small">
            <div style={{ 
              height: 300, 
              display: 'flex', 
              alignItems: 'center', 
              justifyContent: 'center',
              color: '#999'
            }}>
              图表组件将在后续实现
            </div>
          </Card>
        </Col>
        
        <Col xs={24} lg={8}>
          <Card title="热门股票" size="small">
            <div style={{ 
              height: 300, 
              display: 'flex', 
              alignItems: 'center', 
              justifyContent: 'center',
              color: '#999'
            }}>
              热门股票列表将在后续实现
            </div>
          </Card>
        </Col>
      </Row>
    </div>
  )
}

export default Dashboard