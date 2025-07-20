import React from 'react'
import { Typography } from 'antd'

const { Title } = Typography

const Settings: React.FC = () => {
  return (
    <div>
      <Title level={2}>系统设置</Title>
      <div style={{ 
        height: 400, 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'center',
        color: '#999'
      }}>
        系统设置功能将在后续实现
      </div>
    </div>
  )
}

export default Settings