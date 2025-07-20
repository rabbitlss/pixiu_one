import React from 'react'
import { Typography } from 'antd'

const { Title } = Typography

const Analysis: React.FC = () => {
  return (
    <div>
      <Title level={2}>数据分析</Title>
      <div style={{ 
        height: 400, 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'center',
        color: '#999'
      }}>
        数据分析功能将在后续实现
      </div>
    </div>
  )
}

export default Analysis