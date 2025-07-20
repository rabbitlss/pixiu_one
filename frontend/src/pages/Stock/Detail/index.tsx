import React from 'react'
import { Typography } from 'antd'
import { useParams } from 'react-router-dom'

const { Title } = Typography

const StockDetail: React.FC = () => {
  const { code } = useParams<{ code: string }>()

  return (
    <div>
      <Title level={2}>股票详情 - {code}</Title>
      <div style={{ 
        height: 400, 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'center',
        color: '#999'
      }}>
        股票详情功能将在后续实现
      </div>
    </div>
  )
}

export default StockDetail