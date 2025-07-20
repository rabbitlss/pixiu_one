import React from 'react'
import { Typography } from 'antd'

const { Title } = Typography

const StockList: React.FC = () => {
  return (
    <div>
      <Title level={2}>股票列表</Title>
      <div style={{ 
        height: 400, 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'center',
        color: '#999'
      }}>
        股票列表功能将在后续实现
      </div>
    </div>
  )
}

export default StockList