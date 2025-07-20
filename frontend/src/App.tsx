import React from 'react'
import { ConfigProvider, App as AntdApp } from 'antd'
import zhCN from 'antd/locale/zh_CN'
import dayjs from 'dayjs'
import 'dayjs/locale/zh-cn'
import { BrowserRouter } from 'react-router-dom'
import Router from './router'
import { theme } from './config/theme'

dayjs.locale('zh-cn')

function App() {
  return (
    <ConfigProvider locale={zhCN} theme={theme}>
      <AntdApp>
        <BrowserRouter>
          <Router />
        </BrowserRouter>
      </AntdApp>
    </ConfigProvider>
  )
}

export default App