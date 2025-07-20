# 股票信息采集系统 - 后端服务

基于FastAPI构建的高性能后端API服务。

## 环境配置

### 使用Conda创建环境

```bash
# 创建并激活环境
conda env create -f environment.yml
conda activate quantinfo

# 或者手动创建
conda create -n quantinfo python=3.11
conda activate quantinfo
pip install -r requirements.txt
```

### 环境变量配置

1. 复制环境变量模板
```bash
cp .env.example .env
```

2. 编辑.env文件，配置数据库连接等信息

## 开发运行

```bash
# 开发模式运行
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 或使用make命令
make run
```

## 数据库迁移

```bash
# 初始化数据库
alembic init alembic

# 创建迁移
alembic revision --autogenerate -m "Initial migration"

# 执行迁移
alembic upgrade head
```

## API文档

启动服务后访问：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 测试

```bash
# 运行所有测试
pytest

# 运行并显示覆盖率
pytest --cov=app tests/
```

## 项目结构

```
backend/
├── app/
│   ├── api/          # API路由
│   ├── core/         # 核心配置
│   ├── db/           # 数据库相关
│   ├── models/       # 数据模型
│   ├── schemas/      # Pydantic模型
│   ├── services/     # 业务逻辑
│   └── utils/        # 工具函数
├── tests/            # 测试文件
├── alembic/          # 数据库迁移
├── main.py           # 应用入口
└── environment.yml   # Conda环境配置
```