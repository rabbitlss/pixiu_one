import React, { useState, useEffect } from 'react'
import { 
  Typography, 
  Table, 
  Card, 
  Input, 
  Space, 
  Button, 
  Tag, 
  message,
  Tooltip
} from 'antd'
import { SearchOutlined, ReloadOutlined, EyeOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { stockApi } from '@/services/api'
import type { Stock } from '@/types/api'
import type { ColumnsType } from 'antd/es/table'

const { Title } = Typography
const { Search } = Input

const StockList: React.FC = () => {
  const [stocks, setStocks] = useState<Stock[]>([])
  const [loading, setLoading] = useState(false)
  const [searchText, setSearchText] = useState('')
  const navigate = useNavigate()

  const fetchStocks = async (search?: string) => {
    setLoading(true)
    try {
      const response = await stockApi.getStockList({
        search,
        limit: 100
      })
      
      if (response.data) {
        setStocks(response.data.items)
      }
    } catch (error: any) {
      message.error(error.message || '获取股票列表失败')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchStocks()
  }, [])

  const handleSearch = (value: string) => {
    setSearchText(value)
    fetchStocks(value)
  }

  const handleRefresh = () => {
    fetchStocks(searchText)
  }

  const handleViewDetail = (stock: Stock) => {
    navigate(`/stocks/${stock.id}`)
  }

  const getSectorColor = (sector: string) => {
    const colors: Record<string, string> = {
      'Technology': 'blue',
      'Consumer Cyclical': 'green',
      'Healthcare': 'red',
      'Financial Services': 'orange',
      'Communication Services': 'purple',
      'Consumer Defensive': 'cyan',
      'Industrials': 'magenta',
      'Energy': 'volcano',
      'Utilities': 'geekblue',
      'Real Estate': 'gold',
      'Basic Materials': 'lime'
    }
    return colors[sector] || 'default'
  }

  const columns: ColumnsType<Stock> = [
    {
      title: '股票代码',
      dataIndex: 'symbol',
      key: 'symbol',
      width: 120,
      render: (symbol: string) => (
        <span style={{ fontWeight: 'bold', color: '#1890ff' }}>
          {symbol}
        </span>
      ),
    },
    {
      title: '公司名称',
      dataIndex: 'name',
      key: 'name',
      ellipsis: {
        showTitle: false,
      },
      render: (name: string) => (
        <Tooltip placement="topLeft" title={name}>
          {name}
        </Tooltip>
      ),
    },
    {
      title: '交易所',
      dataIndex: 'exchange',
      key: 'exchange',
      width: 100,
      render: (exchange: string) => (
        <Tag color="processing">{exchange}</Tag>
      ),
    },
    {
      title: '行业板块',
      dataIndex: 'sector',
      key: 'sector',
      width: 120,
      render: (sector: string) => (
        <Tag color={getSectorColor(sector)}>{sector}</Tag>
      ),
    },
    {
      title: '具体行业',
      dataIndex: 'industry',
      key: 'industry',
      ellipsis: {
        showTitle: false,
      },
      render: (industry: string) => (
        <Tooltip placement="topLeft" title={industry}>
          {industry}
        </Tooltip>
      ),
    },
    {
      title: '状态',
      dataIndex: 'is_active',
      key: 'is_active',
      width: 80,
      render: (isActive: boolean) => (
        <Tag color={isActive ? 'success' : 'error'}>
          {isActive ? '活跃' : '停牌'}
        </Tag>
      ),
    },
    {
      title: '操作',
      key: 'actions',
      width: 120,
      render: (_, record: Stock) => (
        <Space>
          <Button
            type="primary"
            size="small"
            icon={<EyeOutlined />}
            onClick={() => handleViewDetail(record)}
          >
            详情
          </Button>
        </Space>
      ),
    },
  ]

  return (
    <div>
      <div style={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center',
        marginBottom: 24 
      }}>
        <Title level={2} style={{ margin: 0 }}>股票列表</Title>
        <Space>
          <Search
            placeholder="搜索股票代码或公司名称"
            allowClear
            style={{ width: 300 }}
            onSearch={handleSearch}
            enterButton={<SearchOutlined />}
          />
          <Button 
            icon={<ReloadOutlined />} 
            onClick={handleRefresh}
            loading={loading}
          >
            刷新
          </Button>
        </Space>
      </div>

      <Card>
        <Table
          columns={columns}
          dataSource={stocks}
          rowKey="id"
          loading={loading}
          pagination={{
            total: stocks.length,
            pageSize: 20,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) => 
              `第 ${range[0]}-${range[1]} 条/共 ${total} 条`,
          }}
          scroll={{ x: 1000 }}
        />
      </Card>
    </div>
  )
}

export default StockList