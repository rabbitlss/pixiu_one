import React from 'react'
import { Typography } from 'antd'

const { Title } = Typography

const CompanyInfo: React.FC = () => {
  return (
    <div>
      <Title level={2}>公司信息</Title>
      <div style={{ 
        height: 400, 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'center',
        color: '#999'
      }}>
        公司信息功能将在后续实现
      </div>
    </div>
  )
}

export default CompanyInfo