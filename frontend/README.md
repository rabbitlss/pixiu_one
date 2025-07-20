# Pixiu One Frontend

基于 React + Vite + TypeScript + Ant Design 构建的股票信息采集系统前端应用。

## 功能特性

- 📊 股票信息展示和分析
- 📈 实时价格更新（WebSocket）
- 🏢 公司信息管理
- 📱 响应式设计
- 🎨 美观的用户界面
- 🔄 自动重连和错误处理
- 🚀 生产级代码质量

## 技术栈

- **框架**: React 18 + Vite
- **语言**: TypeScript
- **UI库**: Ant Design 5
- **路由**: React Router 6
- **状态管理**: Zustand
- **HTTP客户端**: Axios
- **图表**: ECharts
- **样式**: Sass
- **构建工具**: Vite

## 环境要求

- Node.js >= 16
- npm >= 8 或 yarn >= 1.22

## 安装依赖

```bash
# 使用 npm
npm install

# 或使用 yarn
yarn install

# 或使用 pnpm
pnpm install
```

## 环境配置

1. 复制环境变量模板：
```bash
cp .env.example .env
```

2. 编辑 `.env` 文件，配置后端API地址等信息：
```env
# API 基础地址
VITE_API_BASE_URL=http://localhost:8000

# WebSocket 地址
VITE_WS_URL=ws://localhost:8000/ws

# 应用标题
VITE_APP_TITLE=Pixiu One
```

## 开发运行

```bash
# 启动开发服务器
npm run dev

# 或
yarn dev
```

访问 http://localhost:3000

## 构建

```bash
# 构建生产版本
npm run build

# 预览构建结果
npm run preview
```

## 代码检查

```bash
# ESLint 检查
npm run lint

# TypeScript 类型检查
npm run type-check
```

## 项目结构

```
frontend/
├── public/                 # 静态资源
├── src/
│   ├── components/         # 公共组件
│   ├── pages/             # 页面组件
│   ├── layouts/           # 布局组件
│   ├── services/          # API 服务
│   ├── utils/             # 工具函数
│   ├── types/             # TypeScript 类型定义
│   ├── hooks/             # 自定义 Hooks
│   ├── store/             # 状态管理
│   ├── config/            # 配置文件
│   ├── router/            # 路由配置
│   ├── App.tsx            # 根组件
│   └── main.tsx           # 入口文件
├── package.json
├── vite.config.ts         # Vite 配置
├── tsconfig.json          # TypeScript 配置
└── README.md
```

## 主要功能模块

### 1. 股票信息模块
- 股票列表展示
- 股票详情页面
- 实时价格更新
- 技术指标分析

### 2. 公司信息模块
- 公司基本信息
- 财务数据展示
- 行业分析

### 3. 数据分析模块
- 技术分析图表
- 市场概览
- 交易建议

### 4. 用户设置模块
- 个人偏好设置
- 关注列表管理
- 系统配置

## API 集成

前端通过以下方式与后端API集成：

1. **HTTP请求**: 使用 Axios 进行RESTful API调用
2. **WebSocket**: 实时数据更新和推送
3. **错误处理**: 统一的错误处理和用户提示
4. **请求拦截**: 自动添加认证token和请求追踪

## 开发指南

### 添加新页面

1. 在 `src/pages/` 目录下创建页面组件
2. 在 `src/router/index.tsx` 中添加路由配置
3. 在主菜单中添加导航链接

### 添加新API

1. 在 `src/types/api.ts` 中定义数据类型
2. 在 `src/services/api.ts` 中添加API函数
3. 在组件中使用API函数

### 状态管理

使用 Zustand 进行状态管理，store文件放在 `src/store/` 目录下。

### 样式开发

- 使用 Ant Design 组件默认样式
- 自定义样式使用 Sass/SCSS
- 响应式设计遵循 Ant Design 的栅格系统

## 生产部署

### Docker 部署

```bash
# 构建 Docker 镜像
docker build -t pixiu-frontend .

# 运行容器
docker run -p 3000:80 pixiu-frontend
```

### 静态文件部署

构建后将 `dist/` 目录内容部署到静态文件服务器（如 Nginx）。

## 注意事项

1. 确保后端API服务已启动并可访问
2. WebSocket连接需要后端支持
3. 开发环境需要配置代理解决跨域问题
4. 生产环境需要配置正确的API地址

## 支持的浏览器

- Chrome >= 88
- Firefox >= 85
- Safari >= 14
- Edge >= 88