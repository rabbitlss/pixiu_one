import React, { lazy, Suspense } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { Spin } from 'antd'
import MainLayout from '@/layouts/MainLayout'
import AuthGuard from '@/components/AuthGuard'

// 路由懒加载
const Login = lazy(() => import('@/pages/Login'))
const Dashboard = lazy(() => import('@/pages/Dashboard'))
const StockList = lazy(() => import('@/pages/Stock/List'))
const StockDetail = lazy(() => import('@/pages/Stock/Detail'))
const AlphaVantageData = lazy(() => import('@/pages/Stock/AlphaVantageData'))
const StockDashboard = lazy(() => import('@/pages/StockDashboard'))
const CompanyInfo = lazy(() => import('@/pages/Company'))
const Analysis = lazy(() => import('@/pages/Analysis'))
const Settings = lazy(() => import('@/pages/Settings'))
const NotFound = lazy(() => import('@/pages/NotFound'))

// 加载中组件
const PageLoading = () => (
  <div style={{ 
    display: 'flex', 
    justifyContent: 'center', 
    alignItems: 'center', 
    height: '100vh' 
  }}>
    <Spin size="large" tip="加载中..." />
  </div>
)

const Router: React.FC = () => {
  return (
    <Suspense fallback={<PageLoading />}>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/" element={<AuthGuard><MainLayout /></AuthGuard>}>
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="stocks">
            <Route index element={<StockList />} />
            <Route path="alphavantage" element={<AlphaVantageData />} />
            <Route path="dashboard" element={<StockDashboard />} />
            <Route path=":code" element={<StockDetail />} />
          </Route>
          <Route path="companies" element={<CompanyInfo />} />
          <Route path="analysis" element={<Analysis />} />
          <Route path="settings" element={<Settings />} />
        </Route>
        <Route path="*" element={<NotFound />} />
      </Routes>
    </Suspense>
  )
}

export default Router