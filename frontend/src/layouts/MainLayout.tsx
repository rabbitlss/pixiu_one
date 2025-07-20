import React, { useState } from 'react'
import { Layout, Menu, Avatar, Dropdown, Space, Typography, theme } from 'antd'
import { Outlet, useNavigate, useLocation } from 'react-router-dom'
import {
  DashboardOutlined,
  StockOutlined,
  BankOutlined,
  BarChartOutlined,
  SettingOutlined,
  UserOutlined,
  LogoutOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  ApiOutlined,
} from '@ant-design/icons'
import type { MenuProps } from 'antd'

const { Header, Sider, Content } = Layout
const { Text } = Typography

type MenuItem = Required<MenuProps>['items'][number]

const MainLayout: React.FC = () => {
  const [collapsed, setCollapsed] = useState(false)
  const navigate = useNavigate()
  const location = useLocation()
  const { token } = theme.useToken()

  // 菜单项配置
  const menuItems: MenuItem[] = [
    {
      key: '/dashboard',
      icon: <DashboardOutlined />,
      label: '仪表盘',
    },
    {
      key: '/stocks',
      icon: <StockOutlined />,
      label: '股票信息',
      children: [
        {
          key: '/stocks',
          label: '股票列表',
        },
        {
          key: '/stocks/alphavantage',
          icon: <ApiOutlined />,
          label: 'Alpha Vantage 数据',
        },
      ],
    },
    {
      key: '/companies',
      icon: <BankOutlined />,
      label: '公司信息',
    },
    {
      key: '/analysis',
      icon: <BarChartOutlined />,
      label: '数据分析',
    },
    {
      key: '/settings',
      icon: <SettingOutlined />,
      label: '系统设置',
    },
  ]

  // 用户下拉菜单
  const userMenuItems: MenuProps['items'] = [
    {
      key: 'profile',
      icon: <UserOutlined />,
      label: '个人资料',
    },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: '退出登录',
      danger: true,
    },
  ]

  const handleMenuClick = ({ key }: { key: string }) => {
    navigate(key)
  }

  const handleUserMenuClick = ({ key }: { key: string }) => {
    switch (key) {
      case 'profile':
        // TODO: 实现个人资料页面
        break
      case 'logout':
        handleLogout()
        break
    }
  }

  const handleLogout = () => {
    // 清除本地存储的认证信息
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    
    // 重定向到登录页面
    navigate('/login')
  }

  // 获取当前选中的菜单项
  const getSelectedKey = () => {
    const path = location.pathname
    if (path === '/stocks/alphavantage') return '/stocks/alphavantage'
    if (path.startsWith('/stocks')) return '/stocks'
    return path
  }

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider 
        trigger={null} 
        collapsible 
        collapsed={collapsed}
        theme="dark"
        width={240}
        style={{
          overflow: 'auto',
          height: '100vh',
          position: 'fixed',
          left: 0,
          top: 0,
          bottom: 0,
        }}
      >
        <div style={{ 
          height: 64, 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'center',
          borderBottom: '1px solid #303030',
        }}>
          <Text 
            style={{ 
              color: '#fff', 
              fontSize: 18, 
              fontWeight: 'bold',
              display: collapsed ? 'none' : 'block'
            }}
          >
            Pixiu One
          </Text>
          <Text 
            style={{ 
              color: '#fff', 
              fontSize: 20, 
              fontWeight: 'bold',
              display: collapsed ? 'block' : 'none'
            }}
          >
            P
          </Text>
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[getSelectedKey()]}
          items={menuItems}
          onClick={handleMenuClick}
          style={{ borderRight: 0 }}
        />
      </Sider>
      
      <Layout style={{ marginLeft: collapsed ? 80 : 240, transition: 'margin-left 0.2s' }}>
        <Header 
          style={{ 
            padding: '0 24px', 
            background: token.colorBgContainer,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            borderBottom: `1px solid ${token.colorBorder}`,
            position: 'sticky',
            top: 0,
            zIndex: 1,
          }}
        >
          <Space>
            <div
              style={{ 
                fontSize: 18, 
                cursor: 'pointer',
                padding: '0 8px',
                borderRadius: 4,
                transition: 'background-color 0.2s',
              }}
              onClick={() => setCollapsed(!collapsed)}
              onMouseEnter={(e) => {
                e.currentTarget.style.backgroundColor = token.colorBgTextHover
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.backgroundColor = 'transparent'
              }}
            >
              {collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
            </div>
          </Space>
          
          <Dropdown 
            menu={{ 
              items: userMenuItems, 
              onClick: handleUserMenuClick 
            }} 
            placement="bottomRight"
          >
            <Space style={{ cursor: 'pointer' }}>
              <Avatar icon={<UserOutlined />} />
              <Text>用户</Text>
            </Space>
          </Dropdown>
        </Header>
        
        <Content
          style={{
            margin: 24,
            padding: 24,
            minHeight: 'calc(100vh - 112px)',
            background: token.colorBgContainer,
            borderRadius: token.borderRadius,
          }}
        >
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  )
}

export default MainLayout