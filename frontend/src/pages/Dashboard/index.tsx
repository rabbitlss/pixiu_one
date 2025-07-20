import React from 'react'
import { Typography, Tabs } from 'antd'
import { DashboardOutlined, BarChartOutlined, FireOutlined } from '@ant-design/icons'
import MarketOverview from '@/components/MarketOverview'
import PersonalizedRanking from '@/components/PersonalizedRanking'

const { Title } = Typography

const Dashboard: React.FC = () => {
  const items = [
    {
      key: 'overview',
      label: (
        <span>
          <DashboardOutlined />
          市场概览
        </span>
      ),
      children: <MarketOverview />
    },
    {
      key: 'ranking',
      label: (
        <span>
          <BarChartOutlined />
          股票排行
        </span>
      ),
      children: <PersonalizedRanking />
    },
    {
      key: 'hotspot',
      label: (
        <span>
          <FireOutlined />
          热点分析
        </span>
      ),
      children: (
        <div style={{ 
          height: 400, 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'center',
          color: '#999'
        }}>
          热点分析功能开发中...
        </div>
      )
    }
  ]

  return (
    <div>
      <Title level={2}>投资决策仪表盘</Title>
      <Tabs defaultActiveKey="overview" items={items} size="large" />
    </div>
  )
}

export default Dashboard