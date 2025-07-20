# 股票信息采集系统 Backend

生产级别的股票数据采集和管理系统后端，基于 FastAPI 构建。

## ✨ 核心功能

### 🔐 用户管理
- JWT 认证授权
- 用户注册/登录
- 权限管理（普通用户/超级用户）
- 密码安全策略

### 📈 股票数据管理
- 股票基本信息管理
- 历史价格数据采集
- 实时行情获取
- 技术指标计算（MA、RSI等）
- 数据质量监控

### 👁️ 监控列表
- 个人股票监控列表
- 公开/私有列表管理
- 股票添加/移除
- 备注和标签

### ⚙️ 系统管理
- 自动数据更新调度
- 后台任务处理
- 系统状态监控
- 数据质量报告

## 🛠️ 技术栈

- **FastAPI** - 现代异步Web框架
- **SQLAlchemy** - 异步ORM
- **SQLite/PostgreSQL** - 数据库
- **Pydantic** - 数据验证
- **JWT** - 身份认证
- **yfinance** - 股票数据源
- **AsyncIO** - 异步处理

## 🚀 快速开始

### 1. 环境准备

```bash
# 克隆项目
cd backend

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置环境

```bash
# 复制环境配置文件
cp .env.example .env

# 编辑配置文件（可选）
vim .env
```

### 3. 启动应用

```bash
# 使用启动脚本（推荐）
./scripts/start.sh

# 或直接启动
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 4. 访问API文档

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- 健康检查: http://localhost:8000/health

## 📚 API文档

### 认证端点
- `POST /api/v1/auth/register` - 用户注册
- `POST /api/v1/auth/login` - 用户登录
- `POST /api/v1/auth/change-password` - 修改密码

### 股票管理
- `GET /api/v1/stocks` - 获取股票列表
- `POST /api/v1/stocks` - 添加股票（管理员）
- `GET /api/v1/stocks/{id}` - 获取股票详情
- `GET /api/v1/stocks/{id}/prices` - 获取价格历史

### 监控列表
- `GET /api/v1/watchlists` - 获取监控列表
- `POST /api/v1/watchlists` - 创建监控列表
- `POST /api/v1/watchlists/{id}/stocks` - 添加股票到监控列表

### 系统管理（仅管理员）
- `GET /api/v1/admin/system-status` - 系统状态
- `POST /api/v1/admin/update-stock-data` - 手动更新数据
- `GET /api/v1/admin/data-quality-report` - 数据质量报告

## 🔧 开发工具

```bash
# 数据库管理
python scripts/dev_tools.py init-db      # 初始化数据库
python scripts/dev_tools.py reset-db     # 重置数据库
python scripts/dev_tools.py stats        # 数据库统计

# 用户管理
python scripts/dev_tools.py create-demo-user  # 创建演示用户

# 数据管理
python scripts/dev_tools.py update-data       # 更新示例数据
python scripts/dev_tools.py test-provider     # 测试数据提供者
```

## 🏗️ 项目结构

```
backend/
├── app/
│   ├── api/v1/endpoints/     # API端点
│   ├── core/                 # 核心配置
│   ├── db/                   # 数据库配置
│   ├── models/               # 数据模型
│   ├── schemas/              # Pydantic模式
│   └── services/             # 业务逻辑
├── scripts/                  # 工具脚本
├── tests/                    # 测试文件
├── main.py                   # 应用入口
└── requirements.txt          # 依赖列表
```

## 🔐 默认账户

系统会自动创建以下默认账户：

**管理员账户**
- 邮箱: `admin@quantinfo.com`
- 用户名: `admin`
- 密码: `admin123!@#`

**演示账户**（通过dev_tools创建）
- 邮箱: `demo@example.com`
- 用户名: `demo`
- 密码: `demo123!`

## 📊 数据采集

### 支持的数据源
- **Yahoo Finance** (默认) - 免费，覆盖全球主要市场
- 可扩展到其他数据源（Alpha Vantage、IEX Cloud等）

### 采集频率
- **历史数据**: 每日凌晨2点自动更新
- **实时数据**: 交易时间内每5分钟更新
- **技术指标**: 每日下午6点计算

### 数据质量
- 自动数据验证
- 异常数据检测
- 数据完整性检查
- 质量报告生成

## 🔄 部署配置

### 环境变量

```bash
# 数据库
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/dbname

# 安全
SECRET_KEY=your-super-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS
CORS_ORIGINS=["http://localhost:3000"]
```

### Docker部署

```bash
# 构建镜像
docker build -t stock-backend .

# 运行容器
docker run -p 8000:8000 stock-backend
```

## 🧪 测试

```bash
# 运行所有测试
pytest

# 运行特定测试
pytest tests/test_auth.py

# 生成覆盖率报告
pytest --cov=app tests/
```

## 📈 性能优化

- **异步处理**: 全异步架构，支持高并发
- **数据库优化**: 合理索引，查询优化
- **缓存策略**: Redis缓存热点数据
- **后台任务**: Celery处理耗时操作

## 🛡️ 安全特性

- **密码安全**: bcrypt哈希，复杂度要求
- **JWT认证**: 安全的无状态认证
- **输入验证**: Pydantic严格验证
- **SQL注入防护**: ORM参数化查询
- **CORS配置**: 跨域访问控制

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情