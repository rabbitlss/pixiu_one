# Pixiu One - 股票信息采集与分析平台

一个基于现代技术栈构建的全栈股票信息采集与分析系统，提供实时数据监控、技术分析和智能投资建议。

## 🚀 系统架构

```
pixiu_one/
├── frontend/          # React + TypeScript + Ant Design 前端应用
├── backend/           # FastAPI + SQLAlchemy 后端服务
├── api-specs/         # API 接口规范文档
├── docker-compose.yml # Docker 编排配置
└── docs/              # 项目文档
```

## ✨ 核心功能

### 📊 数据采集与管理
- 实时股票价格监控
- 历史数据自动收集
- 多数据源支持（Yahoo Finance、Alpha Vantage等）
- 数据质量监控和验证

### 📈 技术分析
- 技术指标计算（MA、RSI、MACD等）
- K线图表展示
- 趋势分析和预测
- 自定义指标支持

### 🎯 智能投资
- 个性化股票监控列表
- 交易信号提醒
- 投资建议生成
- 风险评估分析

### 👤 用户管理
- JWT 安全认证
- 用户权限管理
- 个人偏好设置
- 数据导出功能

## 🛠️ 技术栈

### 前端技术
- **React 18** - 现代化UI框架
- **TypeScript** - 类型安全
- **Vite** - 快速构建工具
- **Ant Design 5** - 企业级UI组件库
- **ECharts** - 专业图表库
- **Axios** - HTTP客户端
- **WebSocket** - 实时数据推送

### 后端技术
- **FastAPI** - 高性能异步框架
- **SQLAlchemy** - ORM数据库操作
- **PostgreSQL/SQLite** - 数据存储
- **Redis** - 缓存和消息队列
- **Celery** - 异步任务处理
- **JWT** - 身份认证
- **yfinance** - 股票数据API

## 🚀 快速开始

### 环境要求
- Node.js >= 16
- Python >= 3.9
- PostgreSQL >= 12 (可选)
- Redis >= 6 (可选)

### 1. 克隆项目
```bash
git clone https://github.com/rabbitlss/pixiu_one.git
cd pixiu_one
```

### 2. 启动后端服务
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
uvicorn main:app --reload
```

后端服务将在 http://localhost:8000 启动

### 3. 启动前端应用
```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

前端应用将在 http://localhost:3000 启动

### 4. 使用 Docker Compose（推荐）
```bash
docker-compose up -d
```

## 📚 API 文档

启动后端服务后，可以访问：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 🔐 默认账户

### 管理员账户
- 邮箱: `admin@quantinfo.com`
- 用户名: `admin`
- 密码: `admin123!@#`

### 演示账户
- 邮箱: `demo@example.com`
- 用户名: `demo`
- 密码: `Demo123456@`

## 📸 系统截图

### 登录页面
- 美观的登录/注册界面
- 表单验证和错误提示
- 记住登录状态

### 股票列表
- 实时数据展示
- 高级搜索和过滤
- 行业分类标签
- 快速操作按钮

### 股票详情
- K线图表展示
- 技术指标分析
- 历史数据查询
- 实时价格更新

### 数据分析
- 市场概览仪表盘
- 行业板块分析
- 趋势预测图表
- 数据导出功能

## 🔄 开发路线图

### 已完成 ✅
- [x] 基础架构搭建
- [x] 用户认证系统
- [x] 股票数据采集
- [x] 前后端联调
- [x] 实时数据展示

### 进行中 🚧
- [ ] ECharts图表集成
- [ ] 股票详情页面
- [ ] 技术指标计算
- [ ] WebSocket实时推送

### 计划中 📋
- [ ] 交易策略回测
- [ ] AI投资建议
- [ ] 移动端适配
- [ ] 多语言支持
- [ ] 社交功能

## 🤝 贡献指南

1. Fork 本仓库
2. 创建你的功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交你的更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启一个 Pull Request

## 📄 开源协议

本项目基于 [MIT License](LICENSE) 开源协议。

## 👨‍💻 作者

- **rabbitlss** - [GitHub](https://github.com/rabbitlss)

## 🙏 致谢

- 感谢所有开源项目的贡献者
- 特别感谢 FastAPI 和 React 社区
- 数据来源：Yahoo Finance、Alpha Vantage

---

**注意**: 本系统仅供学习和研究使用，不构成任何投资建议。股市有风险，投资需谨慎。